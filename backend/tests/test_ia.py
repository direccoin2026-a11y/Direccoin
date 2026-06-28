#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - TEST DE IA                                   ║
║                    Versión: 1.0.0 | Archivo: tests/test_ia.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

PRUEBAS UNITARIAS DEL SISTEMA DE INTELIGENCIA ARTIFICIAL.

Verifica:
  • Controlador de gas dinámico
  • Acelerador de red
  • Guardián de seguridad
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ia.ajuste_gas import ControladorGas, ConfigAjusteGas
from ia.acelerador import AceleradorRed, ConfigAcelerador
from ia.guardian import GuardianSeguridad, ConfigGuardian

class TestIA:
    
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
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🧪 TEST DE IA (Sistema Nervioso)")
        print("=" * 70)
        
        self._test_ajuste_gas()
        self._test_acelerador()
        self._test_guardian()
        
        total = self.pasados + self.fallidos
        print("─" * 70)
        print(f"📊 {self.pasados}/{total} PASADOS | {self.fallidos} FALLIDOS")
        print("─" * 70)
        if self.fallidos == 0:
            print("✅ TODAS LAS PRUEBAS DE IA PASARON\n")
        else:
            print(f"❌ {self.fallidos} PRUEBAS FALLARON\n")
            for e in self.errores:
                print(f"   • {e}")
        return self.fallidos == 0
    
    def _test_ajuste_gas(self):
        print("\n   📋 IA: Ajuste de Gas:\n")
        
        cg = ControladorGas()
        
        # Gas en diferentes niveles
        r = cg.calcular_gas(10, 100, 5)
        self.assert_true("Gas bajo (10% uso)", r["nivel_congestion"] == "bajo")
        
        r = cg.calcular_gas(50, 100, 40)
        self.assert_true("Gas medio (50% uso)", r["nivel_congestion"] == "medio")
        
        r = cg.calcular_gas(90, 100, 200)
        self.assert_true("Gas crítico (90% uso)", r["nivel_congestion"] in ["alto", "critico"])
        
        # Spam
        spam = cg.detectar_spam(600)
        self.assert_true("Detectar spam (600 tx/s)", spam["spam_detectado"])
        
        spam2 = cg.detectar_spam(10)
        self.assert_true("No spam (10 tx/s)", not spam2["spam_detectado"])
        
        # Descuento usuario frecuente
        for _ in range(15):
            cg.registrar_transaccion_usuario("drcFrecuente")
        gas_desc = cg.calcular_gas_para_usuario("drcFrecuente", 1000)
        gas_normal = cg.calcular_gas_para_usuario("drcNuevo", 1000)
        self.assert_true("Descuento 50% frecuente", gas_desc < gas_normal)
        
        # Estadísticas
        stats = cg.obtener_estadisticas()
        self.assert_true("Estadísticas gas", "gas_actual" in stats)
    
    def _test_acelerador(self):
        print("\n   📋 IA: Acelerador de Red:\n")
        
        acel = AceleradorRed()
        
        # Registrar nodos
        for i in range(20):
            acel.registrar_nodo(f"nodo_{i}", random.randint(5, 300))
        self.assert_true("20 nodos registrados", len(acel.nodos) == 20)
        
        # Conexiones
        for i in range(19):
            acel.registrar_conexion(f"nodo_{i}", f"nodo_{i+1}", random.randint(10, 100))
        self.assert_true("Conexiones creadas", len(acel.conexiones) > 0)
        
        # Superpares
        sp = acel.seleccionar_superpares(5)
        self.assert_true("5 superpares", len(sp) == 5)
        
        # Ruta
        ruta = acel.encontrar_mejor_ruta("nodo_0", "nodo_10")
        self.assert_true("Ruta encontrada", len(ruta) > 0 and len(ruta[0]["ruta"]) > 1)
        
        # Balanceo
        distr = acel.balancear_carga(1000, ["nodo_0", "nodo_1", "nodo_2"])
        self.assert_true("Balanceo correcto", sum(distr.values()) == 1000)
    
    def _test_guardian(self):
        print("\n   📋 IA: Guardián de Seguridad:\n")
        
        guard = GuardianSeguridad()
        
        # Transacción normal
        tx_ok = {"origen": "drcBueno", "destino": "drcTienda", "cantidad": 1000,
                 "gas": 50, "txid": "tx_test_001", "timestamp": time.time()}
        r = guard.analizar_transaccion(tx_ok)
        self.assert_true("Tx normal aceptada", r["permitir"])
        
        # Doble gasto
        tx_doble = {"origen": "drcBueno", "destino": "drcTienda", "cantidad": 500,
                    "gas": 50, "txid": "tx_test_001", "timestamp": time.time()}
        r = guard.analizar_transaccion(tx_doble)
        self.assert_true("Doble gasto rechazado", r["bloquear"])
        
        # Lista negra
        guard._bloquear("drcHacker", "Ataque detectado")
        tx_hacker = {"origen": "drcHacker", "destino": "drcVictima", "cantidad": 100,
                     "gas": 10, "txid": "tx_hack_001", "timestamp": time.time()}
        r = guard.analizar_transaccion(tx_hacker)
        self.assert_true("Hacker bloqueado", r["bloquear"])
        
        # Rate limiting
        for i in range(ConfigGuardian.MAX_TX_POR_DIRECCION_POR_SEGUNDO + 1):
            tx_spam = {"origen": "drcSpammer", "destino": f"drcVictim{i}",
                      "cantidad": 1, "gas": 1, "txid": f"tx_spam_{i}", "timestamp": time.time()}
            r = guard.analizar_transaccion(tx_spam)
        self.assert_true("Rate limit activado", r["bloquear"])
        
        # Reputación
        guard.penalizar("drcMalo", "Intento de ataque", 150)
        rep = guard.reputaciones.get("drcMalo")
        self.assert_true("Penalización aplicada", rep is not None and rep.score < 0)
        
        guard._recompensar("drcBueno")
        rep_b = guard.reputaciones.get("drcBueno")
        self.assert_true("Recompensa aplicada", rep_b is not None and rep_b.score > 100)
        
        # Estadísticas
        stats = guard.obtener_estadisticas()
        self.assert_true("Estadísticas guardián", "bloqueados_actuales" in stats)


if __name__ == "__main__":
    test = TestIA()
    test.ejecutar()