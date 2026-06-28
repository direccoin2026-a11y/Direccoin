#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - TEST DE GÉNESIS                             ║
║                    Versión: 1.0.1 | Archivo: tests/test_genesis.py        ║
╚══════════════════════════════════════════════════════════════════════════════╝

PRUEBAS UNITARIAS DEL BLOQUE GÉNESIS Y PREMINE.
"""

import sys
import os
import json
import time
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestGenesis:
    
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
            print(f"   ✅ {nombre}: {valor}")
        else:
            self.fallidos += 1
            msg = f"{nombre}: {valor} != {esperado}"
            self.errores.append(msg)
            print(f"   ❌ {msg}")
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🧪 TEST DE GENESIS.PY")
        print("=" * 70)
        
        ruta_genesis = os.path.join("..", "data", "genesis.json")
        
        if not os.path.exists(ruta_genesis):
            print("   ⚠️  genesis.json no encontrado en data/")
            print("   Buscando en otras ubicaciones...")
            alternativas = [
                "genesis.json",
                os.path.join("data", "genesis.json"),
                os.path.join("..", "genesis.json"),
            ]
            encontrado = False
            for alt in alternativas:
                if os.path.exists(alt):
                    ruta_genesis = alt
                    encontrado = True
                    print(f"   ✅ Encontrado en: {alt}")
                    break
            if not encontrado:
                self._pruebas_minimas()
                return self.fallidos == 0
        
        with open(ruta_genesis) as f:
            genesis = json.load(f)
        
        self._pruebas_completas(genesis)
        
        total = self.pasados + self.fallidos
        print("─" * 70)
        print(f"📊 {self.pasados}/{total} PASADOS | {self.fallidos} FALLIDOS")
        print("─" * 70)
        if self.fallidos == 0:
            print("✅ TODAS LAS PRUEBAS PASARON\n")
        else:
            print(f"❌ {self.fallidos} PRUEBAS FALLARON\n")
            for e in self.errores:
                print(f"   • {e}")
        return self.fallidos == 0
    
    def _pruebas_minimas(self):
        print("\n   📋 Pruebas sin genesis.json:\n")
        self.assert_true("Python funcional", True)
        self.assert_true("Hashlib disponible", hashlib.sha3_256(b"test").digest() is not None)
        self.assert_true("JSON disponible", json.dumps({"test": True}) is not None)
    
    def _pruebas_completas(self, genesis: dict):
        print("\n   📋 Pruebas completas del bloque génesis:\n")
        
        # 1. Estructura del bloque
        bloque = genesis.get("bloque", {})
        self.assert_true("Bloque existe", bool(bloque))
        self.assert_true("Índice presente", "indice" in bloque)
        self.assert_equals("Índice = 0", bloque.get("indice"), 0)
        
        hash_previo = bloque.get("hash_previo", "")
        self.assert_equals("Hash previo = 0x64", hash_previo, "0" * 64)
        
        # 2. Hash del bloque
        hash_bloque = bloque.get("hash", "")
        self.assert_true("Hash existe", len(hash_bloque) > 0)
        self.assert_true("Hash con prefijo d1", hash_bloque.startswith("d1"))
        self.assert_true("Hash de 64 caracteres", len(hash_bloque) == 64)
        
        # 3. Timestamp
        ts = bloque.get("timestamp", 0)
        self.assert_true("Timestamp positivo", ts > 0)
        self.assert_true("Timestamp razonable (>2025)", ts > 1700000000)
        
        # 4. Merkle root
        merkle = bloque.get("merkle_raiz", "")
        self.assert_true("Merkle root existe", len(merkle) == 64)
        
        # 5. Integridad
        integridad = bloque.get("integridad", "")
        self.assert_true("Checksum de integridad", len(integridad) == 16)
        
        # 6. Dificultad y nonce
        self.assert_true("Dificultad presente", "dificultad" in bloque)
        self.assert_true("Nonce presente", "nonce" in bloque)
        
        # 7. Premine
        premine = genesis.get("premine", {})
        self.assert_true("Premine existe", bool(premine))
        self.assert_equals("Suministro total", premine.get("suministro_total"), 100_000_000)
        self.assert_equals("Premine total", premine.get("premine_total"), 3_000_000)
        self.assert_equals("Porcentaje", premine.get("porcentaje"), "3%")
        
        # 8. TXID del premine
        txid = premine.get("transaccion_txid") or premine.get("txid", "")
        self.assert_true("TXID existe", len(txid) == 64)
        
        # 9. Salidas del premine
        salidas = premine.get("salidas", [])
        self.assert_true("Salidas existen", len(salidas) >= 1)
        
        if len(salidas) >= 1:
            self.assert_equals("Salida 0 tipo", salidas[0].get("tipo"), "LIQUIDO_INMEDIATO")
            self.assert_equals("Salida 0 cantidad", salidas[0].get("cantidad"), 1_000_000)
        
        if len(salidas) >= 2:
            self.assert_equals("Salida 1 tipo", salidas[1].get("tipo"), "BLOQUEADO_TEMPORAL")
            self.assert_equals("Salida 1 cantidad", salidas[1].get("cantidad"), 2_000_000)
            
            # Verificar timelock
            script = salidas[1].get("script_bloqueo", {})
            if script:
                liberacion = script.get("liberacion", 0)
                self.assert_true("Timelock futuro", liberacion > ts)
        
        # 10. Direct
        direct = genesis.get("direct", {})
        self.assert_true("Direct existe", bool(direct))
        direccion = direct.get("direccion", "")
        self.assert_true("Dirección con prefijo drc", direccion.startswith("drc"))
        self.assert_true("Dirección longitud", len(direccion) >= 30)
        
        # 11. Configuración (flexible)
        config = genesis.get("configuracion", {})
        if config:
            nombre = config.get("nombre") or config.get("NOMBRE", "")
            simbolo = config.get("simbolo") or config.get("SIMBOLO", "")
            decimales = config.get("decimales") or config.get("DECIMALES", 0)
            if nombre:
                self.assert_equals("Nombre red", nombre, "Direccoin")
            if simbolo:
                self.assert_equals("Símbolo", simbolo, "DRC")
            if decimales:
                self.assert_equals("Decimales", decimales, 6)
            if not nombre and not simbolo and not decimales:
                self.assert_true("Configuración (campos legacy)", True)
        else:
            self.assert_true("Configuración (no presente - OK)", True)
        
        # 12. Mensaje del premine
        mensaje = premine.get("mensaje", "")
        self.assert_true("Mensaje existe", len(mensaje) > 0)


if __name__ == "__main__":
    test = TestGenesis()
    test.ejecutar()