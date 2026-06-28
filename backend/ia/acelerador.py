#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - IA: ACELERADOR DE RED                        ║
║                    Versión: 1.0.1 | Archivo: ia/acelerador.py              ║
╚══════════════════════════════════════════════════════════════════════════════╝

SISTEMA DE IA PARA OPTIMIZACIÓN DE VELOCIDAD EN DIRECCOIN.
"""

import time
import math
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque

class ConfigAcelerador:
    VERSION = "1.0.1"
    MAX_RUTAS_ALTERNATIVAS = 5
    VENTANA_LATENCIA = 50
    PENALIZACION_NODO_LENTO = 2.0
    BONIFICACION_SUPERPAR = 0.5
    LATENCIA_OPTIMA_MS = 50
    LATENCIA_ACEPTABLE_MS = 200
    LATENCIA_MALA_MS = 500
    INTERVALO_REFRESCO_RUTAS = 30


@dataclass
class RutaOptimizada:
    nodos: List[str]
    latencia_total_ms: float
    saltos: int
    confiabilidad: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class NodoRendimiento:
    id_nodo: str
    latencia_promedio_ms: float = 0.0
    latencias: deque = field(default_factory=lambda: deque(maxlen=ConfigAcelerador.VENTANA_LATENCIA))
    paquetes_procesados: int = 0
    tasa_exito: float = 1.0
    score: float = 0.0
    es_superpar: bool = False
    ultima_actualizacion: float = field(default_factory=time.time)


class AceleradorRed:
    
    def __init__(self):
        self.nodos: Dict[str, NodoRendimiento] = {}
        self.conexiones: Dict[str, Dict[str, float]] = {}
        self.superpares: List[str] = []
    
    def registrar_nodo(self, id_nodo: str, latencia_ms: float = 0):
        if id_nodo not in self.nodos:
            self.nodos[id_nodo] = NodoRendimiento(id_nodo=id_nodo)
        nodo = self.nodos[id_nodo]
        nodo.latencias.append(latencia_ms)
        if nodo.latencias:
            nodo.latencia_promedio_ms = sum(nodo.latencias) / len(nodo.latencias)
        nodo.ultima_actualizacion = time.time()
        self._actualizar_score(id_nodo)
    
    def registrar_conexion(self, origen: str, destino: str, latencia_ms: float):
        if origen not in self.conexiones:
            self.conexiones[origen] = {}
        self.conexiones[origen][destino] = latencia_ms
        if destino not in self.conexiones:
            self.conexiones[destino] = {}
        self.conexiones[destino][origen] = latencia_ms
    
    def _actualizar_score(self, id_nodo: str):
        if id_nodo not in self.nodos: return
        nodo = self.nodos[id_nodo]
        s_lat = max(0, 100 - nodo.latencia_promedio_ms) / 100
        s_ex = nodo.tasa_exito
        s_sp = 1.5 if nodo.es_superpar else 1.0
        nodo.score = s_lat * s_ex * s_sp
    
    def seleccionar_superpares(self, max_sp: int = 10) -> List[str]:
        if not self.nodos: return []
        ranking = sorted(self.nodos.items(), key=lambda x: x[1].score, reverse=True)
        self.superpares = [id_n for id_n, _ in ranking[:max_sp]]
        for id_n in self.nodos:
            self.nodos[id_n].es_superpar = id_n in self.superpares
            self._actualizar_score(id_n)
        return self.superpares
    
    def encontrar_mejor_ruta(self, origen: str, destino: str, max_rutas: int = None) -> List[Dict]:
        if max_rutas is None: max_rutas = ConfigAcelerador.MAX_RUTAS_ALTERNATIVAS
        if origen not in self.nodos or destino not in self.nodos: return []
        if origen == destino: return [{"ruta": [origen], "latencia_ms": 0, "saltos": 0}]
        
        dist = {n: float('inf') for n in self.nodos}
        dist[origen] = 0
        prev = {n: None for n in self.nodos}
        visitados = set()
        
        while len(visitados) < len(self.nodos):
            no_vis = {n: d for n, d in dist.items() if n not in visitados}
            if not no_vis: break
            actual = min(no_vis, key=no_vis.get)
            if actual == destino: break
            visitados.add(actual)
            
            for vecino, lat in self.conexiones.get(actual, {}).items():
                if vecino in visitados: continue
                nv = self.nodos.get(vecino)
                pen = ConfigAcelerador.PENALIZACION_NODO_LENTO if nv and nv.latencia_promedio_ms > ConfigAcelerador.LATENCIA_MALA_MS else 1.0
                bon = ConfigAcelerador.BONIFICACION_SUPERPAR if nv and nv.es_superpar else 1.0
                nd = dist[actual] + lat * pen * bon
                if nd < dist[vecino]:
                    dist[vecino] = nd
                    prev[vecino] = actual
        
        if dist[destino] == float('inf'): return []
        
        ruta = []
        a = destino
        while a is not None:
            ruta.append(a)
            a = prev[a]
        ruta.reverse()
        return [{"ruta": ruta, "latencia_ms": round(dist[destino], 2), "saltos": len(ruta)-1}]
    
    def balancear_carga(self, txs: int, nodos_disp: List[str]) -> Dict[str, int]:
        if not nodos_disp: return {}
        scores = [self.nodos[n].score if n in self.nodos else 0.5 for n in nodos_disp]
        total = sum(scores)
        if total == 0:
            por = txs // len(nodos_disp)
            return {n: por for n in nodos_disp}
        distr = {}
        rest = txs
        for i, n in enumerate(nodos_disp):
            if i == len(nodos_disp) - 1:
                distr[n] = rest
            else:
                asig = int(txs * scores[i] / total)
                distr[n] = asig
                rest -= asig
        return distr
    
    def predecir_latencia(self, origen: str, destino: str) -> Dict:
        if destino not in self.nodos:
            return {"latencia_predicha": -1, "confianza": 0}
        nd = self.nodos[destino]
        if len(nd.latencias) < 5:
            return {"latencia_predicha": nd.latencia_promedio_ms, "confianza": 30}
        rec = list(nd.latencias)[-10:]
        tend = (rec[-1] - rec[0]) / len(rec)
        return {
            "latencia_predicha": round(nd.latencia_promedio_ms + tend * 5, 2),
            "latencia_actual": round(nd.latencia_promedio_ms, 2),
            "tendencia": "mejorando" if tend < -1 else "empeorando" if tend > 1 else "estable",
            "confianza": min(90, len(rec) * 5),
        }
    
    def obtener_estadisticas(self) -> Dict:
        return {
            "nodos": len(self.nodos),
            "superpares": len(self.superpares),
            "latencia_media": round(sum(n.latencia_promedio_ms for n in self.nodos.values()) / max(len(self.nodos), 1), 2),
        }


class DiagnosticoAcelerador:
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
        print("🔍 DIAGNÓSTICO IA/ACELERADOR")
        print("=" * 70)
        
        acel = AceleradorRed()
        for i in range(20):
            acel.registrar_nodo(f"nodo_{i}", random.randint(5, 300))
        self._t("20 nodos", len(acel.nodos) == 20)
        
        for i in range(19):
            acel.registrar_conexion(f"nodo_{i}", f"nodo_{i+1}", random.randint(10, 100))
        for i in range(0, 18, 2):
            acel.registrar_conexion(f"nodo_{i}", f"nodo_{i+2}", random.randint(20, 150))
        self._t("Conexiones", len(acel.conexiones) > 0)
        
        sp = acel.seleccionar_superpares(5)
        self._t("5 superpares", len(sp) == 5)
        
        ruta = acel.encontrar_mejor_ruta("nodo_0", "nodo_10")
        self._t("Ruta encontrada", len(ruta) > 0 and len(ruta[0]["ruta"]) > 1)
        
        ruta_self = acel.encontrar_mejor_ruta("nodo_0", "nodo_0")
        self._t("Ruta a sí mismo", ruta_self[0]["latencia_ms"] == 0)
        
        for _ in range(10):
            acel.registrar_nodo("nodo_test", random.randint(40, 60))
        pred = acel.predecir_latencia("nodo_0", "nodo_test")
        self._t("Predicción", "latencia_predicha" in pred)
        
        distr = acel.balancear_carga(1000, ["nodo_0", "nodo_1", "nodo_2"])
        self._t("Balanceo", sum(distr.values()) == 1000)
        
        stats = acel.obtener_estadisticas()
        self._t("Estadísticas", stats["nodos"] >= 20)
        
        n0 = acel.nodos.get("nodo_0")
        self._t("Score calculado", n0 is not None and n0.score >= 0)
        
        if sp:
            nsp = acel.nodos.get(sp[0])
            n15 = acel.nodos.get("nodo_15")
            self._t("Superpar ≥ Normal", nsp.score >= (n15.score if n15 else 0))
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ ACELERADOR OK\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "⚡ " * 35)
    print("DIRECCOIN - ACELERADOR v1.0.1")
    print("⚡ " * 35)
    diag = DiagnosticoAcelerador()
    if diag.ejecutar():
        acel = AceleradorRed()
        for i in range(10):
            acel.registrar_nodo(f"n_{i}", random.randint(5, 200))
        for i in range(9):
            acel.registrar_conexion(f"n_{i}", f"n_{i+1}", random.randint(10, 80))
        sp = acel.seleccionar_superpares(3)
        ruta = acel.encontrar_mejor_ruta("n_0", "n_9")
        if ruta:
            print(f"📋 Mejor ruta: {len(ruta[0]['ruta'])} saltos, {ruta[0]['latencia_ms']}ms")
        print(f"   Superpares: {sp}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()