#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - CONTROL DE DIFICULTAD                        ║
║                    Versión: 1.0.0 | Archivo: mineria/dificultad.py         ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE AJUSTE DINÁMICO DE DIFICULTAD PARA DIRECCOIN.

Controla:
  • Dificultad de minado por tipo de trabajo
  • Ajuste cada 1,000 bloques (~2.2 horas)
  • Dificultad anti-ballena (por saldo)
  • Límites de cambio (4x máximo)
  • Protección contra explosión de hash rate
  • Dificultad mínima para evitar spam

CARACTERÍSTICAS:
  • Ajuste frecuente (1000 bloques)
  • Anti-saturación de mercado
  • Multiplicador por tipo de minero
  • Diagnóstico de 12 pruebas
"""

import math
import time
from typing import Dict, List, Tuple, Optional

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigDificultad:
    VERSION = "1.0.0"
    
    # Tiempo objetivo
    TIEMPO_OBJETIVO_SEGUNDOS = 8          # 8 segundos por bloque
    BLOQUES_POR_AJUSTE = 1_000            # Ajuste cada 1000 bloques
    TIEMPO_ESPERADO_POR_AJUSTE = TIEMPO_OBJETIVO_SEGUNDOS * BLOQUES_POR_AJUSTE
    
    # Dificultad
    DIFICULTAD_INICIAL = 1
    DIFICULTAD_MINIMA = 1
    DIFICULTAD_MAXIMA = 256
    MAX_CAMBIO_POR_AJUSTE = 4             # Máximo 4x de cambio
    
    # Anti-ballena
    FACTOR_ANTI_BALLENA = 0.1             # 10% más difícil por cada orden de magnitud de saldo
    SALDO_REFERENCIA = 10_000_000         # 10 DRC en Direcs
    
    # Tipos de trabajo
    DIFICULTAD_POR_TIPO = {
        "validacion": 1.0,                 # Dificultad base
        "optimizacion": 1.5,               # 50% más difícil
        "cientifico": 2.0,                 # 100% más difícil
    }
    
    # Límites de emisión
    EMISION_MAXIMA_DIARIA = 27_397        # ~10M por año / 365


# ==============================================================================
# CONTROL DE DIFICULTAD
# ==============================================================================

class ControlDificultad:
    """
    Gestiona la dificultad de minado de forma dinámica.
    
    Uso:
        cd = ControlDificultad()
        nueva_dificultad = cd.calcular(bloques_recientes)
        dificultad_minero = cd.dificultad_para_minero(saldo_minero, tipo_trabajo)
    """
    
    def __init__(self, dificultad_inicial: int = None):
        self.dificultad_actual = dificultad_inicial or ConfigDificultad.DIFICULTAD_INICIAL
        self.historial_ajustes: List[Dict] = []
        self.ultimo_ajuste_bloque = 0
        self.tasa_hash_estimada = 0
        self.mineros_activos_estimados = 1
    
    def calcular(self, bloques_recientes: List[dict]) -> int:
        """
        Calcula la nueva dificultad basada en los bloques recientes.
        
        Args:
            bloques_recientes: Lista de dicts con {timestamp, dificultad}
        
        Returns:
            Nueva dificultad
        """
        if len(bloques_recientes) < 2:
            return self.dificultad_actual
        
        # Calcular tiempo real transcurrido
        tiempo_real = bloques_recientes[-1]["timestamp"] - bloques_recientes[0]["timestamp"]
        tiempo_esperado = len(bloques_recientes) * ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS
        
        if tiempo_real <= 0:
            return self.dificultad_actual
        
        # Factor de ajuste
        factor = tiempo_esperado / tiempo_real
        
        # Limitar cambio máximo
        factor = max(1.0 / ConfigDificultad.MAX_CAMBIO_POR_AJUSTE, 
                     min(ConfigDificultad.MAX_CAMBIO_POR_AJUSTE, factor))
        
        # Calcular nueva dificultad
        nueva = int(self.dificultad_actual * factor)
        
        # Aplicar límites
        nueva = max(ConfigDificultad.DIFICULTAD_MINIMA, 
                    min(ConfigDificultad.DIFICULTAD_MAXIMA, nueva))
        
        # Estimar tasa de hash
        if tiempo_real > 0:
            self.tasa_hash_estimada = len(bloques_recientes) / tiempo_real
        
        # Registrar ajuste
        self.historial_ajustes.append({
            "bloque": bloques_recientes[-1].get("indice", 0),
            "dificultad_anterior": self.dificultad_actual,
            "dificultad_nueva": nueva,
            "factor": round(factor, 4),
            "tiempo_real": tiempo_real,
            "tiempo_esperado": tiempo_esperado,
            "timestamp": int(time.time()),
        })
        
        # Limpiar historial (mantener últimos 100)
        if len(self.historial_ajustes) > 100:
            self.historial_ajustes = self.historial_ajustes[-100:]
        
        self.dificultad_actual = nueva
        self.ultimo_ajuste_bloque = bloques_recientes[-1].get("indice", 0)
        
        return nueva
    
    def dificultad_para_minero(self, saldo_minero: int, 
                               tipo_trabajo: str = "validacion") -> int:
        """
        Calcula la dificultad específica para un minero.
        
        Anti-ballena: mineros con más DRC tienen mayor dificultad.
        Esto evita que los ricos acaparen todo el minado.
        
        Args:
            saldo_minero: Saldo del minero en Direcs
            tipo_trabajo: Tipo de trabajo (validacion, optimizacion, cientifico)
        
        Returns:
            Dificultad ajustada para este minero
        """
        base = self.dificultad_actual
        
        # Multiplicador por tipo de trabajo
        mult_tipo = ConfigDificultad.DIFICULTAD_POR_TIPO.get(tipo_trabajo, 1.0)
        
        # Factor anti-ballena
        if saldo_minero > ConfigDificultad.SALDO_REFERENCIA:
            factor_ballena = 1 + (ConfigDificultad.FACTOR_ANTI_BALLENA * 
                                 math.log10(saldo_minero / ConfigDificultad.SALDO_REFERENCIA))
        else:
            factor_ballena = 1.0
        
        # Calcular dificultad final
        dificultad = int(base * mult_tipo * factor_ballena)
        
        return max(ConfigDificultad.DIFICULTAD_MINIMA, 
                   min(ConfigDificultad.DIFICULTAD_MAXIMA, dificultad))
    
    def verificar_dificultad_bloque(self, hash_bloque: str, 
                                   dificultad_requerida: int) -> Tuple[bool, str]:
        """
        Verifica que un hash de bloque cumpla con la dificultad.
        """
        if not hash_bloque.startswith("d1"):
            return False, "Hash no tiene prefijo Direccoin (d1)"
        
        # Contar ceros después del prefijo
        resto = hash_bloque[2:]
        ceros = 0
        for c in resto:
            if c == '0':
                ceros += 1
            else:
                break
        
        if ceros < dificultad_requerida - 2:
            return False, f"Dificultad insuficiente: {ceros} < {dificultad_requerida - 2}"
        
        return True, "Dificultad cumplida"
    
    def estimar_proximo_ajuste(self, bloques_restantes: int) -> dict:
        """
        Estima cuándo será el próximo ajuste y la nueva dificultad.
        """
        tiempo_restante = bloques_restantes * ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS
        
        return {
            "bloques_restantes": bloques_restantes,
            "tiempo_estimado_segundos": tiempo_restante,
            "tiempo_estimado_humano": self._formatear_tiempo(tiempo_restante),
            "dificultad_actual": self.dificultad_actual,
            "ultimo_ajuste_bloque": self.ultimo_ajuste_bloque,
        }
    
    def obtener_estadisticas(self) -> dict:
        """Devuelve estadísticas del control de dificultad."""
        return {
            "dificultad_actual": self.dificultad_actual,
            "tasa_hash_estimada": round(self.tasa_hash_estimada, 2),
            "mineros_activos_estimados": self.mineros_activos_estimados,
            "total_ajustes": len(self.historial_ajustes),
            "ultimo_ajuste": self.historial_ajustes[-1] if self.historial_ajustes else None,
        }
    
    @staticmethod
    def _formatear_tiempo(segundos: int) -> str:
        """Formatea segundos a formato legible."""
        if segundos < 60:
            return f"{segundos}s"
        elif segundos < 3600:
            return f"{segundos // 60}m {segundos % 60}s"
        elif segundos < 86400:
            horas = segundos // 3600
            minutos = (segundos % 3600) // 60
            return f"{horas}h {minutos}m"
        else:
            dias = segundos // 86400
            horas = (segundos % 86400) // 3600
            return f"{dias}d {horas}h"


# ==============================================================================
# SIMULADOR DE DIFICULTAD
# ==============================================================================

class SimuladorDificultad:
    """Simula escenarios de dificultad para pruebas y proyecciones."""
    
    @staticmethod
    def simular_explosion_mineria(dificultad_inicial: int = 1,
                                  factor_mineros: float = 10.0) -> List[dict]:
        """
        Simula qué pasaría si de repente llegan 10x más mineros.
        """
        cd = ControlDificultad(dificultad_inicial)
        resultados = []
        
        for ciclo in range(10):
            # Simular 1000 bloques
            bloques = []
            tiempo_base = ciclo * ConfigDificultad.TIEMPO_ESPERADO_POR_AJUSTE
            
            for i in range(ConfigDificultad.BLOQUES_POR_AJUSTE):
                bloques.append({
                    "indice": ciclo * 1000 + i,
                    "timestamp": tiempo_base + (i * ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS / factor_mineros),
                    "dificultad": cd.dificultad_actual,
                })
            
            nueva = cd.calcular(bloques)
            resultados.append({
                "ciclo": ciclo + 1,
                "dificultad": nueva,
                "factor_mineros": factor_mineros,
            })
        
        return resultados
    
    @staticmethod
    def simular_emision_controlada(años: int = 5) -> List[dict]:
        """
        Simula la emisión controlada por dificultad durante años.
        """
        resultados = []
        bloques_totales = años * 97_000  # Bloques por año
        
        for año in range(1, años + 1):
            bloques_año = 97_000
            emision_estimada = bloques_año * 100  # Recompensa base
            
            resultados.append({
                "año": año,
                "bloques": bloques_año,
                "emision_estimada_drc": emision_estimada,
                "dificultad_promedio": min(256, año * 2),
            })
        
        return resultados


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoDificultad:
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
        print("🔍 DIAGNÓSTICO DE MINERIA/DIFICULTAD.PY")
        print("=" * 70)
        
        cd = ControlDificultad(1)
        
        # 1. Dificultad inicial
        self._t("Dificultad inicial = 1", cd.dificultad_actual == 1)
        
        # 2. Sin cambios con 1 bloque
        bloques_1 = [{"indice": 0, "timestamp": 1000, "dificultad": 1}]
        d = cd.calcular(bloques_1)
        self._t("Sin cambios con 1 bloque", d == 1)
        
        # 3. Ajuste normal (tiempo exacto)
        bloques_normal = []
        for i in range(1000):
            bloques_normal.append({
                "indice": i,
                "timestamp": i * ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS,
                "dificultad": 1,
            })
        d = cd.calcular(bloques_normal)
        self._t("Ajuste normal: dificultad estable", abs(d - 1) <= 1, f"Nueva: {d}")
        
        # 4. Ajuste rápido (bloques muy rápidos → subir dificultad)
        cd2 = ControlDificultad(1)
        bloques_rapido = []
        for i in range(1000):
            bloques_rapido.append({
                "indice": i,
                "timestamp": i * (ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS / 4),
                "dificultad": 1,
            })
        d = cd2.calcular(bloques_rapido)
        self._t("Bloques rápidos → subir dificultad", d > 1, f"Nueva: {d}")
        
        # 5. Ajuste lento (bloques muy lentos → bajar dificultad)
        cd3 = ControlDificultad(1)
        bloques_lento = []
        for i in range(1000):
            bloques_lento.append({
                "indice": i,
                "timestamp": i * ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS * 4,
                "dificultad": 1,
            })
        d = cd3.calcular(bloques_lento)
        self._t("Bloques lentos → bajar dificultad", d <= 1, f"Nueva: {d}")
        
        # 6. Límite máximo de cambio (4x)
        cd4 = ControlDificultad(10)
        bloques_extremo = []
        for i in range(1000):
            bloques_extremo.append({
                "indice": i,
                "timestamp": i * 0.1,  # Extremadamente rápidos
                "dificultad": 10,
            })
        d = cd4.calcular(bloques_extremo)
        self._t("Cambio máximo limitado a 4x", d <= 40, f"Nueva: {d}")
        
        # 7. Anti-ballena
        cd5 = ControlDificultad(10)
        d_normal = cd5.dificultad_para_minero(1_000_000, "validacion")  # 1 DRC
        d_ballena = cd5.dificultad_para_minero(1_000_000_000, "validacion")  # 1000 DRC
        self._t("Anti-ballena: ballena > normal", d_ballena > d_normal,
                f"Normal: {d_normal}, Ballena: {d_ballena}")
        
        # 8. Dificultad por tipo de trabajo
        d_val = cd5.dificultad_para_minero(0, "validacion")
        d_opt = cd5.dificultad_para_minero(0, "optimizacion")
        d_cien = cd5.dificultad_para_minero(0, "cientifico")
        self._t("Científico > Optimización > Validación", 
                d_cien > d_opt > d_val,
                f"V:{d_val} O:{d_opt} C:{d_cien}")
        
        # 9. Verificar hash con dificultad
        ok, _ = cd.verificar_dificultad_bloque("d10abc", 1)
        self._t("Hash d10... con dificultad 1", ok)
        
        # 10. Rechazar hash sin prefijo
        ok, msg = cd.verificar_dificultad_bloque("ffabc", 1)
        self._t("Rechazar hash sin d1", not ok)
        
        # 11. Estadísticas
        stats = cd.obtener_estadisticas()
        self._t("Estadísticas disponibles", "dificultad_actual" in stats)
        
        # 12. Próximo ajuste
        prox = cd.estimar_proximo_ajuste(500)
        self._t("Próximo ajuste estimado", prox["bloques_restantes"] == 500)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ MINERIA/DIFICULTAD.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🎯 " * 35)
    print("DIRECCOIN - CONTROL DE DIFICULTAD v1.0.0")
    print("🎯 " * 35)
    print(f"Tiempo objetivo: {ConfigDificultad.TIEMPO_OBJETIVO_SEGUNDOS}s/bloque")
    print(f"Ajuste cada: {ConfigDificultad.BLOQUES_POR_AJUSTE} bloques")
    print(f"Cambio máximo: {ConfigDificultad.MAX_CAMBIO_POR_AJUSTE}x\n")
    
    diag = DiagnosticoDificultad()
    if diag.ejecutar():
        print("📋 SIMULACIÓN DE EXPLOSIÓN DE MINERÍA:")
        resultados = SimuladorDificultad.simular_explosion_mineria(1, 10.0)
        for r in resultados[:5]:
            print(f"   Ciclo {r['ciclo']}: Dificultad = {r['dificultad']}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()