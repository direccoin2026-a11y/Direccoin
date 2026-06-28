#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - PROPAGACIÓN DE DATOS                         ║
║                    Versión: 1.0.0 | Archivo: red_p2p/propagacion.py        ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE PROPAGACIÓN DE TRANSACCIONES Y BLOQUES PARA DIRECCOIN.

Implementa:
  • Protocolo Gossip para difusión eficiente
  • Priorización de transacciones por gas
  • Anti-spam en propagación
  • Verificación previa antes de propagar
  • Límites de frecuencia por nodo

CARACTERÍSTICAS:
  • Gossip con fanout configurable
  • Cache de transacciones ya vistas
  • Prioridad por gas y antigüedad
  • Protección contra tormentas de propagación
  • Diagnóstico de 10 pruebas
"""

import hashlib
import time
import random
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from collections import OrderedDict

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigPropagacion:
    VERSION = "1.0.0"
    
    # Gossip
    FANOUT = 8                             # Nodos a los que propagar
    MAX_REENVIOS = 3                       # Máximo de reenvíos por mensaje
    CACHE_TX_SIZE = 10_000                 # Transacciones en caché
    CACHE_BLOQUE_SIZE = 1_000              # Bloques en caché
    
    # Frecuencia
    MAX_TX_POR_SEGUNDO_POR_NODO = 50       # Límite anti-spam
    MAX_BLOQUES_POR_MINUTO = 10            # Límite de bloques
    
    # Prioridad
    GAS_MINIMO_PROPAGACION = 1             # Gas mínimo para propagar
    TX_EXPIRACION_SEGUNDOS = 3600          # 1 hora


# ==============================================================================
# ESTRUCTURAS DE DATOS
# ==============================================================================

@dataclass
class MensajePropagacion:
    """Representa un mensaje propagado por la red."""
    tipo: str                              # "transaccion" o "bloque"
    datos: dict
    origen: str                            # ID del nodo que lo originó
    id_mensaje: str
    timestamp: float
    reenvios: int = 0
    prioridad: int = 0
    
    def __hash__(self):
        return hash(self.id_mensaje)
    
    def __eq__(self, other):
        return self.id_mensaje == other.id_mensaje


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3_hex(d: bytes) -> str:
        return hashlib.sha3_256(d).hexdigest()


# ==============================================================================
# CACHÉ DE MENSAJES VISTOS
# ==============================================================================

class CacheMensajes:
    """
    Almacena IDs de mensajes ya vistos para evitar reenvíos infinitos.
    Usa OrderedDict como LRU cache.
    """
    
    def __init__(self, max_size: int = 10_000):
        self.max_size = max_size
        self.vistos: OrderedDict = OrderedDict()
    
    def ya_visto(self, id_mensaje: str) -> bool:
        """Verifica si un mensaje ya fue visto."""
        if id_mensaje in self.vistos:
            self.vistos.move_to_end(id_mensaje)
            return True
        return False
    
    def marcar_visto(self, id_mensaje: str):
        """Marca un mensaje como visto."""
        if id_mensaje in self.vistos:
            self.vistos.move_to_end(id_mensaje)
        else:
            self.vistos[id_mensaje] = time.time()
            if len(self.vistos) > self.max_size:
                self.vistos.popitem(last=False)
    
    def total(self) -> int:
        return len(self.vistos)


# ==============================================================================
# CONTROL DE FRECUENCIA
# ==============================================================================

class ControlFrecuencia:
    """
    Limita la frecuencia de mensajes por nodo para prevenir spam.
    """
    
    def __init__(self):
        self.contadores: Dict[str, List[float]] = {}
    
    def permitir(self, id_nodo: str, tipo: str = "transaccion") -> bool:
        """
        Verifica si un nodo puede enviar otro mensaje.
        """
        ahora = time.time()
        ventana = ahora - 1  # Último segundo
        
        if id_nodo not in self.contadores:
            self.contadores[id_nodo] = []
        
        # Limpiar mensajes antiguos
        self.contadores[id_nodo] = [t for t in self.contadores[id_nodo] if t > ventana]
        
        # Verificar límite
        limite = ConfigPropagacion.MAX_TX_POR_SEGUNDO_POR_NODO if tipo == "transaccion" else ConfigPropagacion.MAX_BLOQUES_POR_MINUTO
        
        if len(self.contadores[id_nodo]) >= limite:
            return False
        
        self.contadores[id_nodo].append(ahora)
        return True
    
    def limpiar(self):
        """Limpia contadores antiguos."""
        ventana = time.time() - 60
        for nodo in list(self.contadores.keys()):
            self.contadores[nodo] = [t for t in self.contadores[nodo] if t > ventana]
            if not self.contadores[nodo]:
                del self.contadores[nodo]


# ==============================================================================
# PROPAGADOR GOSSIP
# ==============================================================================

class PropagadorGossip:
    """
    Implementa el protocolo Gossip para difundir transacciones y bloques.
    
    Uso:
        prop = PropagadorGossip(id_nodo="nodo_001")
        prop.propagar_transaccion(tx_dict, pares_disponibles)
        prop.propagar_bloque(bloque_dict, pares_disponibles)
    """
    
    def __init__(self, id_nodo: str):
        self.id_nodo = id_nodo
        self.cache_tx = CacheMensajes(ConfigPropagacion.CACHE_TX_SIZE)
        self.cache_bloques = CacheMensajes(ConfigPropagacion.CACHE_BLOQUE_SIZE)
        self.control_frecuencia = ControlFrecuencia()
        self.mensajes_propagados = 0
        self.mensajes_recibidos = 0
        self.mensajes_rechazados = 0
    
    def _generar_id_mensaje(self, datos: dict) -> str:
        """Genera un ID único para un mensaje."""
        contenido = str(datos).encode()
        return HashUtil.sha3_hex(contenido)[:32]
    
    def _calcular_prioridad(self, tipo: str, datos: dict) -> int:
        """
        Calcula la prioridad de un mensaje para ordenar la propagación.
        Mayor gas = mayor prioridad.
        """
        if tipo == "transaccion":
            gas = datos.get("gas", 0)
            return min(100, gas // 1000)  # 0-100 basado en gas
        elif tipo == "bloque":
            return 100  # Bloques siempre prioridad máxima
        return 0
    
    def _seleccionar_pares(self, pares: List[Any], fanout: int = None) -> List[Any]:
        """
        Selecciona un subconjunto de pares para propagar.
        Prefiere pares con mejor score.
        """
        if fanout is None:
            fanout = ConfigPropagacion.FANOUT
        
        if len(pares) <= fanout:
            return pares[:]
        
        # Ordenar por score (si tienen) y seleccionar
        pares_ordenados = sorted(pares, key=lambda p: getattr(p, 'score', 0), reverse=True)
        return pares_ordenados[:fanout]
    
    def propagar_transaccion(self, tx: dict, pares: List[Any],
                             nodo_origen: str = "") -> Tuple[bool, str]:
        """
        Propaga una transacción a la red.
        
        Args:
            tx: Diccionario con los datos de la transacción
            pares: Lista de pares disponibles
            nodo_origen: Nodo que originó la transacción
        
        Returns:
            (éxito, mensaje)
        """
        # Verificar gas mínimo
        if tx.get("gas", 0) < ConfigPropagacion.GAS_MINIMO_PROPAGACION:
            self.mensajes_rechazados += 1
            return False, "Gas insuficiente para propagación"
        
        # Verificar expiración
        timestamp = tx.get("timestamp", 0)
        if time.time() - timestamp > ConfigPropagacion.TX_EXPIRACION_SEGUNDOS:
            self.mensajes_rechazados += 1
            return False, "Transacción expirada"
        
        # Control de frecuencia
        if not self.control_frecuencia.permitir(self.id_nodo, "transaccion"):
            self.mensajes_rechazados += 1
            return False, "Límite de frecuencia alcanzado"
        
        # Generar ID y verificar caché
        id_mensaje = self._generar_id_mensaje(tx)
        
        if self.cache_tx.ya_visto(id_mensaje):
            self.mensajes_rechazados += 1
            return False, "Transacción ya vista"
        
        self.cache_tx.marcar_visto(id_mensaje)
        
        # Seleccionar pares para propagar
        pares_seleccionados = self._seleccionar_pares(pares)
        
        # Simular propagación a cada par
        for par in pares_seleccionados:
            if hasattr(par, 'id_nodo') and par.id_nodo == nodo_origen:
                continue  # No reenviar al origen
        
        self.mensajes_propagados += 1
        
        return True, f"Propagada a {len(pares_seleccionados)} pares"
    
    def propagar_bloque(self, bloque: dict, pares: List[Any],
                        nodo_origen: str = "") -> Tuple[bool, str]:
        """
        Propaga un bloque minado a la red.
        
        Args:
            bloque: Diccionario con los datos del bloque
            pares: Lista de pares disponibles
            nodo_origen: Nodo que minó el bloque
        
        Returns:
            (éxito, mensaje)
        """
        # Generar ID y verificar caché
        id_mensaje = self._generar_id_mensaje(bloque)
        
        if self.cache_bloques.ya_visto(id_mensaje):
            self.mensajes_rechazados += 1
            return False, "Bloque ya visto"
        
        self.cache_bloques.marcar_visto(id_mensaje)
        
        # Los bloques siempre se propagan (máxima prioridad)
        pares_seleccionados = self._seleccionar_pares(pares)
        
        self.mensajes_propagados += 1
        
        return True, f"Bloque propagado a {len(pares_seleccionados)} pares"
    
    def recibir_mensaje(self, tipo: str, datos: dict, id_mensaje: str = "") -> Tuple[bool, str]:
        """
        Procesa un mensaje recibido de otro nodo.
        
        Returns:
            (debe_propagarse, mensaje)
        """
        if not id_mensaje:
            id_mensaje = self._generar_id_mensaje(datos)
        
        cache = self.cache_tx if tipo == "transaccion" else self.cache_bloques
        
        if cache.ya_visto(id_mensaje):
            return False, "Ya visto, no propagar"
        
        cache.marcar_visto(id_mensaje)
        self.mensajes_recibidos += 1
        
        return True, "Nuevo, propagar"
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Devuelve estadísticas de propagación."""
        return {
            "mensajes_propagados": self.mensajes_propagados,
            "mensajes_recibidos": self.mensajes_recibidos,
            "mensajes_rechazados": self.mensajes_rechazados,
            "cache_tx_tamano": self.cache_tx.total(),
            "cache_bloques_tamano": self.cache_bloques.total(),
            "tasa_rechazo": round(
                self.mensajes_rechazados / max(self.mensajes_recibidos + self.mensajes_propagados, 1) * 100, 1
            ),
        }
    
    def limpiar_caches(self):
        """Limpia las cachés periódicamente."""
        self.control_frecuencia.limpiar()


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoPropagacion:
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
        print("🔍 DIAGNÓSTICO DE RED_P2P/PROPAGACION.PY")
        print("=" * 70)
        
        prop = PropagadorGossip("nodo_test")
        pares_falsos = [type('Par', (), {'id_nodo': f'par_{i}', 'score': 50})() for i in range(20)]
        
        # 1. Propagar transacción válida
        tx = {"origen": "drcA", "destino": "drcB", "cantidad": 1000, "gas": 100, "timestamp": time.time()}
        ok, msg = prop.propagar_transaccion(tx, pares_falsos)
        self._t("Propagar transacción", ok, msg)
        
        # 2. Rechazar transacción duplicada
        ok, msg = prop.propagar_transaccion(tx, pares_falsos)
        self._t("Rechazar duplicada", not ok)
        
        # 3. Rechazar gas insuficiente
        tx_bajo_gas = {"origen": "drcA", "destino": "drcB", "cantidad": 100, "gas": 0}
        ok, msg = prop.propagar_transaccion(tx_bajo_gas, pares_falsos)
        self._t("Rechazar gas bajo", not ok)
        
        # 4. Propagar bloque
        bloque = {"indice": 1, "hash": "d1abc", "transacciones": [tx]}
        ok, msg = prop.propagar_bloque(bloque, pares_falsos)
        self._t("Propagar bloque", ok)
        
        # 5. Rechazar bloque duplicado
        ok, msg = prop.propagar_bloque(bloque, pares_falsos)
        self._t("Rechazar bloque duplicado", not ok)
        
        # 6. Recibir mensaje nuevo
        tx_nueva = {"origen": "drcC", "destino": "drcD", "cantidad": 500, "gas": 50}
        ok, _ = prop.recibir_mensaje("transaccion", tx_nueva)
        self._t("Recibir mensaje nuevo", ok)
        
        # 7. Rechazar mensaje ya visto
        ok, _ = prop.recibir_mensaje("transaccion", tx_nueva)
        self._t("Rechazar mensaje ya visto", not ok)
        
        # 8. Control de frecuencia
        cf = ControlFrecuencia()
        for _ in range(50):
            cf.permitir("nodo_test", "transaccion")
        ok = cf.permitir("nodo_test", "transaccion")
        self._t("Límite de frecuencia", not ok)
        
        # 9. Estadísticas
        stats = prop.obtener_estadisticas()
        self._t("Estadísticas", stats["mensajes_propagados"] >= 2)
        
        # 10. Selección de pares
        seleccionados = prop._seleccionar_pares(pares_falsos, 5)
        self._t("Seleccionar 5 pares", len(seleccionados) == 5)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ RED_P2P/PROPAGACION.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "📨 " * 35)
    print("DIRECCOIN - PROPAGACIÓN GOSSIP v1.0.0")
    print("📨 " * 35)
    print(f"Fanout: {ConfigPropagacion.FANOUT} pares")
    print(f"Max TX/s/nodo: {ConfigPropagacion.MAX_TX_POR_SEGUNDO_POR_NODO}\n")
    
    diag = DiagnosticoPropagacion()
    if diag.ejecutar():
        print("📋 DEMO:")
        prop = PropagadorGossip("demo")
        pares = [type('Par', (), {'id_nodo': f'p{i}', 'score': 80-i})() for i in range(10)]
        tx = {"origen": "drcA", "destino": "drcB", "cantidad": 500, "gas": 100, "timestamp": time.time()}
        ok, msg = prop.propagar_transaccion(tx, pares)
        print(f"   Transacción: {msg}")
        stats = prop.obtener_estadisticas()
        print(f"   Propaga2/Recib2/Rechaz2: {stats['mensajes_propagados']}/{stats['mensajes_recibidos']}/{stats['mensajes_rechazados']}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()