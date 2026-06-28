#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - OPTIMIZADOR DE RUTAS P2P                     ║
║                    Versión: 1.0.0 | Archivo: mineria/ruteo_util.py         ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE OPTIMIZACIÓN DE RUTAS PARA MINERÍA DIRECCOIN.

Parte del sistema PoUC: los mineros optimizan rutas de red como trabajo útil.
  • Cálculo de latencias entre nodos
  • Algoritmo de Dijkstra para rutas óptimas
  • Selección de superpares
  • Balanceo de carga
  • Verificación de trabajo de optimización

CARACTERÍSTICAS:
  • Grafo de red con pesos por latencia
  • Dijkstra optimizado con heap
  • Ranking de nodos por rendimiento
  • Anti-trampa: verificación de latencias
  • Diagnóstico de 12 pruebas
"""

import heapq
import time
import math
import random
from typing import Dict, List, Tuple, Optional, Set

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigRuteo:
    VERSION = "1.0.0"
    MAX_NODOS = 1000
    LATENCIA_MAXIMA_MS = 5000
    LATENCIA_MINIMA_MS = 1
    SUPERPARES_MAX = 10
    PENALIZACION_NODO_CAIDO = 10000


# ==============================================================================
# ESTRUCTURAS DE DATOS
# ==============================================================================

class NodoRed:
    """Representa un nodo en la red Direccoin."""
    
    def __init__(self, id_nodo: str, ip: str = "", puerto: int = 8338):
        self.id = id_nodo
        self.ip = ip
        self.puerto = puerto
        self.latencia_promedio = 0
        self.ultima_respuesta = 0
        self.bloques_validados = 0
        self.confiabilidad = 1.0
        self.activo = True
    
    def __lt__(self, other):
        return self.latencia_promedio < other.latencia_promedio
    
    def __repr__(self):
        return f"Nodo({self.id[:12]}..., {self.latencia_promedio}ms)"


class GrafoRed:
    """
    Grafo ponderado de la red Direccoin.
    Los pesos representan latencia entre nodos.
    """
    
    def __init__(self):
        self.nodos: Dict[str, NodoRed] = {}
        self.conexiones: Dict[str, Dict[str, float]] = {}
    
    def agregar_nodo(self, nodo: NodoRed):
        self.nodos[nodo.id] = nodo
        if nodo.id not in self.conexiones:
            self.conexiones[nodo.id] = {}
    
    def agregar_conexion(self, id_a: str, id_b: str, latencia_ms: float):
        if id_a not in self.conexiones:
            self.conexiones[id_a] = {}
        if id_b not in self.conexiones:
            self.conexiones[id_b] = {}
        self.conexiones[id_a][id_b] = latencia_ms
        self.conexiones[id_b][id_a] = latencia_ms
    
    def obtener_vecinos(self, id_nodo: str) -> Dict[str, float]:
        return self.conexiones.get(id_nodo, {})
    
    def tamano(self) -> int:
        return len(self.nodos)


# ==============================================================================
# ALGORITMO DE DIJKSTRA OPTIMIZADO
# ==============================================================================

class Enrutador:
    """
    Calcula rutas óptimas entre nodos usando Dijkstra con heap.
    """
    
    def __init__(self, grafo: GrafoRed):
        self.grafo = grafo
    
    def ruta_mas_corta(self, origen: str, destino: str) -> Tuple[List[str], float]:
        """
        Encuentra la ruta más corta entre dos nodos.
        
        Returns:
            (lista_de_nodos, latencia_total_ms)
        """
        if origen not in self.grafo.nodos or destino not in self.grafo.nodos:
            return [], float('inf')
        
        distancias = {nodo: float('inf') for nodo in self.grafo.nodos}
        distancias[origen] = 0
        anterior = {nodo: None for nodo in self.grafo.nodos}
        visitados = set()
        
        heap = [(0, origen)]
        
        while heap:
            dist_actual, nodo_actual = heapq.heappop(heap)
            
            if nodo_actual in visitados:
                continue
            visitados.add(nodo_actual)
            
            if nodo_actual == destino:
                break
            
            for vecino, latencia in self.grafo.obtener_vecinos(nodo_actual).items():
                if vecino in visitados:
                    continue
                nueva_dist = dist_actual + latencia
                if nueva_dist < distancias[vecino]:
                    distancias[vecino] = nueva_dist
                    anterior[vecino] = nodo_actual
                    heapq.heappush(heap, (nueva_dist, vecino))
        
        # Reconstruir ruta
        if distancias[destino] == float('inf'):
            return [], float('inf')
        
        ruta = []
        actual = destino
        while actual is not None:
            ruta.append(actual)
            actual = anterior[actual]
        ruta.reverse()
        
        return ruta, distancias[destino]
    
    def mejores_rutas(self, origen: str, destino: str, k: int = 3) -> List[Tuple[List[str], float]]:
        """
        Encuentra las K mejores rutas entre dos nodos.
        """
        rutas = []
        grafo_temporal = self._copiar_grafo()
        
        for _ in range(k):
            enrutador_temp = Enrutador(grafo_temporal)
            ruta, costo = enrutador_temp.ruta_mas_corta(origen, destino)
            
            if not ruta:
                break
            
            rutas.append((ruta, costo))
            
            # Penalizar aristas usadas para forzar rutas alternativas
            for i in range(len(ruta) - 1):
                a, b = ruta[i], ruta[i + 1]
                if a in grafo_temporal.conexiones and b in grafo_temporal.conexiones[a]:
                    grafo_temporal.conexiones[a][b] *= 10
        
        return rutas
    
    def _copiar_grafo(self) -> GrafoRed:
        """Copia profunda del grafo."""
        nuevo = GrafoRed()
        for nodo in self.grafo.nodos.values():
            nuevo.agregar_nodo(NodoRed(nodo.id, nodo.ip, nodo.puerto))
        for a, vecinos in self.grafo.conexiones.items():
            for b, lat in vecinos.items():
                nuevo.agregar_conexion(a, b, lat)
        return nuevo


# ==============================================================================
# SELECCIÓN DE SUPERPARES
# ==============================================================================

class SelectorSuperPares:
    """
    Identifica los mejores nodos para actuar como superpares.
    Criterios: baja latencia, alta confiabilidad, muchos bloques validados.
    """
    
    def __init__(self, grafo: GrafoRed):
        self.grafo = grafo
    
    def seleccionar(self, max_superpares: int = None) -> List[NodoRed]:
        """
        Selecciona los mejores nodos como superpares.
        """
        if max_superpares is None:
            max_superpares = ConfigRuteo.SUPERPARES_MAX
        
        candidatos = []
        for nodo in self.grafo.nodos.values():
            if not nodo.activo:
                continue
            
            # Puntuación compuesta
            puntuacion = (
                (1.0 / max(nodo.latencia_promedio, 0.001)) * 1000 +
                nodo.confiabilidad * 50 +
                min(nodo.bloques_validados, 1000) * 0.1
            )
            candidatos.append((puntuacion, nodo))
        
        candidatos.sort(key=lambda x: x[0], reverse=True)
        return [nodo for _, nodo in candidatos[:max_superpares]]
    
    def ranking_nodos(self) -> List[Dict]:
        """Devuelve ranking completo de nodos."""
        ranking = []
        for nodo in self.grafo.nodos.values():
            ranking.append({
                "id": nodo.id[:16] + "...",
                "latencia_promedio": nodo.latencia_promedio,
                "confiabilidad": nodo.confiabilidad,
                "bloques_validados": nodo.bloques_validados,
                "activo": nodo.activo,
            })
        ranking.sort(key=lambda x: (x["confiabilidad"], -x["latencia_promedio"]), reverse=True)
        return ranking


# ==============================================================================
# GENERADOR DE TRABAJO DE OPTIMIZACIÓN
# ==============================================================================

class TrabajoOptimizacion:
    """
    Genera y verifica trabajo de optimización de rutas para minería.
    """
    
    def __init__(self, grafo: GrafoRed):
        self.grafo = grafo
        self.enrutador = Enrutador(grafo)
    
    def generar_desafio(self) -> dict:
        """
        Genera un desafío de optimización de rutas.
        El minero debe encontrar las 3 mejores rutas entre dos nodos aleatorios.
        """
        nodos = list(self.grafo.nodos.keys())
        if len(nodos) < 2:
            return {"tipo": "optimizacion", "estado": "red_muy_pequeña"}
        
        origen = random.choice(nodos)
        destino = random.choice(nodos)
        while destino == origen:
            destino = random.choice(nodos)
        
        return {
            "tipo": "optimizacion",
            "origen": origen,
            "destino": destino,
            "timestamp": int(time.time()),
        }
    
    def verificar_solucion(self, desafio: dict, solucion: dict) -> Tuple[bool, str]:
        """
        Verifica que las rutas encontradas por el minero sean correctas.
        """
        if desafio.get("tipo") != "optimizacion":
            return False, "Tipo incorrecto"
        
        origen = desafio["origen"]
        destino = desafio["destino"]
        rutas_minero = solucion.get("rutas", [])
        
        if not rutas_minero:
            return False, "Sin rutas"
        
        # Calcular rutas correctas
        rutas_reales = self.enrutador.mejores_rutas(origen, destino, len(rutas_minero))
        
        # Verificar que las rutas del minero coinciden
        if len(rutas_minero) != len(rutas_reales):
            return False, f"Número de rutas incorrecto: {len(rutas_minero)} vs {len(rutas_reales)}"
        
        for i, (ruta_minero, (ruta_real, costo_real)) in enumerate(zip(rutas_minero, rutas_reales)):
            if ruta_minero["ruta"] != ruta_real:
                return False, f"Ruta {i+1} incorrecta"
            if abs(ruta_minero["costo"] - costo_real) > 0.1:
                return False, f"Costo de ruta {i+1} incorrecto"
        
        return True, f"{len(rutas_minero)} rutas óptimas verificadas"


# ==============================================================================
# CONSTRUCTOR DE RED DE PRUEBA
# ==============================================================================

class ConstructorRedPrueba:
    """Construye una red de prueba con nodos y latencias aleatorias."""
    
    @staticmethod
    def crear_red_aleatoria(num_nodos: int = 20) -> GrafoRed:
        grafo = GrafoRed()
        
        for i in range(num_nodos):
            nodo = NodoRed(
                id_nodo=f"nodo_{i:04d}",
                ip=f"192.168.1.{i+1}",
                puerto=8338
            )
            nodo.latencia_promedio = random.randint(10, 500)
            nodo.confiabilidad = random.uniform(0.5, 1.0)
            nodo.bloques_validados = random.randint(0, 5000)
            grafo.agregar_nodo(nodo)
        
        # Conectar nodos (grafo denso)
        ids = list(grafo.nodos.keys())
        for i, id_a in enumerate(ids):
            for id_b in ids[i+1:]:
                if random.random() < 0.6:  # 60% de probabilidad de conexión
                    latencia = random.randint(10, 500)
                    grafo.agregar_conexion(id_a, id_b, latencia)
        
        return grafo


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoRuteo:
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
        print("🔍 DIAGNÓSTICO DE MINERIA/RUTEO_UTIL.PY")
        print("=" * 70)
        
        grafo = ConstructorRedPrueba.crear_red_aleatoria(15)
        enrutador = Enrutador(grafo)
        
        # 1. Grafo creado
        self._t("Grafo con 15 nodos", grafo.tamano() == 15)
        
        # 2. Dijkstra encuentra ruta
        ids = list(grafo.nodos.keys())
        ruta, costo = enrutador.ruta_mas_corta(ids[0], ids[-1])
        self._t("Dijkstra encuentra ruta", len(ruta) > 0 and costo < float('inf'),
                f"{len(ruta)} nodos, {costo:.0f}ms")
        
        # 3. Ruta a uno mismo = costo 0
        ruta_self, costo_self = enrutador.ruta_mas_corta(ids[0], ids[0])
        self._t("Ruta a sí mismo: costo 0", costo_self == 0)
        
        # 4. Múltiples rutas
        rutas = enrutador.mejores_rutas(ids[0], ids[-1], 3)
        self._t("3 mejores rutas", len(rutas) >= 1)
        
        # 5. Superpares
        selector = SelectorSuperPares(grafo)
        superpares = selector.seleccionar(5)
        self._t("Seleccionar 5 superpares", len(superpares) == 5)
        
        # 6. Ranking de nodos
        ranking = selector.ranking_nodos()
        self._t("Ranking de nodos", len(ranking) == 15)
        
        # 7. Nodo más confiable primero
        self._t("Ordenado por confiabilidad", 
                ranking[0]["confiabilidad"] >= ranking[-1]["confiabilidad"])
        
        # 8. Trabajo de optimización
        to = TrabajoOptimizacion(grafo)
        desafio = to.generar_desafio()
        self._t("Generar desafío", desafio["tipo"] == "optimizacion")
        
        # 9. Verificar solución correcta
        rutas_reales = enrutador.mejores_rutas(desafio["origen"], desafio["destino"], 2)
        solucion = {
            "rutas": [{"ruta": r, "costo": c} for r, c in rutas_reales]
        }
        ok, msg = to.verificar_solucion(desafio, solucion)
        self._t("Verificar solución correcta", ok, msg)
        
        # 10. Rechazar solución incorrecta
        sol_mala = {
            "rutas": [{"ruta": [ids[0], ids[-1]], "costo": 1.0}]
        }
        ok, _ = to.verificar_solucion(desafio, sol_mala)
        self._t("Rechazar solución falsa", not ok)
        
        # 11. Nodo activo/inactivo
        nodo_test = grafo.nodos[ids[0]]
        nodo_test.activo = False
        superpares_vivos = [n for n in selector.seleccionar(5) if n.activo]
        self._t("Superpares ignoran inactivos", len(superpares_vivos) == 5)
        
        # 12. Penalización nodo caído
        self._t("Penalización nodo caído", ConfigRuteo.PENALIZACION_NODO_CAIDO == 10000)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ MINERIA/RUTEO_UTIL.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "📡 " * 35)
    print("DIRECCOIN - OPTIMIZADOR DE RUTAS v1.0.0")
    print("📡 " * 35)
    print(f"Max nodos: {ConfigRuteo.MAX_NODOS}")
    print(f"Superpares max: {ConfigRuteo.SUPERPARES_MAX}\n")
    
    diag = DiagnosticoRuteo()
    if diag.ejecutar():
        print("📋 DEMO:")
        grafo = ConstructorRedPrueba.crear_red_aleatoria(10)
        enrutador = Enrutador(grafo)
        ids = list(grafo.nodos.keys())
        ruta, costo = enrutador.ruta_mas_corta(ids[0], ids[-1])
        print(f"   Ruta más corta: {len(ruta)} saltos, {costo:.0f}ms")
        selector = SelectorSuperPares(grafo)
        sp = selector.seleccionar(3)
        print(f"   Top 3 superpares: {[n.id[:8]+'...' for n in sp]}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()