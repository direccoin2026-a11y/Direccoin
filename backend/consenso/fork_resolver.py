#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - RESOLUCIÓN DE FORKS                          ║
║                    Versión: 1.0.0 | Archivo: consenso/fork_resolver.py     ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE RESOLUCIÓN DE BIFURCACIONES PARA DIRECCOIN.

Gestiona:
  • Detección de forks (bifurcaciones)
  • Elección de cadena canónica (más trabajo acumulado)
  • Reorganización de bloques
  • Protección contra ataques de reorganización profunda
  • Resolución de conflictos entre cadenas

CARACTERÍSTICAS:
  • Regla de cadena más pesada (mayor trabajo acumulado)
  • Límite máximo de reorganización (100 bloques)
  • Verificación de integridad post-reorganización
  • Registro de forks para auditoría
  • Diagnóstico de 10 pruebas
"""

import hashlib
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigForkResolver:
    VERSION = "1.0.0"
    MAX_REORGANIZACION = 100          # Máximo de bloques a reorganizar
    MIN_TRABAJO_ACUMULADO = 1         # Trabajo mínimo para considerar cadena
    MAX_FORKS_REGISTRADOS = 50        # Historial máximo de forks


# ==============================================================================
# ESTRUCTURAS DE DATOS
# ==============================================================================

@dataclass
class RamaAlternativa:
    """Representa una rama alternativa de la cadena."""
    id_rama: str
    bloques: List[dict] = field(default_factory=list)
    trabajo_acumulado: int = 0
    altura: int = 0
    timestamp_deteccion: int = 0
    resuelta: bool = False
    ganadora: bool = False


@dataclass
class ResultadoFork:
    """Resultado de una resolución de fork."""
    hubo_fork: bool
    hubo_reorganizacion: bool
    bloques_reorganizados: int
    cadena_ganadora: str       # "principal" o "alternativa"
    trabajo_principal: int
    trabajo_alternativa: int
    mensaje: str
    detalles: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# RESOLVEDOR DE FORKS
# ==============================================================================

class ForkResolver:
    """
    Detecta y resuelve bifurcaciones en la cadena de bloques.
    
    Principio: La cadena con mayor trabajo acumulado (suma de dificultades)
    es la cadena canónica.
    
    Uso:
        resolver = ForkResolver()
        resultado = resolver.resolver(cadena_principal, cadena_alternativa)
        if resultado.hubo_reorganizacion:
            print(f"Reorganizados {resultado.bloques_reorganizados} bloques")
    """
    
    def __init__(self):
        self.forks_historial: List[RamaAlternativa] = []
        self.total_reorganizaciones = 0
        self.bloques_reorganizados_total = 0
    
    def detectar_fork(self, cadena_principal: List[dict],
                      cadena_alternativa: List[dict]) -> Optional[dict]:
        """
        Detecta el punto de bifurcación entre dos cadenas.
        
        Returns:
            Diccionario con {indice_fork, hash_comun} o None si son iguales
        """
        if not cadena_principal or not cadena_alternativa:
            return None
        
        # Recorrer desde el génesis hasta encontrar divergencia
        for i in range(min(len(cadena_principal), len(cadena_alternativa))):
            hash_ppal = cadena_principal[i].get("hash", "")
            hash_alt = cadena_alternativa[i].get("hash", "")
            
            if hash_ppal != hash_alt:
                return {
                    "indice_fork": i,
                    "hash_comun": cadena_principal[i-1].get("hash", "0"*64) if i > 0 else "0"*64,
                    "altura_fork": i,
                }
        
        # Si una es prefijo de la otra
        if len(cadena_principal) != len(cadena_alternativa):
            return {
                "indice_fork": min(len(cadena_principal), len(cadena_alternativa)),
                "hash_comun": cadena_principal[-1].get("hash", "") if len(cadena_principal) <= len(cadena_alternativa) else cadena_alternativa[-1].get("hash", ""),
                "altura_fork": min(len(cadena_principal), len(cadena_alternativa)),
            }
        
        return None  # Cadenas idénticas
    
    def calcular_trabajo_acumulado(self, cadena: List[dict]) -> int:
        """
        Calcula el trabajo acumulado de una cadena.
        Trabajo = suma de 2^dificultad para cada bloque.
        """
        trabajo = 0
        for bloque in cadena:
            dificultad = bloque.get("dificultad", 1)
            trabajo += 2 ** dificultad
        return trabajo
    
    def es_cadena_valida(self, cadena: List[dict]) -> bool:
        """
        Verifica rápidamente que una cadena sea internamente consistente.
        """
        if not cadena:
            return False
        
        for i in range(1, len(cadena)):
            bloque = cadena[i]
            anterior = cadena[i-1]
            
            if bloque.get("hash_previo") != anterior.get("hash"):
                return False
            if bloque.get("indice") != anterior.get("indice", -1) + 1:
                return False
        
        return True
    
    def resolver(self, cadena_principal: List[dict],
                 cadena_alternativa: List[dict]) -> ResultadoFork:
        """
        Resuelve un fork entre dos cadenas.
        
        Args:
            cadena_principal: La cadena que el nodo tiene actualmente
            cadena_alternativa: La cadena alternativa recibida
        
        Returns:
            ResultadoFork con la decisión
        """
        # Verificar si son iguales
        fork_info = self.detectar_fork(cadena_principal, cadena_alternativa)
        
        if fork_info is None:
            return ResultadoFork(
                hubo_fork=False,
                hubo_reorganizacion=False,
                bloques_reorganizados=0,
                cadena_ganadora="principal",
                trabajo_principal=0,
                trabajo_alternativa=0,
                mensaje="Cadenas idénticas, sin fork",
            )
        
        # Verificar validez de cadenas
        if not self.es_cadena_valida(cadena_principal):
            return ResultadoFork(
                hubo_fork=True,
                hubo_reorganizacion=True,
                bloques_reorganizados=len(cadena_alternativa),
                cadena_ganadora="alternativa",
                trabajo_principal=0,
                trabajo_alternativa=0,
                mensaje="Cadena principal inválida, adoptando alternativa",
            )
        
        if not self.es_cadena_valida(cadena_alternativa):
            return ResultadoFork(
                hubo_fork=True,
                hubo_reorganizacion=False,
                bloques_reorganizados=0,
                cadena_ganadora="principal",
                trabajo_principal=0,
                trabajo_alternativa=0,
                mensaje="Cadena alternativa inválida, manteniendo principal",
            )
        
        # Calcular trabajo acumulado
        trabajo_ppal = self.calcular_trabajo_acumulado(cadena_principal)
        trabajo_alt = self.calcular_trabajo_acumulado(cadena_alternativa)
        
        # Verificar límite de reorganización
        bloques_a_reorg = len(cadena_alternativa) - fork_info["altura_fork"]
        
        if bloques_a_reorg > ConfigForkResolver.MAX_REORGANIZACION:
            return ResultadoFork(
                hubo_fork=True,
                hubo_reorganizacion=False,
                bloques_reorganizados=0,
                cadena_ganadora="principal",
                trabajo_principal=trabajo_ppal,
                trabajo_alternativa=trabajo_alt,
                mensaje=f"Reorganización excesiva ({bloques_a_reorg} > {ConfigForkResolver.MAX_REORGANIZACION})",
            )
        
        # Decidir por trabajo acumulado
        if trabajo_alt > trabajo_ppal:
            # Cadena alternativa gana
            self.total_reorganizaciones += 1
            self.bloques_reorganizados_total += bloques_a_reorg
            
            # Registrar fork
            rama = RamaAlternativa(
                id_rama=f"fork_{int(time.time())}",
                bloques=cadena_alternativa[fork_info["altura_fork"]:],
                trabajo_acumulado=trabajo_alt,
                altura=fork_info["altura_fork"],
                timestamp_deteccion=int(time.time()),
                resuelta=True,
                ganadora=True,
            )
            self.forks_historial.append(rama)
            
            return ResultadoFork(
                hubo_fork=True,
                hubo_reorganizacion=True,
                bloques_reorganizados=bloques_a_reorg,
                cadena_ganadora="alternativa",
                trabajo_principal=trabajo_ppal,
                trabajo_alternativa=trabajo_alt,
                mensaje=f"Adoptando cadena alternativa (+{bloques_a_reorg} bloques, más trabajo)",
                detalles={
                    "altura_fork": fork_info["altura_fork"],
                    "bloques_desechados": len(cadena_principal) - fork_info["altura_fork"],
                    "bloques_adoptados": bloques_a_reorg,
                }
            )
        else:
            # Cadena principal se mantiene
            rama = RamaAlternativa(
                id_rama=f"fork_{int(time.time())}",
                bloques=cadena_alternativa[fork_info["altura_fork"]:],
                trabajo_acumulado=trabajo_alt,
                altura=fork_info["altura_fork"],
                timestamp_deteccion=int(time.time()),
                resuelta=True,
                ganadora=False,
            )
            self.forks_historial.append(rama)
            
            return ResultadoFork(
                hubo_fork=True,
                hubo_reorganizacion=False,
                bloques_reorganizados=0,
                cadena_ganadora="principal",
                trabajo_principal=trabajo_ppal,
                trabajo_alternativa=trabajo_alt,
                mensaje="Manteniendo cadena principal (más trabajo acumulado)",
            )
    
    def calcular_mejor_cadena(self, cadenas: List[List[dict]]) -> Tuple[int, List[dict]]:
        """
        Dada una lista de cadenas candidatas, elige la mejor.
        
        Returns:
            (indice_ganador, cadena_ganadora)
        """
        if not cadenas:
            return -1, []
        
        mejor_indice = 0
        mejor_trabajo = 0
        
        for i, cadena in enumerate(cadenas):
            if not self.es_cadena_valida(cadena):
                continue
            trabajo = self.calcular_trabajo_acumulado(cadena)
            if trabajo > mejor_trabajo:
                mejor_trabajo = trabajo
                mejor_indice = i
        
        return mejor_indice, cadenas[mejor_indice] if cadenas else []
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Devuelve estadísticas del resolvedor de forks."""
        return {
            "total_reorganizaciones": self.total_reorganizaciones,
            "bloques_reorganizados_total": self.bloques_reorganizados_total,
            "forks_detectados": len(self.forks_historial),
            "forks_ganados_por_alternativa": sum(1 for f in self.forks_historial if f.ganadora),
            "ultimo_fork": self.forks_historial[-1].__dict__ if self.forks_historial else None,
        }
    
    def limpiar_historial(self):
        """Limpia el historial manteniendo los últimos forks."""
        if len(self.forks_historial) > ConfigForkResolver.MAX_FORKS_REGISTRADOS:
            self.forks_historial = self.forks_historial[-ConfigForkResolver.MAX_FORKS_REGISTRADOS:]


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoForkResolver:
    def __init__(self):
        self.ok = 0
        self.fail = 0
    
    def _t(self, n, ok, d=""):
        s = "✅" if ok else "❌"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    
    def _crear_bloque(self, indice: int, hash_previo: str, hash_propio: str, 
                      dificultad: int = 1) -> dict:
        return {
            "indice": indice,
            "hash_previo": hash_previo,
            "hash": hash_propio,
            "dificultad": dificultad,
            "timestamp": 1000000 + indice * 8,
        }
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE CONSENSO/FORK_RESOLVER.PY")
        print("=" * 70)
        
        resolver = ForkResolver()
        
        # Construir cadena principal
        principal = [self._crear_bloque(0, "0"*64, "genesis_hash")]
        for i in range(1, 6):
            principal.append(self._crear_bloque(i, principal[-1]["hash"], f"ppal_hash_{i}"))
        
        # Construir cadena alternativa (fork en bloque 3)
        alternativa = principal[:3].copy()
        for i in range(3, 7):
            alternativa.append(self._crear_bloque(i, alternativa[-1]["hash"], f"alt_hash_{i}", dificultad=2))
        
        # 1. Detectar fork
        fork_info = resolver.detectar_fork(principal, alternativa)
        self._t("Detectar fork", fork_info is not None and fork_info["indice_fork"] == 3,
                f"Fork en altura {fork_info['altura_fork']}" if fork_info else "No detectado")
        
        # 2. Cadenas idénticas no tienen fork
        fork_info2 = resolver.detectar_fork(principal, principal)
        self._t("Cadenas idénticas: sin fork", fork_info2 is None)
        
        # 3. Calcular trabajo acumulado
        trabajo_ppal = resolver.calcular_trabajo_acumulado(principal)
        trabajo_alt = resolver.calcular_trabajo_acumulado(alternativa)
        self._t("Trabajo alternativa > principal (más dificultad)",
                trabajo_alt > trabajo_ppal,
                f"Ppal: {trabajo_ppal}, Alt: {trabajo_alt}")
        
        # 4. Validar cadena
        self._t("Cadena principal válida", resolver.es_cadena_valida(principal))
        
        # 5. Cadena rota no válida
        cadena_rota = principal[:2] + [self._crear_bloque(2, "hash_falso", "hash_roto")]
        self._t("Cadena rota detectada", not resolver.es_cadena_valida(cadena_rota))
        
        # 6. Resolver fork a favor de alternativa
        resultado = resolver.resolver(principal, alternativa)
        self._t("Alternativa gana (más trabajo)", 
                resultado.hubo_reorganizacion and resultado.cadena_ganadora == "alternativa",
                resultado.mensaje[:40])
        
        # 7. Resolver fork a favor de principal
        resultado2 = resolver.resolver(alternativa, principal)
        self._t("Principal se mantiene", 
                not resultado2.hubo_reorganizacion)
        
        # 8. Elegir mejor cadena entre varias
        mejor_idx, mejor = resolver.calcular_mejor_cadena([principal, alternativa])
        self._t("Mejor cadena es la alternativa", mejor_idx == 1)
        
        # 9. Estadísticas
        stats = resolver.obtener_estadisticas()
        self._t("Estadísticas disponibles", stats["total_reorganizaciones"] >= 1)
        
        # 10. Límite de reorganización
        self._t("Max reorganización = 100", ConfigForkResolver.MAX_REORGANIZACION == 100)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ CONSENSO/FORK_RESOLVER.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🔄 " * 35)
    print("DIRECCOIN - FORK RESOLVER v1.0.0")
    print("🔄 " * 35)
    print(f"Max reorganización: {ConfigForkResolver.MAX_REORGANIZACION} bloques\n")
    
    diag = DiagnosticoForkResolver()
    if diag.ejecutar():
        print("📋 DEMO:")
        resolver = ForkResolver()
        stats = resolver.obtener_estadisticas()
        print(f"   Reorganizaciones: {stats['total_reorganizaciones']}")
        print(f"   Bloques reorganizados: {stats['bloques_reorganizados_total']}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()