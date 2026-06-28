#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - TEST DE BILLETERA                            ║
║                    Versión: 1.0.1 | Archivo: tests/test_billetera.py       ║
╚══════════════════════════════════════════════════════════════════════════════╝

PRUEBAS UNITARIAS DEL SISTEMA DE BILLETERA.
"""

import sys
import os
import time
import json
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from billetera.keystore import Keystore, FraseSemilla, CryptoUtil, CifradoSimetrico
from billetera.historial import GestorHistorial, RegistroTransaccion

class TestBilletera:
    
    def __init__(self):
        self.pasados = 0
        self.fallidos = 0
        self.errores = []
    
    def assert_true(self, nombre: str, condicion: bool, mensaje: str = ""):
        if condicion:
            self.pasados += 1
            print(f"   ✅ {nombre}")
        else:
            self.fallidos += 1
            self.errores.append(nombre)
            print(f"   ❌ {nombre}: {mensaje}")
    
    def assert_equals(self, nombre: str, valor, esperado):
        if valor == esperado:
            self.pasados += 1
            print(f"   ✅ {nombre}")
        else:
            self.fallidos += 1
            msg = f"{nombre}: {valor} != {esperado}"
            self.errores.append(msg)
            print(f"   ❌ {msg}")
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🧪 TEST DE BILLETERA")
        print("=" * 70)
        
        self._test_keystore()
        self._test_frases()
        self._test_historial()
        
        total = self.pasados + self.fallidos
        print("─" * 70)
        print(f"📊 {self.pasados}/{total} PASADOS | {self.fallidos} FALLIDOS")
        print("─" * 70)
        if self.fallidos == 0:
            print("✅ TODAS LAS PRUEBAS DE BILLETERA PASARON\n")
        else:
            print(f"❌ {self.fallidos} PRUEBAS FALLARON\n")
            for e in self.errores:
                print(f"   • {e}")
        return self.fallidos == 0
    
    def _test_keystore(self):
        print("\n   📋 Keystore (Cifrado):\n")
        
        clave_original = os.urandom(32)
        ks = Keystore()
        archivo = ks.guardar(clave_original, "password123", "test_wallet")
        self.assert_true("Keystore guardado", os.path.exists(archivo))
        
        clave_recuperada = ks.cargar(archivo, "password123")
        self.assert_true("Clave recuperada", clave_recuperada is not None)
        
        if clave_recuperada:
            self.assert_true("Clave correcta", clave_recuperada == clave_original)
        
        clave_mala = ks.cargar(archivo, "mala")
        self.assert_true("Contraseña incorrecta rechazada", clave_mala is None)
        
        nonce, cifrado = CifradoSimetrico.cifrar(b"k" * 32, b"mensaje secreto")
        plano = CifradoSimetrico.descifrar(b"k" * 32, nonce, cifrado)
        self.assert_true("Cifrar/descifrar", plano == b"mensaje secreto")
        
        derivada = CryptoUtil.pbkdf2("test", b"sal", 1000)
        self.assert_true("PBKDF2 32 bytes", len(derivada) == 32)
        
        if os.path.exists(archivo):
            os.remove(archivo)
    
    def _test_frases(self):
        print("\n   📋 Frases Semilla:\n")
        
        frase = FraseSemilla.generar(128)
        palabras = frase.split()
        self.assert_equals("12 palabras", len(palabras), 12)
        
        self.assert_true("Frase válida", FraseSemilla.es_valida(frase))
        self.assert_true("Frase inválida rechazada", not FraseSemilla.es_valida("perro " * 12))
        
        entropia = FraseSemilla.a_entropia(frase)
        self.assert_true("Frase → entropía", entropia is not None and len(entropia) == 16)
        
        frase24 = FraseSemilla.generar(256)
        self.assert_equals("24 palabras", len(frase24.split()), 24)
    
    def _test_historial(self):
        print("\n   📋 Historial de Transacciones:\n")
        
        hist = GestorHistorial("drcTestPropia", persistente=False)
        
        hist.agregar("tx001", "drcTestPropia", "drcB", 1000, tipo="envio", estado="confirmado")
        self.assert_equals("1 transacción", hist.total(), 1)
        
        hist.agregar("tx002", "drcA", "drcTestPropia", 500, tipo="recepcion", estado="confirmado")
        hist.agregar("tx003", "drcTestPropia", "drcC", 200, tipo="envio", estado="pendiente")
        hist.agregar("tx004", "drcD", "drcTestPropia", 1500, tipo="recepcion", estado="confirmado")
        self.assert_equals("4 transacciones", hist.total(), 4)
        
        r = hist.buscar(direccion="drcTestPropia")
        self.assert_equals("Buscar 4 resultados", r["total"], 4)
        
        r = hist.buscar(tipo="envio")
        self.assert_equals("Buscar envíos", r["total"], 2)
        
        r = hist.buscar(estado="confirmado")
        self.assert_equals("Buscar confirmados", r["total"], 3)
        
        tx = hist.buscar_por_txid("tx001")
        self.assert_true("Buscar TXID", tx is not None and tx["cantidad"] == 1000)
        
        bal = hist.obtener_balance_historico()
        self.assert_equals("Total enviado", bal["total_enviado"], 1200)
        self.assert_equals("Total recibido", bal["total_recibido"], 2000)
        
        stats = hist.obtener_estadisticas()
        self.assert_true("Estadísticas", stats["total_transacciones"] == 4)
        
        csv_str = hist.exportar_csv_string()
        self.assert_true("Exportar CSV", "txid" in csv_str and "drcTestPropia" in csv_str)


if __name__ == "__main__":
    test = TestBilletera()
    test.ejecutar()