#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - GENERADOR DE PRIMOS                          ║
║                    Versión: 1.0.1 | Archivo: mineria/primos.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE GENERACIÓN Y VERIFICACIÓN DE NÚMEROS PRIMOS PARA DIRECCOIN.
Parte del sistema PoUC (Proof of Useful Computation).
"""

import random
import math
import time
import hashlib
from typing import List, Tuple, Optional

class ConfigPrimos:
    VERSION = "1.0.1"
    TAMANO_CACHE = 1000
    RANGO_MINIMO = 1000
    RANGO_MAXIMO = 10_000_000
    BASES_MILLER_RABIN = [2, 3, 5, 7, 11, 13]
    BASES_GRANDES = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]


class MathUtil:
    @staticmethod
    def raiz_cuadrada_entera(n: int) -> int:
        if n < 0: raise ValueError("No se puede calcular raíz de negativo")
        if n == 0: return 0
        return int(math.isqrt(n))


class PruebaPrimalidad:
    
    @staticmethod
    def miller_rabin(n: int, bases: List[int] = None) -> bool:
        if n < 2: return False
        if n == 2: return True
        if n % 2 == 0: return False
        
        if bases is None:
            bases = ConfigPrimos.BASES_MILLER_RABIN if n < 3_474_749_660_383 else ConfigPrimos.BASES_GRANDES
        
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        
        for a in bases:
            if a >= n: continue
            x = pow(a, d, n)
            if x == 1 or x == n - 1: continue
            compuesto = True
            for _ in range(s - 1):
                x = (x * x) % n
                if x == n - 1:
                    compuesto = False
                    break
            if compuesto: return False
        return True
    
    @staticmethod
    def es_primo(n: int) -> bool:
        if n < 2: return False
        if n < 4: return True
        if n % 2 == 0: return False
        if n % 3 == 0: return n == 3
        if n % 5 == 0: return n == 5
        return PruebaPrimalidad.miller_rabin(n)
    
    @staticmethod
    def es_primo_gemelo(n: int) -> bool:
        return PruebaPrimalidad.es_primo(n) and PruebaPrimalidad.es_primo(n + 2)


class GeneradorPrimos:
    
    def __init__(self):
        self.cache: List[int] = []
        self.primos_encontrados = 0
    
    def primos_en_rango(self, inicio: int, fin: int, max_primos: int = 100) -> List[int]:
        if inicio < 2: inicio = 2
        if fin < inicio: return []
        if fin - inicio > ConfigPrimos.RANGO_MAXIMO:
            fin = inicio + ConfigPrimos.RANGO_MAXIMO
        
        primos = []
        n = inicio if inicio % 2 == 1 else inicio + 1
        while n <= fin and len(primos) < max_primos:
            if PruebaPrimalidad.es_primo(n): primos.append(n)
            n += 2
        return primos
    
    def buscar_primos_gemelos(self, inicio: int, max_pares: int = 10) -> List[Tuple[int, int]]:
        pares = []
        n = inicio if inicio % 2 == 1 else inicio + 1
        while len(pares) < max_pares:
            if n > ConfigPrimos.RANGO_MAXIMO: break
            if PruebaPrimalidad.es_primo_gemelo(n):
                pares.append((n, n + 2))
                n += 4
            else:
                n += 2
        return pares
    
    def siguiente_primo(self, n: int) -> int:
        if n < 2: return 2
        candidato = n + 1 if n % 2 == 0 else n + 2
        while not PruebaPrimalidad.es_primo(candidato): candidato += 2
        return candidato
    
    def primo_aleatorio(self, bits: int = 16) -> int:
        if bits < 4: bits = 4
        while True:
            n = random.getrandbits(bits)
            n |= (1 << (bits - 1)) | 1
            if PruebaPrimalidad.es_primo(n): return n
    
    def factorizar(self, n: int) -> List[int]:
        factores = []
        temp = n
        while temp % 2 == 0:
            factores.append(2)
            temp //= 2
        d = 3
        limite = MathUtil.raiz_cuadrada_entera(temp)
        while d <= limite:
            while temp % d == 0:
                factores.append(d)
                temp //= d
                limite = MathUtil.raiz_cuadrada_entera(temp)
            d += 2
        if temp > 1: factores.append(temp)
        return factores


class TrabajoMineria:
    
    def __init__(self):
        self.generador = GeneradorPrimos()
    
    def generar_desafio(self, semilla: bytes, dificultad: int = 1) -> dict:
        hash_semilla = hashlib.sha3_256(semilla).digest()
        rango_inicio = int.from_bytes(hash_semilla[:4], 'big') % 1_000_000
        rango_fin = rango_inicio + (dificultad * 10000)
        return {
            "tipo": "primos_gemelos",
            "rango_inicio": rango_inicio,
            "rango_fin": rango_fin,
            "dificultad": dificultad,
            "hash_semilla": hash_semilla.hex(),
        }
    
    def verificar_solucion(self, desafio: dict, solucion: dict) -> Tuple[bool, str]:
        if desafio.get("tipo") != "primos_gemelos":
            return False, "Tipo de desafío incorrecto"
        pares = solucion.get("pares", [])
        if not pares:
            return False, "Sin pares encontrados"
        rango_ini = desafio["rango_inicio"]
        rango_fin = desafio["rango_fin"]
        for p1, p2 in pares:
            if p1 < rango_ini or p2 > rango_fin:
                return False, f"Par ({p1},{p2}) fuera de rango [{rango_ini},{rango_fin}]"
            if p2 != p1 + 2:
                return False, f"({p1},{p2}) no son gemelos"
            if not PruebaPrimalidad.es_primo_gemelo(p1):
                return False, f"({p1},{p2}) no son primos gemelos válidos"
        return True, f"{len(pares)} pares de primos gemelos válidos"


class DiagnosticoPrimos:
    def __init__(self):
        self.ok = 0
        self.fail = 0
    def _t(self, n, ok, d=""):
        s = "✅" if ok else "❌"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE MINERIA/PRIMOS.PY")
        print("=" * 70)
        
        self._t("2 es primo", PruebaPrimalidad.es_primo(2))
        self._t("3 es primo", PruebaPrimalidad.es_primo(3))
        self._t("4 no es primo", not PruebaPrimalidad.es_primo(4))
        self._t("97 es primo", PruebaPrimalidad.es_primo(97))
        self._t("100 no es primo", not PruebaPrimalidad.es_primo(100))
        self._t("Miller-Rabin: 9973 es primo", PruebaPrimalidad.miller_rabin(9973))
        self._t("(5,7) son gemelos", PruebaPrimalidad.es_primo_gemelo(5))
        self._t("(7,9) no son gemelos", not PruebaPrimalidad.es_primo_gemelo(7))
        self._t("(11,13) son gemelos", PruebaPrimalidad.es_primo_gemelo(11))
        
        gen = GeneradorPrimos()
        primos = gen.primos_en_rango(100, 200, 5)
        self._t("Primos en rango (100,200)", len(primos) == 5)
        
        sp = gen.siguiente_primo(100)
        self._t("Siguiente primo > 100: 101", sp == 101)
        
        pares = gen.buscar_primos_gemelos(1, 3)
        self._t("Primeros 3 pares gemelos", len(pares) == 3)
        
        # Verificar solución con rango conocido
        tm = TrabajoMineria()
        desafio_fijo = {"tipo": "primos_gemelos", "rango_inicio": 1, "rango_fin": 30,
                       "dificultad": 1, "hash_semilla": "aa"}
        solucion_fija = {"pares": [(3, 5), (5, 7), (11, 13)]}
        ok, msg = tm.verificar_solucion(desafio_fijo, solucion_fija)
        self._t("Verificar solución", ok, msg[:30])
        
        # Rechazar solución inválida
        sol_mala = {"pares": [(4, 6)]}
        ok, _ = tm.verificar_solucion(desafio_fijo, sol_mala)
        self._t("Rechazar solución falsa", not ok)
        
        factores = gen.factorizar(84)
        self._t("Factorizar 84 = 2*2*3*7", factores == [2, 2, 3, 7])
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ MINERIA/PRIMOS.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "🔢 " * 35)
    print("DIRECCOIN - GENERADOR DE PRIMOS v1.0.1")
    print("🔢 " * 35)
    print(f"Bases Miller-Rabin: {ConfigPrimos.BASES_MILLER_RABIN}")
    print(f"Cache: {ConfigPrimos.TAMANO_CACHE} primos\n")
    diag = DiagnosticoPrimos()
    if diag.ejecutar():
        gen = GeneradorPrimos()
        print("📋 DEMO:")
        inicio = time.time()
        primo = gen.primo_aleatorio(32)
        fin = time.time()
        print(f"   Primo aleatorio (32 bits): {primo}")
        print(f"   Tiempo: {(fin - inicio)*1000:.2f} ms")
        pares = gen.buscar_primos_gemelos(100, 3)
        print(f"   Primeros 3 pares gemelos > 100: {pares}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()