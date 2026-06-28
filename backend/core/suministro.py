#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - CONTROL DE SUMINISTRO                        ║
║                    Versión: 1.0.3 | Archivo: core/suministro.py            ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE CONTROL DE EMISIÓN MONETARIA PARA DIRECCOIN.

Controla:
  • Suministro total: 100,000,000 DRC
  • Premine: 3,000,000 DRC (3%)
  • Minado: 97,000,000 DRC (97%)
  • Curva de emisión: reducción 10% anual
  • Recompensa por bloque: 100 DRC inicial
  • Verificación de suministro máximo
  • Función de quema de tokens
"""

import math
import time
from typing import Tuple, Optional, List, Dict

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigSuministro:
    VERSION = "1.0.3"
    
    SUMINISTRO_TOTAL = 100_000_000
    PREMINE_TOTAL = 3_000_000
    PREMINE_LIQUIDO = 1_000_000
    PREMINE_BLOQUEADO = 2_000_000
    
    TOTAL_MINABLE = 97_000_000
    RECOMPENSA_INICIAL_POR_BLOQUE = 100_000_000
    BLOQUES_POR_AÑO = 97_000
    
    REDUCCION_ANUAL = 0.90
    DIAS_POR_PERIODO = 365
    
    TIMESTAMP_GENESIS = 1778279888
    
    DECIMALES = 6
    UNIDAD_MINIMA = "Direc"
    SIMBOLO = "DRC"
    
    DIRECCION_QUEMADO_BYTES = b'\x00' * 20


# ==============================================================================
# CONTROL DE SUMINISTRO
# ==============================================================================

class ControlSuministro:
    
    def __init__(self, timestamp_genesis: Optional[int] = None):
        self.timestamp_genesis = timestamp_genesis or ConfigSuministro.TIMESTAMP_GENESIS
        self.total_quemado = 0
    
    def calcular_año_actual(self, numero_bloque: int) -> int:
        if numero_bloque <= 0:
            return 0
        return math.ceil(numero_bloque / ConfigSuministro.BLOQUES_POR_AÑO)
    
    def calcular_recompensa_bloque(self, numero_bloque: int) -> int:
        if numero_bloque <= 0:
            return 0
        
        año = self.calcular_año_actual(numero_bloque)
        if año <= 0:
            return 0
        
        recompensa = ConfigSuministro.RECOMPENSA_INICIAL_POR_BLOQUE
        for _ in range(1, año):
            recompensa = int(recompensa * ConfigSuministro.REDUCCION_ANUAL)
        
        return max(1, recompensa)
    
    def calcular_recompensa_anual(self, año: int) -> int:
        if año <= 0:
            return 0
        
        bloques = ConfigSuministro.BLOQUES_POR_AÑO
        recompensa = ConfigSuministro.RECOMPENSA_INICIAL_POR_BLOQUE
        
        for _ in range(1, año):
            recompensa = int(recompensa * ConfigSuministro.REDUCCION_ANUAL)
        
        return bloques * recompensa
    
    def calcular_emitido_total(self, numero_bloque: int) -> int:
        factor = 10 ** ConfigSuministro.DECIMALES
        if numero_bloque <= 0:
            return ConfigSuministro.PREMINE_TOTAL * factor
        
        año_actual = self.calcular_año_actual(numero_bloque)
        total = ConfigSuministro.PREMINE_TOTAL * factor
        
        for año in range(1, año_actual):
            total += self.calcular_recompensa_anual(año)
        
        bloques_año_anterior = (año_actual - 1) * ConfigSuministro.BLOQUES_POR_AÑO
        bloques_este_año = numero_bloque - bloques_año_anterior
        recompensa_actual = self.calcular_recompensa_bloque(numero_bloque)
        total += bloques_este_año * recompensa_actual
        
        maximo = ConfigSuministro.SUMINISTRO_TOTAL * factor
        return min(total, maximo)
    
    def calcular_restante_minable(self, numero_bloque: int) -> int:
        emitido = self.calcular_emitido_total(numero_bloque)
        factor = 10 ** ConfigSuministro.DECIMALES
        maximo = ConfigSuministro.SUMINISTRO_TOTAL * factor
        restante = maximo - emitido - self.total_quemado
        return max(0, restante)
    
    def verificar_limite_suministro(self, cantidad_propuesta: int,
                                    numero_bloque: int) -> bool:
        emitido = self.calcular_emitido_total(numero_bloque)
        factor = 10 ** ConfigSuministro.DECIMALES
        maximo = ConfigSuministro.SUMINISTRO_TOTAL * factor
        return (emitido + cantidad_propuesta) <= maximo
    
    def quemar_tokens(self, cantidad: int) -> Tuple[bool, str]:
        if cantidad <= 0:
            return False, "Cantidad debe ser positiva"
        self.total_quemado += cantidad
        factor = 10 ** ConfigSuministro.DECIMALES
        maximo = ConfigSuministro.SUMINISTRO_TOTAL * factor
        if self.total_quemado > maximo:
            self.total_quemado = maximo
        return True, f"Quemados {self.formatear_drc(cantidad)}"
    
    def obtener_estadisticas(self, numero_bloque: int) -> dict:
        año = self.calcular_año_actual(numero_bloque)
        emitido = self.calcular_emitido_total(numero_bloque)
        restante = self.calcular_restante_minable(numero_bloque)
        recompensa = self.calcular_recompensa_bloque(numero_bloque)
        factor = 10 ** ConfigSuministro.DECIMALES
        maximo = ConfigSuministro.SUMINISTRO_TOTAL * factor
        
        return {
            "bloque_actual": numero_bloque,
            "año_emision": año,
            "recompensa_bloque_drc": recompensa,
            "recompensa_bloque_formateada": self.formatear_drc(recompensa),
            "emitido_total_direcs": emitido,
            "emitido_total_formateado": self.formatear_drc(emitido),
            "emitido_porcentaje": round((emitido / maximo) * 100, 6),
            "restante_minable_direcs": restante,
            "restante_minable_formateado": self.formatear_drc(restante),
            "total_quemado_direcs": self.total_quemado,
            "total_quemado_formateado": self.formatear_drc(self.total_quemado),
            "suministro_maximo_drc": ConfigSuministro.SUMINISTRO_TOTAL,
        }
    
    @staticmethod
    def formatear_drc(cantidad: int) -> str:
        signo = ""
        if cantidad < 0:
            signo = "-"
            cantidad = abs(cantidad)
        factor = 10 ** ConfigSuministro.DECIMALES
        entero = cantidad // factor
        decimal = cantidad % factor
        return f"{signo}{entero}.{decimal:0{ConfigSuministro.DECIMALES}d} {ConfigSuministro.SIMBOLO}"
    
    @staticmethod
    def drc_a_direcs(drc: float) -> int:
        return int(drc * (10 ** ConfigSuministro.DECIMALES))
    
    @staticmethod
    def direcs_a_drc(direcs: int) -> float:
        return direcs / (10 ** ConfigSuministro.DECIMALES)


# ==============================================================================
# PROYECCIÓN
# ==============================================================================

class ProyeccionSuministro:
    
    @staticmethod
    def proyectar_emision(años: int = 25) -> List[Dict]:
        cs = ControlSuministro()
        proyeccion = []
        factor = 10 ** ConfigSuministro.DECIMALES
        acumulado = ConfigSuministro.PREMINE_TOTAL * factor
        maximo = ConfigSuministro.SUMINISTRO_TOTAL * factor
        
        for año in range(1, años + 1):
            recompensa = ConfigSuministro.RECOMPENSA_INICIAL_POR_BLOQUE
            for _ in range(1, año):
                recompensa = int(recompensa * ConfigSuministro.REDUCCION_ANUAL)
            recompensa = max(1, recompensa)
            
            emision_anual = ConfigSuministro.BLOQUES_POR_AÑO * recompensa
            emision_anual = min(emision_anual, maximo - acumulado)
            acumulado += emision_anual
            
            proyeccion.append({
                "año": año,
                "recompensa_por_bloque_direcs": recompensa,
                "recompensa_por_bloque_formateada": cs.formatear_drc(recompensa),
                "emision_anual_direcs": emision_anual,
                "emision_anual_formateada": cs.formatear_drc(emision_anual),
                "acumulado_direcs": acumulado,
                "acumulado_formateado": cs.formatear_drc(acumulado),
                "porcentaje_total": round((acumulado / maximo) * 100, 2)
            })
            
            if acumulado >= maximo:
                break
        
        return proyeccion
    
    @staticmethod
    def imprimir_proyeccion(años: int = 25):
        proyeccion = ProyeccionSuministro.proyectar_emision(años)
        
        print(f"\n📊 PROYECCIÓN DE EMISIÓN DIRECCOIN")
        print("=" * 95)
        print(f"{'Año':<6} {'Recompensa':<18} {'Emisión Anual':<22} {'Acumulado':<24} {'%':<8}")
        print("─" * 95)
        
        for p in proyeccion:
            print(f"{p['año']:<6} {p['recompensa_por_bloque_formateada']:<18} "
                  f"{p['emision_anual_formateada']:<22} {p['acumulado_formateado']:<24} "
                  f"{p['porcentaje_total']}%")
        
        print("─" * 95)


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoSuministro:
    def __init__(self):
        self.ok = 0
        self.fail = 0
    
    def _t(self, n, ok, d=""):
        s = "✅ PASÓ" if ok else "❌ FALLÓ"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE CORE/SUMINISTRO.PY")
        print("=" * 70)
        
        cs = ControlSuministro()
        factor = 10 ** ConfigSuministro.DECIMALES
        
        self._t("Premine = 3M DRC", ConfigSuministro.PREMINE_TOTAL == 3_000_000)
        self._t("Suministro = 100M DRC", ConfigSuministro.SUMINISTRO_TOTAL == 100_000_000)
        self._t("Minable = 97M DRC", ConfigSuministro.TOTAL_MINABLE == 97_000_000)
        
        r0 = cs.calcular_recompensa_bloque(0)
        self._t("Bloque 0: recompensa 0", r0 == 0)
        
        r1 = cs.calcular_recompensa_bloque(1)
        self._t("Bloque 1: 100 DRC", r1 == 100_000_000, cs.formatear_drc(r1))
        
        bloque_a2 = ConfigSuministro.BLOQUES_POR_AÑO + 1
        r2 = cs.calcular_recompensa_bloque(bloque_a2)
        self._t("Año 2: recompensa 90 DRC", r2 == 90_000_000, cs.formatear_drc(r2))
        
        e0 = cs.calcular_emitido_total(0)
        self._t("Emitido bloque 0 = 3M DRC", e0 == 3_000_000 * factor, cs.formatear_drc(e0))
        
        e1 = cs.calcular_emitido_total(1)
        esperado = 3_000_000 * factor + 100_000_000
        self._t("Emitido bloque 1 correcto", e1 == esperado, cs.formatear_drc(e1))
        
        self._t("Límite suministro OK", cs.verificar_limite_suministro(100_000_000, 1))
        
        ok_q, _ = cs.quemar_tokens(500_000 * factor)
        self._t("Quemar tokens", ok_q)
        
        self._t("Formatear 12.345678", cs.formatear_drc(12_345_678) == "12.345678 DRC")
        self._t("Formatear 100 DRC", cs.formatear_drc(100_000_000) == "100.000000 DRC")
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0:
            print("✅ CORE/SUMINISTRO.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "💰 " * 35)
    print("DIRECCOIN - CONTROL DE SUMINISTRO v1.0.3")
    print("💰 " * 35)
    print(f"Suministro: {ConfigSuministro.SUMINISTRO_TOTAL:,} DRC")
    print(f"Premine: {ConfigSuministro.PREMINE_TOTAL:,} DRC (3%)")
    print(f"Minable: {ConfigSuministro.TOTAL_MINABLE:,} DRC (97%)")
    print(f"Recompensa: {ConfigSuministro.RECOMPENSA_INICIAL_POR_BLOQUE // 1_000_000} DRC/bloque")
    print(f"Bloques/año: {ConfigSuministro.BLOQUES_POR_AÑO:,}\n")
    
    diag = DiagnosticoSuministro()
    if diag.ejecutar():
        ProyeccionSuministro.imprimir_proyeccion(20)
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()