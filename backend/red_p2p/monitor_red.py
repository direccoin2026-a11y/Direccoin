#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - MONITOR DE RED                               ║
║                    Versión: 1.0.2 | Archivo: red_p2p/monitor_red.py        ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE TELEMETRÍA Y MONITOREO DE RED PARA DIRECCOIN.
"""

import time
import json
import os
import random
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import deque

class ConfigMonitor:
    VERSION = "1.0.2"
    INTERVALO_METRICAS = 10
    INTERVALO_ALERTAS = 30
    MAX_HISTORIAL_METRICAS = 1000
    MAX_EVENTOS = 500
    LATENCIA_CRITICA_MS = 1000
    LATENCIA_ALTA_MS = 500
    PAQUETES_PERDIDOS_CRITICO = 0.20
    PAQUETES_PERDIDOS_ALTO = 0.10
    NODOS_MINIMO_OPERATIVO = 3
    ARCHIVO_METRICAS = "metricas_red.json"


@dataclass
class MetricaNodo:
    id_nodo: str
    latencia_ms: float
    paquetes_enviados: int = 0
    paquetes_recibidos: int = 0
    paquetes_perdidos: int = 0
    bloques_validados: int = 0
    transacciones_procesadas: int = 0
    timestamp: float = field(default_factory=time.time)
    activo: bool = True


@dataclass
class MetricaRed:
    timestamp: float
    nodos_activos: int = 0
    nodos_totales: int = 0
    latencia_promedio_ms: float = 0
    latencia_maxima_ms: float = 0
    transacciones_por_segundo: float = 0
    bloques_por_minuto: float = 0
    paquetes_perdidos_porcentaje: float = 0
    salud_general: float = 0


@dataclass
class EventoRed:
    timestamp: float
    tipo: str
    severidad: str
    mensaje: str
    datos: Dict[str, Any] = field(default_factory=dict)


class MonitorRed:
    
    def __init__(self):
        self.metricas_nodos: Dict[str, MetricaNodo] = {}
        self.historial_metricas: deque = deque(maxlen=ConfigMonitor.MAX_HISTORIAL_METRICAS)
        self.eventos: deque = deque(maxlen=ConfigMonitor.MAX_EVENTOS)
        self.ultimo_monitoreo = 0
    
    def actualizar_metrica_nodo(self, id_nodo: str, latencia_ms: float,
                                paquetes_enviados: int = 0,
                                paquetes_recibidos: int = 0,
                                paquetes_perdidos: int = 0,
                                bloques_validados: int = 0,
                                transacciones_procesadas: int = 0,
                                activo: bool = True):
        metrica = MetricaNodo(
            id_nodo=id_nodo,
            latencia_ms=latencia_ms,
            paquetes_enviados=paquetes_enviados,
            paquetes_recibidos=paquetes_recibidos,
            paquetes_perdidos=paquetes_perdidos,
            bloques_validados=bloques_validados,
            transacciones_procesadas=transacciones_procesadas,
            activo=activo,
        )
        self.metricas_nodos[id_nodo] = metrica
    
    def nodo_desconectado(self, id_nodo: str):
        if id_nodo in self.metricas_nodos:
            self.metricas_nodos[id_nodo].activo = False
        self._registrar_evento("desconexion", "warning", f"Nodo {id_nodo[:12]}... desconectado")
    
    def nodo_conectado(self, id_nodo: str):
        self._registrar_evento("conexion", "info", f"Nodo {id_nodo[:12]}... conectado")
    
    def detectar_ataque(self, tipo: str, evidencia: Dict = None):
        self._registrar_evento("ataque", "critical", f"Posible ataque {tipo}", evidencia or {})
    
    def _registrar_evento(self, tipo: str, severidad: str, mensaje: str, datos: Dict = None):
        self.eventos.append(EventoRed(
            timestamp=time.time(), tipo=tipo, severidad=severidad,
            mensaje=mensaje, datos=datos or {}
        ))
    
    def obtener_metricas_red(self) -> MetricaRed:
        activos = [m for m in self.metricas_nodos.values() if m.activo]
        total = len(self.metricas_nodos)
        
        if not activos:
            return MetricaRed(timestamp=time.time(), nodos_totales=total)
        
        latencias = [m.latencia_ms for m in activos]
        latencia_promedio = sum(latencias) / len(latencias)
        
        total_perdidos = sum(m.paquetes_perdidos for m in activos)
        total_enviados = sum(m.paquetes_enviados for m in activos)
        total_paquetes = total_enviados + total_perdidos
        perdida = total_perdidos / max(total_paquetes, 1)
        
        salud = self._calcular_salud(len(activos), latencia_promedio, perdida, total)
        
        metrica = MetricaRed(
            timestamp=time.time(),
            nodos_activos=len(activos),
            nodos_totales=total,
            latencia_promedio_ms=round(latencia_promedio, 2),
            latencia_maxima_ms=round(max(latencias), 2),
            paquetes_perdidos_porcentaje=round(perdida * 100, 2),
            salud_general=round(salud, 4),
        )
        self.historial_metricas.append(metrica)
        return metrica
    
    def _calcular_salud(self, n_activos: int, latencia: float, perdida: float, total: int) -> float:
        score = 1.0
        if total < ConfigMonitor.NODOS_MINIMO_OPERATIVO: score -= 0.3
        if latencia > ConfigMonitor.LATENCIA_CRITICA_MS: score -= 0.4
        elif latencia > ConfigMonitor.LATENCIA_ALTA_MS: score -= 0.2
        if perdida > ConfigMonitor.PAQUETES_PERDIDOS_CRITICO: score -= 0.4
        elif perdida > ConfigMonitor.PAQUETES_PERDIDOS_ALTO: score -= 0.2
        if n_activos > 10: score += 0.1
        return max(0.0, min(1.0, score))
    
    def verificar_alertas(self) -> List[Dict]:
        alertas = []
        metrica = self.obtener_metricas_red()
        if metrica.nodos_activos < ConfigMonitor.NODOS_MINIMO_OPERATIVO:
            alertas.append({"tipo": "nodos", "severidad": "critical", "msg": f"{metrica.nodos_activos} nodos"})
        if metrica.latencia_promedio_ms > ConfigMonitor.LATENCIA_CRITICA_MS:
            alertas.append({"tipo": "latencia", "severidad": "critical", "msg": f"{metrica.latencia_promedio_ms}ms"})
        if metrica.salud_general < 0.3:
            alertas.append({"tipo": "salud", "severidad": "critical", "msg": f"{metrica.salud_general:.1%}"})
        return alertas
    
    def exportar_para_ia(self) -> Dict:
        m = self.obtener_metricas_red()
        return {"nodos": m.nodos_activos, "latencia": m.latencia_promedio_ms, "salud": m.salud_general}


class DiagnosticoMonitor:
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
        print("🔍 DIAGNÓSTICO DE RED_P2P/MONITOR_RED.PY")
        print("=" * 70)
        
        monitor = MonitorRed()
        
        for i in range(10):
            monitor.actualizar_metrica_nodo(f"nodo_{i}", random.randint(10, 300),
                                            paquetes_enviados=random.randint(100, 1000),
                                            paquetes_recibidos=random.randint(100, 1000),
                                            paquetes_perdidos=random.randint(0, 10))
        self._t("Métricas 10 nodos", len(monitor.metricas_nodos) == 10)
        
        metrica = monitor.obtener_metricas_red()
        self._t("Métricas de red", metrica.nodos_activos == 10)
        self._t("Salud calculada", 0 <= metrica.salud_general <= 1)
        
        monitor.nodo_conectado("nuevo_nodo")
        self._t("Eventos registrados", len(monitor.eventos) >= 1)
        
        monitor.detectar_ataque("spam", {"txs": 1000})
        self._t("Ataque detectado", any(e.tipo == "ataque" for e in monitor.eventos))
        
        alertas = monitor.verificar_alertas()
        self._t("Sistema alertas", isinstance(alertas, list))
        
        datos_ia = monitor.exportar_para_ia()
        self._t("Exportar IA", "salud" in datos_ia)
        
        # Desconectar nodo_0 (existe en métricas)
        monitor.nodo_desconectado("nodo_0")
        metrica2 = monitor.obtener_metricas_red()
        self._t("Desconexión detectada", metrica2.nodos_activos == 9)
        
        if os.path.exists(ConfigMonitor.ARCHIVO_METRICAS):
            os.remove(ConfigMonitor.ARCHIVO_METRICAS)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ MONITOR_RED OK\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "📊 " * 35)
    print("DIRECCOIN - MONITOR DE RED v1.0.2")
    print("📊 " * 35)
    diag = DiagnosticoMonitor()
    if diag.ejecutar():
        print("📋 DEMO:")
        m = MonitorRed()
        for i in range(15):
            m.actualizar_metrica_nodo(f"n_{i}", random.randint(5, 200),
                                      paquetes_enviados=random.randint(500, 5000),
                                      paquetes_recibidos=random.randint(500, 5000))
        met = m.obtener_metricas_red()
        print(f"   Nodos: {met.nodos_activos}/{met.nodos_totales} | Lat: {met.latencia_promedio_ms}ms | Salud: {met.salud_general:.1%}")
        if os.path.exists(ConfigMonitor.ARCHIVO_METRICAS): os.remove(ConfigMonitor.ARCHIVO_METRICAS)
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()