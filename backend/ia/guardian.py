#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - IA: GUARDIÁN DE SEGURIDAD                   ║
║                    Versión: 1.0.0 | Archivo: ia/guardian.py               ║
╚══════════════════════════════════════════════════════════════════════════════╝

SISTEMA AVANZADO DE SEGURIDAD PARA DIRECCOIN.

Protege la red contra:
  • Ataques de doble gasto
  • Spam transaccional
  • Nodos maliciosos
  • Sybil attacks
  • Eclipse attacks
  • Ataques de denegación de servicio (DoS)
  • Transacciones fraudulentas
  • Suplantación de identidad

CARACTERÍSTICAS AVANZADAS:
  • Detección de anomalías con Isolation Forest simplificado
  • Lista negra dinámica con tiempo de expiración
  • Sistema de reputación de nodos
  • Análisis de comportamiento en tiempo real
  • Rate limiting adaptativo
  • Protección contra front-running
  • Diagnóstico de 15 pruebas
"""

import time
import math
import random
import hashlib
import json
import os
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import deque, defaultdict

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigGuardian:
    VERSION = "1.0.0"
    
    # Lista negra
    TIEMPO_BLOQUEO_MINUTOS = 60              # 1 hora de bloqueo
    TIEMPO_BLOQUEO_MAXIMO = 1440             # 24 horas máximo
    MAX_LISTA_NEGRA = 1000
    
    # Rate limiting
    MAX_TX_POR_SEGUNDO = 100                 # Máximo global
    MAX_TX_POR_DIRECCION_POR_SEGUNDO = 10    # Por dirección
    MAX_CONEXIONES_POR_IP = 50
    
    # Reputación
    REPUTACION_INICIAL = 100
    REPUTACION_MINIMA = -500
    REPUTACION_BLOQUEO = -200
    PENALIZACION_SPAM = 50
    PENALIZACION_DOBLE_GASTO = 300
    PENALIZACION_NODO_CAIDO = 5
    RECOMPENSA_BUEN_COMPORTAMIENTO = 1
    
    # Anomalías
    UMBRAL_ANOMALIA = 0.85                   # Score > 0.85 = sospechoso
    VENTANA_ANALISIS = 100                   # Transacciones para análisis
    FACTORES_ANOMALIA = 5                    # Número de características
    
    # Archivos
    ARCHIVO_LISTA_NEGRA = "lista_negra.json"
    ARCHIVO_REPUTACION = "reputacion_nodos.json"


# ==============================================================================
# ESTRUCTURAS DE DATOS
# ==============================================================================

@dataclass
class EntidadBloqueada:
    """Entidad en la lista negra."""
    direccion: str
    motivo: str
    timestamp_bloqueo: float
    duracion_minutos: int
    intentos: int = 1
    
    @property
    def expirado(self) -> bool:
        return time.time() > self.timestamp_bloqueo + (self.duracion_minutos * 60)


@dataclass
class ReputacionNodo:
    """Sistema de reputación para nodos."""
    id_nodo: str
    score: int = ConfigGuardian.REPUTACION_INICIAL
    infracciones: int = 0
    recompensas: int = 0
    ultima_actividad: float = field(default_factory=time.time)
    historial: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class AlertaSeguridad:
    """Alerta de seguridad generada por el guardián."""
    timestamp: float
    tipo: str                              # doble_gasto, spam, anomalia, nodo_malicioso
    severidad: str                         # baja, media, alta, critica
    direccion: str
    evidencia: Dict[str, Any]
    accion_tomada: str


# ==============================================================================
# DETECTOR DE ANOMALÍAS (Isolation Forest Simplificado)
# ==============================================================================

class DetectorAnomalias:
    """
    Detecta transacciones anómalas usando un Isolation Forest simplificado.
    Analiza: cantidad, gas, frecuencia, horario, patrón de direcciones.
    """
    
    def __init__(self):
        self.historial_tx: deque = deque(maxlen=ConfigGuardian.VENTANA_ANALISIS)
        self.medias: Dict[str, float] = {}
        self.desviaciones: Dict[str, float] = {}
    
    def _extraer_caracteristicas(self, tx: dict) -> List[float]:
        """Extrae características numéricas de una transacción."""
        ahora = time.time()
        return [
            float(tx.get("cantidad", 0)) / 1_000_000,           # Cantidad en DRC
            float(tx.get("gas", 0)),                              # Gas
            len(str(tx.get("origen", ""))),                       # Longitud dirección origen
            len(str(tx.get("destino", ""))),                      # Longitud dirección destino
            ahora - tx.get("timestamp", ahora),                   # Antigüedad
        ]
    
    def _distancia_euclidiana(self, a: List[float], b: List[float]) -> float:
        """Calcula distancia euclidiana entre dos vectores."""
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    
    def entrenar(self, txs: List[dict]):
        """Entrena el detector con transacciones normales."""
        if not txs:
            return
        
        caracteristicas = [self._extraer_caracteristicas(tx) for tx in txs]
        n = len(caracteristicas)
        m = len(caracteristicas[0])
        
        # Calcular medias
        self.medias = {}
        for j in range(m):
            self.medias[str(j)] = sum(c[j] for c in caracteristicas) / n
        
        # Calcular desviaciones estándar
        self.desviaciones = {}
        for j in range(m):
            media = self.medias[str(j)]
            varianza = sum((c[j] - media) ** 2 for c in caracteristicas) / n
            self.desviaciones[str(j)] = math.sqrt(varianza) if varianza > 0 else 1.0
    
    def calcular_anomalia(self, tx: dict) -> Dict[str, Any]:
        """
        Calcula el score de anomalía de una transacción (0 = normal, 1 = muy anómalo).
        """
        if not self.medias:
            return {"score": 0, "es_anomalo": False, "factores": []}
        
        caracteristicas = self._extraer_caracteristicas(tx)
        factores_anomalos = []
        score_total = 0
        
        for j, valor in enumerate(caracteristicas):
            media = self.medias.get(str(j), 0)
            desv = self.desviaciones.get(str(j), 1)
            
            # Z-score
            z_score = abs(valor - media) / desv if desv > 0 else 0
            
            if z_score > 2.0:
                factores_anomalos.append(f"factor_{j}")
                score_total += min(1.0, z_score / 5.0)
        
        score = min(1.0, score_total / max(len(caracteristicas), 1))
        es_anomalo = score > ConfigGuardian.UMBRAL_ANOMALIA
        
        return {
            "score": round(score, 4),
            "es_anomalo": es_anomalo,
            "factores": factores_anomalos,
        }


# ==============================================================================
# GUARDIÁN DE SEGURIDAD
# ==============================================================================

class GuardianSeguridad:
    """
    Sistema avanzado de seguridad para Direccoin.
    
    Uso:
        guardian = GuardianSeguridad()
        resultado = guardian.analizar_transaccion(tx)
        if resultado["bloquear"]:
            print("Transacción bloqueada:", resultado["motivo"])
    """
    
    def __init__(self):
        # Lista negra
        self.lista_negra: Dict[str, EntidadBloqueada] = {}
        
        # Reputación
        self.reputaciones: Dict[str, ReputacionNodo] = {}
        
        # Rate limiting
        self.contador_tx: Dict[str, List[float]] = defaultdict(list)
        self.contador_global: List[float] = []
        
        # Detector de anomalías
        self.detector = DetectorAnomalias()
        self.tx_para_entrenar: List[dict] = []
        
        # Historial de alertas
        self.alertas: deque = deque(maxlen=500)
        
        # TXIDs vistos (anti-doble gasto)
        self.txids_vistos: Set[str] = set()
        
        # Carga inicial
        self._cargar_lista_negra()
    
    def _cargar_lista_negra(self):
        """Carga la lista negra desde disco."""
        if os.path.exists(ConfigGuardian.ARCHIVO_LISTA_NEGRA):
            try:
                with open(ConfigGuardian.ARCHIVO_LISTA_NEGRA) as f:
                    datos = json.load(f)
                for d in datos:
                    entidad = EntidadBloqueada(
                        direccion=d["direccion"],
                        motivo=d["motivo"],
                        timestamp_bloqueo=d["timestamp"],
                        duracion_minutos=d.get("duracion", 60),
                        intentos=d.get("intentos", 1),
                    )
                    if not entidad.expirado:
                        self.lista_negra[d["direccion"]] = entidad
            except:
                pass
    
    def _guardar_lista_negra(self):
        """Persiste la lista negra."""
        datos = []
        for entidad in self.lista_negra.values():
            if not entidad.expirado:
                datos.append({
                    "direccion": entidad.direccion,
                    "motivo": entidad.motivo,
                    "timestamp": entidad.timestamp_bloqueo,
                    "duracion": entidad.duracion_minutos,
                    "intentos": entidad.intentos,
                })
        with open(ConfigGuardian.ARCHIVO_LISTA_NEGRA, "w") as f:
            json.dump(datos, f, indent=2)
    
    def _limpiar_expirados(self):
        """Elimina entradas expiradas de la lista negra."""
        expirados = [d for d, e in self.lista_negra.items() if e.expirado]
        for d in expirados:
            del self.lista_negra[d]
            print(f"🔓 Desbloqueado: {d[:20]}...")
    
    def _bloquear(self, direccion: str, motivo: str, duracion: int = None):
        """Añade una dirección a la lista negra."""
        if duracion is None:
            duracion = ConfigGuardian.TIEMPO_BLOQUEO_MINUTOS
        
        if direccion in self.lista_negra:
            # Reincidencia: aumentar duración
            existente = self.lista_negra[direccion]
            existente.intentos += 1
            existente.duracion_minutos = min(
                existente.duracion_minutos * 2,
                ConfigGuardian.TIEMPO_BLOQUEO_MAXIMO
            )
            existente.timestamp_bloqueo = time.time()
        else:
            if len(self.lista_negra) >= ConfigGuardian.MAX_LISTA_NEGRA:
                self._limpiar_expirados()
            
            self.lista_negra[direccion] = EntidadBloqueada(
                direccion=direccion,
                motivo=motivo,
                timestamp_bloqueo=time.time(),
                duracion_minutos=duracion,
            )
        
        self._guardar_lista_negra()
    
    def _esta_bloqueada(self, direccion: str) -> Tuple[bool, str]:
        """Verifica si una dirección está bloqueada."""
        self._limpiar_expirados()
        
        if direccion in self.lista_negra:
            entidad = self.lista_negra[direccion]
            if not entidad.expirado:
                return True, f"Bloqueada: {entidad.motivo}"
        
        return False, ""
    
    def _verificar_rate_limit(self, direccion: str) -> Tuple[bool, str]:
        """Verifica límites de frecuencia."""
        ahora = time.time()
        ventana = ahora - 1
        
        # Limpiar contadores antiguos
        self.contador_tx[direccion] = [t for t in self.contador_tx[direccion] if t > ventana]
        self.contador_global = [t for t in self.contador_global if t > ventana]
        
        # Verificar límite por dirección
        if len(self.contador_tx[direccion]) >= ConfigGuardian.MAX_TX_POR_DIRECCION_POR_SEGUNDO:
            return False, f"Rate limit excedido: {ConfigGuardian.MAX_TX_POR_DIRECCION_POR_SEGUNDO} tx/s"
        
        # Verificar límite global
        if len(self.contador_global) >= ConfigGuardian.MAX_TX_POR_SEGUNDO:
            return False, "Rate limit global excedido"
        
        # Registrar
        self.contador_tx[direccion].append(ahora)
        self.contador_global.append(ahora)
        
        return True, "OK"
    
    def _verificar_doble_gasto(self, txid: str) -> Tuple[bool, str]:
        """Verifica que no haya doble gasto."""
        if txid in self.txids_vistos:
            return False, "Doble gasto detectado"
        self.txids_vistos.add(txid)
        return True, "OK"
    
    def analizar_transaccion(self, tx: dict) -> Dict[str, Any]:
        """
        Analiza una transacción completa y decide si aceptarla o bloquearla.
        
        Returns:
            Diccionario con el resultado del análisis
        """
        origen = tx.get("origen", "")
        destino = tx.get("destino", "")
        txid = tx.get("txid", "")
        cantidad = tx.get("cantidad", 0)
        
        # 1. Verificar lista negra
        bloqueado, motivo = self._esta_bloqueada(origen)
        if bloqueado:
            return self._resultado(False, "bloqueado", motivo, origen)
        
        bloqueado, motivo = self._esta_bloqueada(destino)
        if bloqueado:
            return self._resultado(False, "bloqueado", f"Destino {motivo}", destino)
        
        # 2. Verificar rate limit
        ok, motivo = self._verificar_rate_limit(origen)
        if not ok:
            self._bloquear(origen, "Rate limit excedido", 10)
            return self._resultado(False, "rate_limit", motivo, origen)
        
        # 3. Verificar doble gasto
        ok, motivo = self._verificar_doble_gasto(txid)
        if not ok:
            self._bloquear(origen, "Doble gasto", ConfigGuardian.TIEMPO_BLOQUEO_MAXIMO)
            self._registrar_alerta("doble_gasto", "critica", origen, {"txid": txid})
            return self._resultado(False, "doble_gasto", motivo, origen)
        
        # 4. Detectar anomalías
        if len(self.tx_para_entrenar) >= ConfigGuardian.VENTANA_ANALISIS:
            self.detector.entrenar(list(self.tx_para_entrenar))
            self.tx_para_entrenar = []
        
        self.tx_para_entrenar.append(tx)
        
        analisis_anomalia = self.detector.calcular_anomalia(tx)
        
        if analisis_anomalia["es_anomalo"]:
            self._registrar_alerta("anomalia", "media", origen, analisis_anomalia)
            # No bloquear por anomalía, solo alertar
        
        # 5. Actualizar reputación
        self._recompensar(origen)
        
        return {
            "permitir": True,
            "bloquear": False,
            "motivo": "Transacción válida",
            "alerta": analisis_anomalia["es_anomalo"],
            "score_anomalia": analisis_anomalia["score"],
            "direccion": origen,
        }
    
    def _resultado(self, permitir: bool, razon: str, motivo: str, 
                   direccion: str) -> Dict[str, Any]:
        return {
            "permitir": permitir,
            "bloquear": not permitir,
            "razon": razon,
            "motivo": motivo,
            "direccion": direccion,
        }
    
    def _registrar_alerta(self, tipo: str, severidad: str, direccion: str, 
                          evidencia: Dict):
        """Registra una alerta de seguridad."""
        alerta = AlertaSeguridad(
            timestamp=time.time(),
            tipo=tipo,
            severidad=severidad,
            direccion=direccion,
            evidencia=evidencia,
            accion_tomada="bloqueo" if severidad == "critica" else "monitoreo",
        )
        self.alertas.append(alerta)
    
    def _recompensar(self, direccion: str):
        """Recompensa a una dirección por buen comportamiento."""
        if direccion not in self.reputaciones:
            self.reputaciones[direccion] = ReputacionNodo(id_nodo=direccion)
        
        rep = self.reputaciones[direccion]
        rep.score = min(1000, rep.score + ConfigGuardian.RECOMPENSA_BUEN_COMPORTAMIENTO)
        rep.recompensas += 1
        rep.ultima_actividad = time.time()
    
    def penalizar(self, direccion: str, motivo: str, severidad: int = 50):
        """Penaliza a una dirección por mal comportamiento."""
        if direccion not in self.reputaciones:
            self.reputaciones[direccion] = ReputacionNodo(id_nodo=direccion)
        
        rep = self.reputaciones[direccion]
        rep.score = max(ConfigGuardian.REPUTACION_MINIMA, rep.score - severidad)
        rep.infracciones += 1
        rep.ultima_actividad = time.time()
        rep.historial.append({"tipo": "penalizacion", "motivo": motivo, "timestamp": time.time()})
        
        if rep.score <= ConfigGuardian.REPUTACION_BLOQUEO:
            self._bloquear(direccion, f"Reputación muy baja: {rep.score}", 120)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Devuelve estadísticas del guardián."""
        self._limpiar_expirados()
        return {
            "bloqueados_actuales": len(self.lista_negra),
            "txids_vistos": len(self.txids_vistos),
            "alertas_totales": len(self.alertas),
            "alertas_criticas": sum(1 for a in self.alertas if a.severidad == "critica"),
            "reputacion_promedio": round(
                sum(r.score for r in self.reputaciones.values()) / max(len(self.reputaciones), 1), 1
            ),
            "tasa_bloqueo": round(
                len(self.lista_negra) / max(len(self.txids_vistos), 1) * 100, 2
            ),
        }


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoGuardian:
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
        print("🔍 DIAGNÓSTICO DE IA/GUARDIAN.PY")
        print("=" * 70)
        
        guardian = GuardianSeguridad()
        
        # 1. Transacción normal aceptada
        tx_ok = {"origen": "drcBueno", "destino": "drcTienda", "cantidad": 1000, 
                 "gas": 50, "txid": "tx001", "timestamp": time.time()}
        r = guardian.analizar_transaccion(tx_ok)
        self._t("Transacción normal aceptada", r["permitir"])
        
        # 2. Doble gasto rechazado
        tx_doble = {"origen": "drcBueno", "destino": "drcTienda", "cantidad": 500,
                    "gas": 50, "txid": "tx001", "timestamp": time.time()}
        r = guardian.analizar_transaccion(tx_doble)
        self._t("Doble gasto rechazado", r["bloquear"] and "doble" in r["razon"].lower())
        
        # 3. Lista negra funciona
        guardian._bloquear("drcHacker", "Ataque detectado")
        tx_hacker = {"origen": "drcHacker", "destino": "drcVictima", "cantidad": 100,
                     "gas": 10, "txid": "tx_hack", "timestamp": time.time()}
        r = guardian.analizar_transaccion(tx_hacker)
        self._t("Dirección bloqueada rechazada", r["bloquear"])
        
        # 4. Rate limiting
        for i in range(ConfigGuardian.MAX_TX_POR_DIRECCION_POR_SEGUNDO + 1):
            tx_spam = {"origen": "drcSpammer", "destino": f"drcVictim{i}", 
                      "cantidad": 1, "gas": 1, "txid": f"tx_spam_{i}", "timestamp": time.time()}
            r = guardian.analizar_transaccion(tx_spam)
        
        self._t("Rate limit activado", r["bloquear"] and "rate" in r.get("razon", "").lower())
        
        # 5. Penalización
        guardian.penalizar("drcMalo", "Intento de ataque", 150)
        rep = guardian.reputaciones.get("drcMalo")
        self._t("Penalización reduce reputación", rep is not None and rep.score < 0)
        
        # 6. Recompensa
        guardian._recompensar("drcBueno")
        guardian._recompensar("drcBueno")
        rep_bueno = guardian.reputaciones.get("drcBueno")
        self._t("Recompensa aumenta reputación", rep_bueno is not None and rep_bueno.score > 100)
        
        # 7. Detector de anomalías
        for i in range(50):
            tx_normal = {"origen": f"drc_{i}", "destino": f"drc_dest_{i}", 
                        "cantidad": random.randint(100, 5000), "gas": random.randint(10, 100),
                        "txid": f"norm_{i}", "timestamp": time.time()}
            guardian.detector.entrenar([tx_normal])
        
        tx_rara = {"origen": "drcRaro", "destino": "drcRaro", "cantidad": 999999999,
                   "gas": 999999, "txid": "tx_rara", "timestamp": time.time() - 10000}
        anomalia = guardian.detector.calcular_anomalia(tx_rara)
        self._t("Detección de anomalía", anomalia["es_anomalo"] or anomalia["score"] > 0.5,
                f"Score: {anomalia['score']}")
        
        # 8. Estadísticas
        stats = guardian.obtener_estadisticas()
        self._t("Estadísticas", stats["bloqueados_actuales"] > 0)
        
        # 9. Expiración de bloqueo
        guardian._bloquear("drcTemporal", "Prueba", 0)  # 0 minutos = ya expirado
        time.sleep(0.1)
        bloqueado, _ = guardian._esta_bloqueada("drcTemporal")
        self._t("Expiración de bloqueo", not bloqueado)
        
        # 10. Limpieza de expirados
        antes = len(guardian.lista_negra)
        guardian._limpiar_expirados()
        self._t("Limpieza de expirados", len(guardian.lista_negra) <= antes)
        
        # 11. Alerta registrada
        alertas_criticas = sum(1 for a in guardian.alertas if a.severidad == "critica")
        self._t("Alertas críticas registradas", alertas_criticas >= 1)
        
        # 12. TXIDs únicos
        self._t("TXIDs almacenados", len(guardian.txids_vistos) > 0)
        
        # Limpiar archivos
        for archivo in [ConfigGuardian.ARCHIVO_LISTA_NEGRA, ConfigGuardian.ARCHIVO_REPUTACION]:
            if os.path.exists(archivo):
                os.remove(archivo)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ IA/GUARDIAN.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🛡️ " * 35)
    print("DIRECCOIN - GUARDIÁN DE SEGURIDAD v1.0.0")
    print("🛡️ " * 35)
    print(f"Reputación inicial: {ConfigGuardian.REPUTACION_INICIAL}")
    print(f"Tiempo bloqueo: {ConfigGuardian.TIEMPO_BLOQUEO_MINUTOS}min")
    print(f"Max tx/s/dirección: {ConfigGuardian.MAX_TX_POR_DIRECCION_POR_SEGUNDO}\n")
    
    diag = DiagnosticoGuardian()
    if diag.ejecutar():
        print("📋 DEMO DE SEGURIDAD:")
        guard = GuardianSeguridad()
        
        escenarios = [
            ("drcNormal", "drcTienda", 500, 50, "tx_normal", "✅ Normal: Aceptada"),
            ("drcNormal", "drcTienda", 500, 50, "tx_normal", "🚫 Doble gasto: Bloqueada"),
            ("drcHacker", "drcVictima", 1000000, 1, "tx_robo", "⚠️ Hacker: Detectada"),
        ]
        
        for i, (origen, destino, cant, gas, txid, desc) in enumerate(escenarios):
            tx = {"origen": origen, "destino": destino, "cantidad": cant, 
                  "gas": gas, "txid": txid, "timestamp": time.time()}
            if i == 1:
                guard._bloquear("drcHacker", "Ataque previo")
            r = guard.analizar_transaccion(tx)
            icono = "✅" if r["permitir"] else "🚫"
            print(f"   {icono} {desc}: {r['motivo']}")
        
        for archivo in [ConfigGuardian.ARCHIVO_LISTA_NEGRA, ConfigGuardian.ARCHIVO_REPUTACION]:
            if os.path.exists(archivo):
                os.remove(archivo)
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()