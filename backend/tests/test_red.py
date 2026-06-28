#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - TEST DE RED                                  ║
║                    Versión: 1.0.0 | Archivo: tests/test_red.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

PRUEBAS UNITARIAS DEL SISTEMA DE RED P2P Y CONSENSO.

Verifica:
  • Descubrimiento de pares
  • Propagación de transacciones y bloques
  • Monitor de red
  • Nodo completo
  • Consenso y forks
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from red_p2p.descubrimiento import DescubridorPares, TablaPares, Par as ParDescubrimiento
from red_p2p.propagacion import PropagadorGossip, CacheMensajes, ControlFrecuencia
from red_p2p.monitor_red import MonitorRed
from red_p2p.nodo import NodoDireccoin, ConfigNodo
from consenso.reglas import ValidadorBloques, VerificadorDobleGasto, GestorFinalidad
from consenso.fork_resolver import ForkResolver

class TestRed:
    
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
        print("🧪 TEST DE RED P2P Y CONSENSO")
        print("=" * 70)
        
        self._test_descubrimiento()
        self._test_propagacion()
        self._test_monitor()
        self._test_nodo()
        self._test_consenso()
        self._test_forks()
        
        total = self.pasados + self.fallidos
        print("─" * 70)
        print(f"📊 {self.pasados}/{total} PASADOS | {self.fallidos} FALLIDOS")
        print("─" * 70)
        if self.fallidos == 0:
            print("✅ TODAS LAS PRUEBAS DE RED PASARON\n")
        else:
            print(f"❌ {self.fallidos} PRUEBAS FALLARON\n")
            for e in self.errores:
                print(f"   • {e}")
        return self.fallidos == 0
    
    def _test_descubrimiento(self):
        print("\n   📋 Descubrimiento de Pares:\n")
        
        desc = DescubridorPares()
        self.assert_true("ID de nodo generado", len(desc.id_nodo) == 40)
        self.assert_true("Tabla de pares creada", desc.tabla is not None)
        self.assert_true("Nodos semilla", len(desc.nodos_semilla) >= 1)
        
        par_test = ParDescubrimiento(id_nodo="a" * 40, direccion="192.168.1.1:8338")
        ok = desc.tabla.agregar_par(par_test)
        self.assert_true("Agregar par", ok)
        
        ok = desc.tabla.agregar_par(par_test)
        self.assert_true("Rechazar duplicado", not ok)
        
        respondio, latencia = desc.simular_ping(par_test)
        self.assert_true("Ping responde", respondio and latencia > 0)
    
    def _test_propagacion(self):
        print("\n   📋 Propagación Gossip:\n")
        
        prop = PropagadorGossip("nodo_test")
        pares_falsos = [type('Par', (), {'id_nodo': f'p{i}', 'score': 50})() for i in range(20)]
        
        tx = {"origen": "drcA", "destino": "drcB", "cantidad": 1000, "gas": 100, "timestamp": time.time()}
        ok, msg = prop.propagar_transaccion(tx, pares_falsos)
        self.assert_true("Propagar transacción", ok)
        
        ok, msg = prop.propagar_transaccion(tx, pares_falsos)
        self.assert_true("Rechazar duplicada", not ok)
        
        bloque = {"indice": 1, "hash": "d1abc", "transacciones": [tx]}
        ok, msg = prop.propagar_bloque(bloque, pares_falsos)
        self.assert_true("Propagar bloque", ok)
        
        # Cache
        cache = CacheMensajes(100)
        cache.marcar_visto("msg_001")
        self.assert_true("Cache: ya visto", cache.ya_visto("msg_001"))
        self.assert_true("Cache: no visto", not cache.ya_visto("msg_002"))
        
        # Control frecuencia
        cf = ControlFrecuencia()
        for _ in range(50):
            cf.permitir("nodo_test", "transaccion")
        self.assert_true("Rate limit activado", not cf.permitir("nodo_test", "transaccion"))
    
    def _test_monitor(self):
        print("\n   📋 Monitor de Red:\n")
        
        monitor = MonitorRed()
        
        for i in range(10):
            monitor.actualizar_metrica_nodo(f"nodo_{i}", random.randint(10, 300),
                                            paquetes_enviados=random.randint(100, 1000),
                                            paquetes_recibidos=random.randint(100, 1000))
        self.assert_true("10 nodos registrados", len(monitor.metricas_nodos) == 10)
        
        metrica = monitor.obtener_metricas_red()
        self.assert_true("Métricas de red", metrica.nodos_activos == 10)
        self.assert_true("Salud calculada", 0 <= metrica.salud_general <= 1)
        
        monitor.detectar_ataque("spam", {"txs": 1000})
        self.assert_true("Ataque registrado", any(e.tipo == "ataque" for e in monitor.eventos))
        
        datos_ia = monitor.exportar_para_ia()
        self.assert_true("Exportar para IA", "salud" in datos_ia)
    
    def _test_nodo(self):
        print("\n   📋 Nodo Completo:\n")
        
        nodo = NodoDireccoin(modo=ConfigNodo.MODO_MINERO)
        self.assert_true("Nodo creado", nodo.id_nodo is not None)
        
        nodo.iniciar()
        self.assert_true("Nodo iniciado", nodo.iniciado)
        
        sync = nodo.sincronizar()
        self.assert_true("Sincronizado", sync["sincronizado"])
        
        resultado = nodo.minar(100)
        self.assert_true("Minado ejecutado", "encontrado" in resultado)
        
        tx = {"origen": "drcA", "destino": "drcB", "cantidad": 500, "gas": 10}
        ok, txid = nodo.procesar_transaccion(tx)
        self.assert_true("Procesar transacción", ok)
        
        estado = nodo.obtener_estado()
        self.assert_true("Estado disponible", "altura" in estado)
        
        nodo.detener()
        self.assert_true("Nodo detenido", not nodo.ejecutando)
    
    def _test_consenso(self):
        print("\n   📋 Reglas de Consenso:\n")
        
        validador = ValidadorBloques()
        
        genesis = {
            "indice": 0, "hash_previo": "0" * 64, "timestamp": 1778279888,
            "transacciones": [], "nonce": 0, "dificultad": 1,
            "merkle_raiz": "0" * 64, "hash": "d1" + "0" * 62, "recompensa": 0
        }
        r = validador.validar_bloque_completo(genesis, es_genesis=True)
        self.assert_true("Génesis válido", r.valido)
        
        # Doble gasto
        vdg = VerificadorDobleGasto()
        ok, _ = vdg.verificar_transaccion({"txid": "tx001", "origen": "drcA", "cantidad": 100, "nonce": 1}, 1000)
        self.assert_true("Primera tx aceptada", ok)
        ok, _ = vdg.verificar_transaccion({"txid": "tx001", "origen": "drcA", "cantidad": 100, "nonce": 1}, 1000)
        self.assert_true("Doble gasto rechazado", not ok)
        
        # Finalidad
        gf = GestorFinalidad()
        for i in range(10):
            gf.registrar_bloque(f"bloque_{i}", i)
        self.assert_true("Bloque final (6+ conf)", gf.es_final("bloque_0"))
        self.assert_true("Bloque no final", not gf.es_final("bloque_8"))
    
    def _test_forks(self):
        print("\n   📋 Resolución de Forks:\n")
        
        resolver = ForkResolver()
        
        def crear_bloque(indice, hash_previo, hash_propio, dificultad=1):
            return {"indice": indice, "hash_previo": hash_previo, "hash": hash_propio, "dificultad": dificultad}
        
        principal = [crear_bloque(0, "0"*64, "genesis")]
        for i in range(1, 6):
            principal.append(crear_bloque(i, principal[-1]["hash"], f"ppal_{i}"))
        
        alternativa = principal[:3].copy()
        for i in range(3, 7):
            alternativa.append(crear_bloque(i, alternativa[-1]["hash"], f"alt_{i}", 2))
        
        fork_info = resolver.detectar_fork(principal, alternativa)
        self.assert_true("Fork detectado", fork_info is not None and fork_info["indice_fork"] == 3)
        
        self.assert_true("Cadenas idénticas: sin fork", resolver.detectar_fork(principal, principal) is None)
        
        resultado = resolver.resolver(principal, alternativa)
        self.assert_true("Alternativa gana (más trabajo)", resultado.hubo_reorganizacion)


if __name__ == "__main__":
    test = TestRed()
    test.ejecutar()