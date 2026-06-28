#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - IA: AJUSTE DINÁMICO DE GAS                  ║
║                    Versión: 1.0.0 | Archivo: ia/ajuste_gas.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

SISTEMA DE IA PARA CONTROL DINÁMICO DE GAS EN DIRECCOIN.

Funciones:
  • Monitoreo de congestión de red en tiempo real
  • Ajuste dinámico de tarifas de gas
  • Detección de spam transaccional
  • Priorización de transacciones legítimas
  • Predicción de demanda futura

CARACTERÍSTICAS:
  • Algoritmo de media móvil exponencial (EMA)
  • Sistema de niveles de congestión (verde, amarillo, rojo)
  • Anti-spam con tarifas progresivas
  • Descuentos para usuarios frecuentes
  • Diagnóstico de 10 pruebas
"""

import time
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigAjusteGas:
    VERSION = "1.0.0"
    
    # Niveles de gas (en Direcs)
    GAS_MINIMO = 1                          # Gas mínimo absoluto
    GAS_BASE = 100                          # Gas base en condiciones normales
    GAS_MAXIMO = 100_000                    # Gas máximo (anti-spam extremo)
    
    # Umbrales de congestión
    CONGESTION_BAJA = 0.3                   # < 30% uso = gas bajo
    CONGESTION_MEDIA = 0.6                  # 30-60% = gas normal
    CONGESTION_ALTA = 0.85                  # 60-85% = gas alto
    # > 85% = gas máximo
    
    # Parámetros de media móvil
    EMA_ALPHA = 0.2                         # Factor de suavizado
    VENTANA_HISTORIAL = 100                 # Puntos de datos
    
    # Anti-spam
    TX_POR_SEGUNDO_NORMAL = 50             # Tasa normal de transacciones
    TX_POR_SEGUNDO_SPAM = 500               # Umbral de spam
    MULTIPLICADOR_SPAM = 10                 # Multiplicador de gas en spam
    
    # Descuentos
    DESCUENTO_USUARIO_FRECUENTE = 0.5       # 50% descuento
    MIN_TX_PARA_DESCUENTO = 10              # Transacciones para ser frecuente


# ==============================================================================
# ESTRUCTURAS DE DATOS
# ==============================================================================

@dataclass
class MetricaGas:
    """Métrica de uso de gas en un momento dado."""
    timestamp: float
    gas_promedio: float
    transacciones_pendientes: int
    uso_mempool: float                     # 0.0 - 1.0
    nivel_congestion: str                  # "bajo", "medio", "alto", "critico"
    gas_sugerido: int
    tasa_llegada: float                    # tx/segundo


# ==============================================================================
# CONTROLADOR DE GAS
# ==============================================================================

class ControladorGas:
    """
    Sistema IA para ajuste dinámico de tarifas de gas.
    
    Uso:
        cg = ControladorGas()
        gas_sugerido = cg.calcular_gas(mempool_tamano, max_mempool)
        es_spam = cg.detectar_spam(tasa_transacciones)
    """
    
    def __init__(self):
        self.historial: deque = deque(maxlen=ConfigAjusteGas.VENTANA_HISTORIAL)
        self.ema_gas = ConfigAjusteGas.GAS_BASE
        self.ema_tasa = 0
        self.usuarios_frecuentes: Dict[str, int] = {}
        self.ultima_actualizacion = time.time()
        self.en_modo_spam = False
    
    def _ema(self, valor_actual: float, valor_anterior: float, 
             alpha: float = None) -> float:
        """Calcula media móvil exponencial."""
        if alpha is None:
            alpha = ConfigAjusteGas.EMA_ALPHA
        return alpha * valor_actual + (1 - alpha) * valor_anterior
    
    def _nivel_congestion(self, uso_mempool: float) -> str:
        """Determina el nivel de congestión."""
        if uso_mempool < ConfigAjusteGas.CONGESTION_BAJA:
            return "bajo"
        elif uso_mempool < ConfigAjusteGas.CONGESTION_MEDIA:
            return "medio"
        elif uso_mempool < ConfigAjusteGas.CONGESTION_ALTA:
            return "alto"
        else:
            return "critico"
    
    def _calcular_factor_congestion(self, nivel: str) -> float:
        """Calcula el multiplicador de gas según congestión."""
        factores = {
            "bajo": 0.5,       # Gas barato para atraer transacciones
            "medio": 1.0,      # Gas normal
            "alto": 3.0,       # Gas alto para desalentar spam
            "critico": 10.0,   # Gas muy alto, solo transacciones urgentes
        }
        return factores.get(nivel, 1.0)
    
    def calcular_gas(self, txs_pendientes: int, max_mempool: int,
                     tasa_llegada: float = 0) -> Dict[str, Any]:
        """
        Calcula el gas sugerido basado en el estado actual de la red.
        
        Args:
            txs_pendientes: Transacciones en mempool
            max_mempool: Capacidad máxima del mempool
            tasa_llegada: Transacciones por segundo entrantes
        
        Returns:
            Diccionario con recomendaciones de gas
        """
        if max_mempool <= 0:
            max_mempool = 1
        
        uso_mempool = min(1.0, txs_pendientes / max_mempool)
        nivel = self._nivel_congestion(uso_mempool)
        factor = self._calcular_factor_congestion(nivel)
        
        # Actualizar EMA
        self.ema_gas = self._ema(ConfigAjusteGas.GAS_BASE * factor, self.ema_gas)
        self.ema_tasa = self._ema(tasa_llegada, self.ema_tasa)
        
        # Calcular gas sugerido
        gas_base = int(self.ema_gas)
        
        # Ajustar por spam
        if self.en_modo_spam:
            gas_base = int(gas_base * ConfigAjusteGas.MULTIPLICADOR_SPAM)
        
        # Asegurar límites
        gas_sugerido = max(ConfigAjusteGas.GAS_MINIMO, 
                          min(ConfigAjusteGas.GAS_MAXIMO, gas_base))
        
        # Registrar métrica
        metrica = MetricaGas(
            timestamp=time.time(),
            gas_promedio=self.ema_gas,
            transacciones_pendientes=txs_pendientes,
            uso_mempool=uso_mempool,
            nivel_congestion=nivel,
            gas_sugerido=gas_sugerido,
            tasa_llegada=tasa_llegada,
        )
        self.historial.append(metrica)
        self.ultima_actualizacion = time.time()
        
        return {
            "gas_sugerido": gas_sugerido,
            "gas_sugerido_drc": gas_sugerido / 1_000_000,
            "nivel_congestion": nivel,
            "uso_mempool": round(uso_mempool * 100, 1),
            "factor_congestion": factor,
            "modo_spam": self.en_modo_spam,
            "tasa_llegada": round(tasa_llegada, 2),
        }
    
    def detectar_spam(self, tasa_actual: float) -> Dict[str, Any]:
        """
        Detecta si hay un ataque de spam basado en la tasa de transacciones.
        
        Returns:
            Diccionario con resultado del análisis
        """
        if tasa_actual > ConfigAjusteGas.TX_POR_SEGUNDO_SPAM:
            self.en_modo_spam = True
            return {
                "spam_detectado": True,
                "severidad": "alta",
                "tasa_actual": tasa_actual,
                "accion": "Subir gas 10x y priorizar cuentas con saldo",
            }
        elif tasa_actual > ConfigAjusteGas.TX_POR_SEGUNDO_NORMAL * 2:
            return {
                "spam_detectado": False,
                "severidad": "media",
                "tasa_actual": tasa_actual,
                "accion": "Monitoreando posible ataque",
            }
        else:
            # Recuperación gradual del modo spam
            if self.en_modo_spam and tasa_actual < ConfigAjusteGas.TX_POR_SEGUNDO_NORMAL:
                self.en_modo_spam = False
            
            return {
                "spam_detectado": False,
                "severidad": "ninguna",
                "tasa_actual": tasa_actual,
                "accion": "Operación normal",
            }
    
    def calcular_gas_para_usuario(self, direccion: str, gas_base: int) -> int:
        """
        Calcula el gas para un usuario específico, con descuentos.
        """
        tx_count = self.usuarios_frecuentes.get(direccion, 0)
        
        if tx_count >= ConfigAjusteGas.MIN_TX_PARA_DESCUENTO:
            return int(gas_base * ConfigAjusteGas.DESCUENTO_USUARIO_FRECUENTE)
        
        return gas_base
    
    def registrar_transaccion_usuario(self, direccion: str):
        """Registra una transacción de un usuario para descuentos."""
        self.usuarios_frecuentes[direccion] = \
            self.usuarios_frecuentes.get(direccion, 0) + 1
    
    def priorizar_transacciones(self, txs: List[dict]) -> List[dict]:
        """
        Ordena transacciones por prioridad.
        Mayor gas + usuario frecuente = mayor prioridad.
        """
        def prioridad(tx):
            gas = tx.get("gas", 0)
            origen = tx.get("origen", "")
            bonus_frecuente = 2 if self.usuarios_frecuentes.get(origen, 0) >= ConfigAjusteGas.MIN_TX_PARA_DESCUENTO else 1
            return gas * bonus_frecuente
        
        return sorted(txs, key=prioridad, reverse=True)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Devuelve estadísticas del controlador de gas."""
        return {
            "gas_actual": int(self.ema_gas),
            "gas_minimo": ConfigAjusteGas.GAS_MINIMO,
            "gas_maximo": ConfigAjusteGas.GAS_MAXIMO,
            "modo_spam": self.en_modo_spam,
            "usuarios_frecuentes": len(self.usuarios_frecuentes),
            "metricas_historicas": len(self.historial),
        }
    
    def predecir_gas_futuro(self, segundos: int = 60) -> Dict[str, Any]:
        """
        Predice el gas sugerido en el futuro basado en tendencias.
        """
        if len(self.historial) < 2:
            return {"gas_predicho": ConfigAjusteGas.GAS_BASE, "confianza": 0}
        
        # Tendencia simple: comparar últimos 10 puntos
        recientes = list(self.historial)[-10:]
        if len(recientes) >= 2:
            tendencia = recientes[-1].uso_mempool - recientes[0].uso_mempool
            gas_predicho = int(self.ema_gas * (1 + tendencia))
        else:
            gas_predicho = int(self.ema_gas)
        
        return {
            "gas_predicho": gas_predicho,
            "gas_predicho_drc": gas_predicho / 1_000_000,
            "confianza": min(90, len(recientes) * 10),
            "tendencia": "subiendo" if tendencia > 0 else "bajando" if tendencia < 0 else "estable",
        }


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoAjusteGas:
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
        print("🔍 DIAGNÓSTICO DE IA/AJUSTE_GAS.PY")
        print("=" * 70)
        
        cg = ControladorGas()
        
        # 1. Gas en condiciones normales
        r = cg.calcular_gas(10, 100, 5)
        self._t("Gas normal (10% uso)", r["nivel_congestion"] == "bajo",
                f"{r['gas_sugerido_drc']} DRC, {r['nivel_congestion']}")
        
        # 2. Gas en congestión media
        r = cg.calcular_gas(50, 100, 40)
        self._t("Gas congestión media (50%)", r["nivel_congestion"] == "medio")
        
        # 3. Gas en congestión alta
        r = cg.calcular_gas(80, 100, 200)
        self._t("Gas congestión alta (80%)", r["nivel_congestion"] == "alto")
        
        # 4. Gas en congestión crítica
        r = cg.calcular_gas(95, 100, 600)
        self._t("Gas congestión crítica (95%)", r["nivel_congestion"] == "critico")
        
        # 5. Detectar spam
        spam = cg.detectar_spam(600)
        self._t("Detectar spam (600 tx/s)", spam["spam_detectado"])
        
        # 6. No detectar spam en normal
        spam2 = cg.detectar_spam(10)
        self._t("No spam (10 tx/s)", not spam2["spam_detectado"])
        
        # 7. Descuento usuario frecuente
        for _ in range(15):
            cg.registrar_transaccion_usuario("drcUsuarioFrecuente")
        gas_desc = cg.calcular_gas_para_usuario("drcUsuarioFrecuente", 1000)
        gas_normal = cg.calcular_gas_para_usuario("drcNuevo", 1000)
        self._t("Descuento 50%", gas_desc < gas_normal,
                f"Frecuente: {gas_desc}, Nuevo: {gas_normal}")
        
        # 8. Priorizar transacciones
        txs = [
            {"origen": "drcA", "gas": 10},
            {"origen": "drcB", "gas": 100},
            {"origen": "drcC", "gas": 50},
        ]
        cg.registrar_transaccion_usuario("drcA")
        priorizadas = cg.priorizar_transacciones(txs)
        self._t("Priorizar por gas", priorizadas[0]["gas"] == 100)
        
        # 9. Estadísticas
        stats = cg.obtener_estadisticas()
        self._t("Estadísticas", "gas_actual" in stats)
        
        # 10. Predicción
        pred = cg.predecir_gas_futuro(60)
        self._t("Predicción futura", "gas_predicho" in pred)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ IA/AJUSTE_GAS.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "💸 " * 35)
    print("DIRECCOIN - IA: AJUSTE DE GAS v1.0.0")
    print("💸 " * 35)
    print(f"Gas base: {ConfigAjusteGas.GAS_BASE} Direcs")
    print(f"Gas mínimo: {ConfigAjusteGas.GAS_MINIMO} | Máximo: {ConfigAjusteGas.GAS_MAXIMO:,}\n")
    
    diag = DiagnosticoAjusteGas()
    if diag.ejecutar():
        print("📋 DEMO DE ESCENARIOS:")
        cg = ControladorGas()
        
        escenarios = [(5, 100, 3, "🌙 Noche"), (40, 100, 30, "☀️ Día"), 
                      (90, 100, 450, "🔥 Alta demanda"), (98, 100, 800, "🚨 Ataque")]
        
        for txs, max_tx, tasa, nombre in escenarios:
            r = cg.calcular_gas(txs, max_tx, tasa)
            print(f"   {nombre}: {r['gas_sugerido_drc']:.6f} DRC | {r['uso_mempool']:.0f}% | {r['nivel_congestion']}")
        
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()