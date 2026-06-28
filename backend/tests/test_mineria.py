#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - TEST DE MINERÍA                             ║
║                    Versión: 1.0.0 | Archivo: tests/test_mineria.py        ║
╚══════════════════════════════════════════════════════════════════════════════╝

PRUEBAS UNITARIAS DEL SISTEMA DE MINERÍA POUC.

Verifica:
  • Verificador de trabajo
  • Generador de primos
  • Control de dificultad
  • Minero PoUC
  • Optimizador de rutas
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Importar módulos de minería
from mineria.verificador import VerificadorHash, VerificadorPoUC, VerificadorRecompensa
from mineria.primos import PruebaPrimalidad, GeneradorPrimos, TrabajoMineria
from mineria.dificultad import ControlDificultad, ConfigDificultad
from mineria.ruteo_util import GrafoRed, Enrutador, SelectorSuperPares, ConstructorRedPrueba
from mineria.minero import MineroPoUC, ConfigMinero

class TestMineria:
    
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
        print("🧪 TEST DE MINERIA (PoUC)")
        print("=" * 70)
        
        self._test_verificador()
        self._test_primos()
        self._test_dificultad()
        self._test_ruteo()
        self._test_minero()
        
        total = self.pasados + self.fallidos
        print("─" * 70)
        print(f"📊 {self.pasados}/{total} PASADOS | {self.fallidos} FALLIDOS")
        print("─" * 70)
        if self.fallidos == 0:
            print("✅ TODAS LAS PRUEBAS DE MINERÍA PASARON\n")
        else:
            print(f"❌ {self.fallidos} PRUEBAS FALLARON\n")
            for e in self.errores:
                print(f"   • {e}")
        return self.fallidos == 0
    
    def _test_verificador(self):
        print("\n   📋 Verificador de trabajo:\n")
        
        vh = VerificadorHash()
        self.assert_true("Cumple dificultad 1", vh.cumple_dificultad("d1abc", 1))
        self.assert_true("Cumple dificultad 3", vh.cumple_dificultad("d10ab", 2))
        self.assert_true("No cumple sin d1", not vh.cumple_dificultad("ffabc", 1))
        
        vp = VerificadorPoUC()
        self.assert_true("9973 es primo", vp.es_primo(9973))
        self.assert_true("8 no es primo", not vp.es_primo(8))
        
        ok, msg, mult = vp.verificar_trabajo_util("validacion", {"numero": 11})
        self.assert_true("Trabajo validación (11,13)", ok and mult == 1.0)
        
        vr = VerificadorRecompensa()
        ok, msg, rec = vr.verificar_recompensa(100_000_000, 1, "validacion")
        self.assert_true("Recompensa correcta", ok)
        
        ok, msg, rec = vr.verificar_recompensa(999_999_999, 1, "validacion")
        self.assert_true("Recompensa excesiva rechazada", not ok)
    
    def _test_primos(self):
        print("\n   📋 Generador de primos:\n")
        
        pp = PruebaPrimalidad()
        self.assert_true("2 es primo", pp.es_primo(2))
        self.assert_true("97 es primo", pp.es_primo(97))
        self.assert_true("100 no es primo", not pp.es_primo(100))
        self.assert_true("(5,7) gemelos", pp.es_primo_gemelo(5))
        self.assert_true("(7,9) no gemelos", not pp.es_primo_gemelo(7))
        
        gen = GeneradorPrimos()
        primos = gen.primos_en_rango(100, 200, 5)
        self.assert_true("Primos en rango", len(primos) == 5)
        
        sp = gen.siguiente_primo(100)
        self.assert_equals("Siguiente primo >100", sp, 101)
        
        pares = gen.buscar_primos_gemelos(1, 3)
        self.assert_true("3 pares gemelos", len(pares) == 3)
        
        factores = gen.factorizar(84)
        self.assert_true("Factorizar 84", factores == [2, 2, 3, 7])
    
    def _test_dificultad(self):
        print("\n   📋 Control de dificultad:\n")
        
        cd = ControlDificultad(1)
        self.assert_equals("Dificultad inicial", cd.dificultad_actual, 1)
        
        # Ajuste normal
        bloques = []
        for i in range(1000):
            bloques.append({"indice": i, "timestamp": i * 8, "dificultad": 1})
        d = cd.calcular(bloques)
        self.assert_true("Ajuste normal estable", abs(d - 1) <= 1)
        
        # Anti-ballena
        d_normal = cd.dificultad_para_minero(1_000_000, "validacion")
        d_ballena = cd.dificultad_para_minero(1_000_000_000, "validacion")
        self.assert_true("Anti-ballena", d_ballena >= d_normal)
        
        # Por tipo
        d_val = cd.dificultad_para_minero(0, "validacion")
        d_cien = cd.dificultad_para_minero(0, "cientifico")
        self.assert_true("Científico más difícil", d_cien >= d_val)
        
        # Verificar hash
        ok, _ = cd.verificar_dificultad_bloque("d10abc", 1)
        self.assert_true("Hash cumple dificultad", ok)
    
    def _test_ruteo(self):
        print("\n   📋 Optimizador de rutas:\n")
        
        grafo = ConstructorRedPrueba.crear_red_aleatoria(15)
        self.assert_true("Grafo con 15 nodos", grafo.tamano() == 15)
        
        enrutador = Enrutador(grafo)
        ids = list(grafo.nodos.keys())
        ruta, costo = enrutador.ruta_mas_corta(ids[0], ids[-1])
        self.assert_true("Dijkstra encuentra ruta", len(ruta) > 0 and costo < float('inf'))
        
        ruta_self, costo_self = enrutador.ruta_mas_corta(ids[0], ids[0])
        self.assert_equals("Ruta a sí mismo", costo_self, 0)
        
        selector = SelectorSuperPares(grafo)
        sp = selector.seleccionar(5)
        self.assert_true("5 superpares", len(sp) == 5)
    
    def _test_minero(self):
        print("\n   📋 Minero PoUC:\n")
        
        minero = MineroPoUC("drcTest", "validacion")
        self.assert_true("Minero creado", minero is not None)
        
        tipo = minero.seleccionar_mejor_trabajo()
        self.assert_true("Auto-selección", tipo in ConfigMinero.TIPOS_TRABAJO)
        
        datos = b"bloque_prueba_mineria"
        resultado = minero.minar_ronda(datos, "validacion")
        self.assert_true("Minado ejecutado", "intentos" in resultado)
        
        minero.iniciar()
        self.assert_true("Minero activo", minero.activo)
        minero.detener()
        self.assert_true("Minero detenido", not minero.activo)
        
        stats = minero.obtener_estadisticas()
        self.assert_true("Estadísticas", "tasa_hash" in stats)


if __name__ == "__main__":
    test = TestMineria()
    test.ejecutar()