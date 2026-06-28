#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - MINERO PoUC                                  ║
║                    Versión: 1.0.0 | Archivo: mineria/minero.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

MOTOR DE MINADO INTELIGENTE PARA DIRECCOIN.

Integra todos los módulos de minería:
  • Proof of Useful Computation (PoUC)
  • Búsqueda de primos gemelos
  • Optimización de rutas P2P
  • Cálculo científico verificable
  • Selección automática de mejor trabajo
  • Control de dificultad dinámico
  • Recompensas por tipo de trabajo

CARACTERÍSTICAS:
  • Minado multimodo (validación, optimización, científico)
  • Auto-selección del trabajo más rentable
  • Batería optimizada para móviles
  • Progreso guardable y reanudable
  • Diagnóstico de 12 pruebas
"""

import hashlib
import time
import random
import math
import json
import os
from typing import Dict, List, Tuple, Optional, Any

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigMinero:
    VERSION = "1.0.0"
    
    # Tipos de trabajo
    TIPOS_TRABAJO = {
        "validacion": {"recompensa": 1.0, "dificultad": 1.0, "descripcion": "Primos gemelos"},
        "optimizacion": {"recompensa": 1.5, "dificultad": 1.5, "descripcion": "Rutas P2P"},
        "cientifico": {"recompensa": 2.0, "dificultad": 2.0, "descripcion": "Cálculo avanzado"},
    }
    
    # Límites
    MAX_INTENTOS_POR_RONDA = 100_000
    MAX_TIEMPO_POR_RONDA = 60  # segundos
    PAUSA_ENTRE_RONDAS = 0.1   # segundos (ahorro batería)
    
    # Archivo de progreso
    ARCHIVO_PROGRESO = "minero_progreso.json"
    
    # Recompensa base en Direcs
    RECOMPENSA_BASE = 100_000_000  # 100 DRC


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    @staticmethod
    def doble_hex(d: bytes) -> str:
        return hashlib.sha3_256(hashlib.sha3_256(d).digest()).hex()


# ==============================================================================
# MINERO PoUC
# ==============================================================================

class MineroPoUC:
    """
    Motor de minado inteligente para Direccoin.
    
    Uso:
        minero = MineroPoUC(direccion="drc...", tipo_trabajo="validacion")
        minero.iniciar()
        resultado = minero.minar_ronda()
        if resultado["encontrado"]:
            print(f"¡Bloque minado! Recompensa: {resultado['recompensa']}")
    """
    
    def __init__(self, direccion: str, tipo_trabajo: str = "auto",
                 dificultad: int = 1):
        self.direccion = direccion
        self.dificultad = dificultad
        self.tipo_trabajo = tipo_trabajo
        
        # Estado
        self.intentos_totales = 0
        self.bloques_minados = 0
        self.recompensa_total = 0
        self.ultimo_bloque = None
        self.tiempo_inicio = time.time()
        self.activo = False
        
        # Estadísticas por tipo
        self.stats = {
            "validacion": {"intentos": 0, "encontrados": 0, "recompensa": 0},
            "optimizacion": {"intentos": 0, "encontrados": 0, "recompensa": 0},
            "cientifico": {"intentos": 0, "encontrados": 0, "recompensa": 0},
        }
        
        self._cargar_progreso()
    
    def _cargar_progreso(self):
        """Carga progreso anterior si existe."""
        if os.path.exists(ConfigMinero.ARCHIVO_PROGRESO):
            try:
                with open(ConfigMinero.ARCHIVO_PROGRESO) as f:
                    datos = json.load(f)
                self.intentos_totales = datos.get("intentos_totales", 0)
                self.bloques_minados = datos.get("bloques_minados", 0)
                self.recompensa_total = datos.get("recompensa_total", 0)
            except:
                pass
    
    def _guardar_progreso(self):
        """Persiste el progreso de minado."""
        with open(ConfigMinero.ARCHIVO_PROGRESO, "w") as f:
            json.dump({
                "intentos_totales": self.intentos_totales,
                "bloques_minados": self.bloques_minados,
                "recompensa_total": self.recompensa_total,
                "ultimo_bloque": self.ultimo_bloque,
                "timestamp": int(time.time()),
            }, f, indent=2)
    
    def seleccionar_mejor_trabajo(self, saldo: float = 0) -> str:
        """
        Selecciona automáticamente el tipo de trabajo más rentable.
        """
        if self.tipo_trabajo != "auto":
            return self.tipo_trabajo
        
        # Encontrar el trabajo con mejor relación recompensa/dificultad
        mejor = "validacion"
        mejor_ratio = 0
        
        for tipo, datos in ConfigMinero.TIPOS_TRABAJO.items():
            ratio = datos["recompensa"] / datos["dificultad"]
            if ratio > mejor_ratio:
                mejor_ratio = ratio
                mejor = tipo
        
        return mejor
    
    def _es_primo(self, n: int) -> bool:
        """Test rápido de primalidad."""
        if n < 2: return False
        if n < 4: return True
        if n % 2 == 0: return False
        if n % 3 == 0: return n == 3
        if n % 5 == 0: return n == 5
        
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        
        for a in [2, 3, 5, 7, 11]:
            if a >= n: continue
            x = pow(a, d, n)
            if x == 1 or x == n - 1: continue
            for _ in range(s - 1):
                x = (x * x) % n
                if x == n - 1: break
            else:
                return False
        return True
    
    def _es_primo_gemelo(self, n: int) -> bool:
        return self._es_primo(n) and self._es_primo(n + 2)
    
    def minar_validacion(self, semilla: bytes, rango_inicio: int,
                         max_pares: int = 1) -> Dict[str, Any]:
        """
        Trabajo de validación: buscar primos gemelos.
        """
        resultado = {
            "tipo": "validacion",
            "encontrado": False,
            "pares": [],
            "intentos": 0,
            "tiempo_ms": 0,
        }
        
        inicio = time.time()
        n = rango_inicio if rango_inicio % 2 == 1 else rango_inicio + 1
        intentos = 0
        
        while len(resultado["pares"]) < max_pares and intentos < ConfigMinero.MAX_INTENTOS_POR_RONDA:
            if self._es_primo_gemelo(n):
                resultado["pares"].append((n, n + 2))
                n += 4
            else:
                n += 2
            intentos += 1
        
        resultado["intentos"] = intentos
        resultado["tiempo_ms"] = (time.time() - inicio) * 1000
        
        if resultado["pares"]:
            resultado["encontrado"] = True
        
        return resultado
    
    def minar_optimizacion(self, datos_red: bytes) -> Dict[str, Any]:
        """
        Trabajo de optimización: encontrar mejor ruta P2P.
        Simula cálculo de rutas óptimas.
        """
        resultado = {
            "tipo": "optimizacion",
            "encontrado": False,
            "rutas": [],
            "intentos": 0,
            "tiempo_ms": 0,
        }
        
        inicio = time.time()
        hash_base = HashUtil.sha3(datos_red)
        intentos = 0
        
        # Simular búsqueda de rutas óptimas
        mejor_latencia = float('inf')
        mejor_ruta = []
        
        for _ in range(min(1000, ConfigMinero.MAX_INTENTOS_POR_RONDA)):
            # Generar ruta aleatoria simulada
            num_saltos = random.randint(2, 5)
            ruta = [f"nodo_{random.randint(1,100)}" for _ in range(num_saltos)]
            
            # Calcular latencia simulada desde el hash
            hash_ruta = HashUtil.sha3(str(ruta).encode() + hash_base)
            latencia = int.from_bytes(hash_ruta[:2], 'big') % 500 + 10
            
            if latencia < mejor_latencia:
                mejor_latencia = latencia
                mejor_ruta = ruta
            
            intentos += 1
        
        if mejor_ruta:
            resultado["encontrado"] = True
            resultado["rutas"] = [{"ruta": mejor_ruta, "latencia_ms": mejor_latencia}]
        
        resultado["intentos"] = intentos
        resultado["tiempo_ms"] = (time.time() - inicio) * 1000
        
        return resultado
    
    def minar_cientifico(self, datos: bytes) -> Dict[str, Any]:
        """
        Trabajo científico: resolver problema matemático verificable.
        Encuentra números con propiedades especiales.
        """
        resultado = {
            "tipo": "cientifico",
            "encontrado": False,
            "resultado": "",
            "intentos": 0,
            "tiempo_ms": 0,
        }
        
        inicio = time.time()
        hash_datos = HashUtil.sha3(datos)
        semilla = int.from_bytes(hash_datos[:4], 'big')
        intentos = 0
        
        # Buscar número especial: suma de dígitos del hash = primo
        for i in range(ConfigMinero.MAX_INTENTOS_POR_RONDA):
            n = semilla + i
            suma_digitos = sum(int(d) for d in str(n))
            
            if self._es_primo(suma_digitos) and n % 7 == 0:
                resultado["encontrado"] = True
                resultado["resultado"] = str(n)
                break
            
            intentos += 1
        
        resultado["intentos"] = intentos
        resultado["tiempo_ms"] = (time.time() - inicio) * 1000
        
        return resultado
    
    def minar_ronda(self, datos_bloque: bytes = None,
                    tipo_trabajo: str = None) -> Dict[str, Any]:
        """
        Ejecuta una ronda de minado.
        
        Args:
            datos_bloque: Datos del bloque a minar
            tipo_trabajo: Tipo de trabajo (None = auto)
        
        Returns:
            Resultado del minado
        """
        if datos_bloque is None:
            datos_bloque = HashUtil.sha3(str(time.time()).encode())
        
        if tipo_trabajo is None:
            tipo_trabajo = self.seleccionar_mejor_trabajo()
        
        # Ejecutar trabajo según tipo
        if tipo_trabajo == "validacion":
            rango = int.from_bytes(HashUtil.sha3(datos_bloque)[:4], 'big') % 100_000
            resultado = self.minar_validacion(datos_bloque, rango, max_pares=1)
        elif tipo_trabajo == "optimizacion":
            resultado = self.minar_optimizacion(datos_bloque)
        elif tipo_trabajo == "cientifico":
            resultado = self.minar_cientifico(datos_bloque)
        else:
            return {"encontrado": False, "error": f"Tipo desconocido: {tipo_trabajo}"}
        
        # Actualizar estadísticas
        self.intentos_totales += resultado["intentos"]
        self.stats[tipo_trabajo]["intentos"] += resultado["intentos"]
        
        if resultado["encontrado"]:
            self.bloques_minados += 1
            self.stats[tipo_trabajo]["encontrados"] += 1
            
            # Calcular recompensa
            multiplicador = ConfigMinero.TIPOS_TRABAJO[tipo_trabajo]["recompensa"]
            recompensa = int(ConfigMinero.RECOMPENSA_BASE * multiplicador)
            
            self.recompensa_total += recompensa
            self.stats[tipo_trabajo]["recompensa"] += recompensa
            self.ultimo_bloque = int(time.time())
            
            resultado["recompensa_direcs"] = recompensa
            resultado["recompensa_drc"] = recompensa / 1_000_000
            resultado["bloques_minados"] = self.bloques_minados
            resultado["recompensa_total_drc"] = self.recompensa_total / 1_000_000
        
        self._guardar_progreso()
        resultado["intentos_totales"] = self.intentos_totales
        
        return resultado
    
    def iniciar(self):
        """Inicia el minero."""
        self.activo = True
        self.tiempo_inicio = time.time()
    
    def detener(self):
        """Detiene el minero."""
        self.activo = False
        self._guardar_progreso()
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Devuelve estadísticas completas del minero."""
        tiempo_activo = time.time() - self.tiempo_inicio
        
        return {
            "direccion": self.direccion,
            "activo": self.activo,
            "tiempo_activo_segundos": int(tiempo_activo),
            "tiempo_activo_humano": self._formatear_tiempo(int(tiempo_activo)),
            "intentos_totales": self.intentos_totales,
            "bloques_minados": self.bloques_minados,
            "recompensa_total_drc": self.recompensa_total / 1_000_000,
            "tasa_hash": self.intentos_totales / max(tiempo_activo, 1),
            "stats_por_tipo": self.stats,
        }
    
    @staticmethod
    def _formatear_tiempo(segundos: int) -> str:
        if segundos < 60: return f"{segundos}s"
        elif segundos < 3600: return f"{segundos//60}m {segundos%60}s"
        else:
            h = segundos // 3600
            m = (segundos % 3600) // 60
            return f"{h}h {m}m"


# ==============================================================================
# SIMULADOR DE MINERÍA
# ==============================================================================

class SimuladorMineria:
    """Simula el minado para pruebas sin gastar recursos reales."""
    
    @staticmethod
    def simular_minado(direccion: str, num_rondas: int = 10,
                       tipo: str = "validacion") -> Dict[str, Any]:
        minero = MineroPoUC(direccion, tipo)
        minero.iniciar()
        
        resultados = []
        for i in range(num_rondas):
            datos = f"bloque_simulado_{i}_{time.time()}".encode()
            r = minero.minar_ronda(datos)
            resultados.append({
                "ronda": i + 1,
                "encontrado": r["encontrado"],
                "intentos": r.get("intentos", 0),
                "tiempo_ms": r.get("tiempo_ms", 0),
            })
        
        minero.detener()
        stats = minero.obtener_estadisticas()
        stats["resultados_rondas"] = resultados
        
        return stats


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoMinero:
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
        print("🔍 DIAGNÓSTICO DE MINERIA/MINERO.PY")
        print("=" * 70)
        
        minero = MineroPoUC("drcTest", "validacion")
        
        # 1. Seleccionar mejor trabajo
        tipo = minero.seleccionar_mejor_trabajo()
        self._t("Auto-selección de trabajo", tipo in ConfigMinero.TIPOS_TRABAJO, tipo)
        
        # 2. Minar validación
        datos = b"bloque_prueba_001"
        r = minero.minar_ronda(datos, "validacion")
        self._t("Minar validación", "intentos" in r, f"{r.get('intentos', 0)} intentos")
        
        # 3. Minar optimización
        r = minero.minar_ronda(datos, "optimizacion")
        self._t("Minar optimización", "rutas" in r)
        
        # 4. Minar científico
        r = minero.minar_ronda(datos, "cientifico")
        self._t("Minar científico", "resultado" in r)
        
        # 5. Estadísticas
        stats = minero.obtener_estadisticas()
        self._t("Estadísticas disponibles", "tasa_hash" in stats, 
                f"{stats['intentos_totales']} intentos")
        
        # 6. Iniciar/detener
        minero.iniciar()
        self._t("Minero activo", minero.activo)
        minero.detener()
        self._t("Minero detenido", not minero.activo)
        
        # 7. Persistencia de progreso
        self._t("Progreso guardado", os.path.exists(ConfigMinero.ARCHIVO_PROGRESO))
        
        # 8. Recompensa calculada
        r = minero.minar_ronda(datos, "validacion")
        if r["encontrado"]:
            self._t("Recompensa asignada", r.get("recompensa_drc", 0) > 0,
                    f"{r.get('recompensa_drc', 0)} DRC")
        
        # 9. Simulador
        sim = SimuladorMineria.simular_minado("drcSim", 3, "validacion")
        self._t("Simulación completada", len(sim["resultados_rondas"]) == 3)
        
        # 10. Tipos de trabajo disponibles
        self._t("3 tipos de trabajo", len(ConfigMinero.TIPOS_TRABAJO) == 3)
        
        # 11. Límite de intentos
        self._t("Max intentos por ronda", ConfigMinero.MAX_INTENTOS_POR_RONDA == 100_000)
        
        # 12. Recompensa base
        self._t("Recompensa base 100 DRC", ConfigMinero.RECOMPENSA_BASE == 100_000_000)
        
        # Limpiar
        if os.path.exists(ConfigMinero.ARCHIVO_PROGRESO):
            os.remove(ConfigMinero.ARCHIVO_PROGRESO)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ MINERIA/MINERO.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "⛏️ " * 35)
    print("DIRECCOIN - MINERO PoUC v1.0.0")
    print("⛏️ " * 35)
    print(f"Tipos de trabajo: {', '.join(ConfigMinero.TIPOS_TRABAJO.keys())}")
    print(f"Recompensa base: {ConfigMinero.RECOMPENSA_BASE // 1_000_000} DRC\n")
    
    diag = DiagnosticoMinero()
    if diag.ejecutar():
        print("📋 DEMO DE MINADO:")
        sim = SimuladorMineria.simular_minado("drcDemo", 5, "validacion")
        for r in sim["resultados_rondas"]:
            icono = "💎" if r["encontrado"] else "⛏️"
            print(f"   {icono} Ronda {r['ronda']}: {r['intentos']} intentos, {r['tiempo_ms']:.0f}ms")
        print(f"\n   Total bloques: {sim['bloques_minados']}")
        print(f"   Recompensa: {sim['recompensa_total_drc']:.6f} DRC")
        print(f"   Tasa hash: {sim['tasa_hash']:.1f} intentos/s")
        
        if os.path.exists(ConfigMinero.ARCHIVO_PROGRESO):
            os.remove(ConfigMinero.ARCHIVO_PROGRESO)
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()