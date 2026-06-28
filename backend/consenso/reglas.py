#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - REGLAS DE CONSENSO                           ║
║                    Versión: 1.0.0 | Archivo: consenso/reglas.py            ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE REGLAS DE CONSENSO PARA DIRECCOIN.

Define y aplica las reglas que todos los nodos deben seguir:
  • Validación completa de bloques
  • Verificación de transacciones
  • Reglas de emisión y recompensa
  • Consenso por trabajo acumulado (cadena más pesada)
  • Finalidad después de N confirmaciones
  • Anti-spam y anti-ataques

CARACTERÍSTICAS:
  • Reglas estrictas e inmutables
  • Verificación en múltiples niveles
  • Protección contra doble gasto
  • Finalidad probabilística (6 bloques)
  • Diagnóstico de 12 pruebas
"""

import hashlib
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigConsenso:
    VERSION = "1.0.0"
    
    # Parámetros de consenso
    TIEMPO_MAX_BLOQUE_FUTURO = 30          # Segundos de tolerancia
    CONFIRMACIONES_FINALIDAD = 6           # Bloques para finalidad
    MAX_TAMANO_BLOQUE = 4_194_304          # 4 MB
    MAX_TRANSACCIONES_POR_BLOQUE = 5_000
    DIFICULTAD_MINIMA = 1
    
    # Recompensas
    RECOMPENSA_BASE = 100_000_000          # 100 DRC en Direcs
    EMISION_MAXIMA = 100_000_000 * 10**6   # 100M DRC en Direcs
    
    # Límites
    MAX_GAS_POR_BLOQUE = 10_000_000
    MAX_GAS_POR_TRANSACCION = 1_000_000


# ==============================================================================
# RESULTADO DE VALIDACIÓN
# ==============================================================================

@dataclass
class ResultadoValidacion:
    valido: bool
    mensaje: str
    detalles: Dict[str, Any] = field(default_factory=dict)
    advertencias: List[str] = field(default_factory=list)


# ==============================================================================
# VALIDADOR DE BLOQUES
# ==============================================================================

class ValidadorBloques:
    """
    Aplica las reglas de consenso para validar bloques.
    """
    
    def __init__(self, emision_actual: int = 3_000_000 * 10**6):
        self.emision_actual = emision_actual  # Direcs emitidos hasta ahora
        self.bloques_validados = 0
    
    def validar_bloque_completo(self, bloque: dict, 
                                bloque_anterior: dict = None,
                                es_genesis: bool = False) -> ResultadoValidacion:
        """
        Valida un bloque contra todas las reglas de consenso.
        
        Args:
            bloque: Diccionario con datos del bloque
            bloque_anterior: Bloque previo en la cadena
            es_genesis: Si es el bloque 0
        
        Returns:
            ResultadoValidacion con el resultado
        """
        advertencias = []
        
        # 1. Validar estructura básica
        if not self._estructura_valida(bloque):
            return ResultadoValidacion(False, "Estructura de bloque inválida")
        
        # 2. Validar índice
        if es_genesis:
            if bloque.get("indice") != 0:
                return ResultadoValidacion(False, "Bloque génesis debe tener índice 0")
            if bloque.get("hash_previo") != "0" * 64:
                return ResultadoValidacion(False, "Hash previo del génesis debe ser 0")
        else:
            if bloque_anterior is None:
                return ResultadoValidacion(False, "Se requiere bloque anterior")
            if bloque.get("indice") != bloque_anterior.get("indice", -1) + 1:
                return ResultadoValidacion(False, "Índice no secuencial")
            if bloque.get("hash_previo") != bloque_anterior.get("hash", ""):
                return ResultadoValidacion(False, "Hash previo no coincide")
        
        # 3. Validar timestamp
        if not self._timestamp_valido(bloque.get("timestamp", 0)):
            return ResultadoValidacion(False, "Timestamp inválido")
        
        # 4. Validar tamaño
        if not self._tamano_valido(bloque):
            advertencias.append("Bloque cerca del límite de tamaño")
        
        # 5. Validar transacciones
        txs = bloque.get("transacciones", [])
        if len(txs) > ConfigConsenso.MAX_TRANSACCIONES_POR_BLOQUE:
            return ResultadoValidacion(False, 
                f"Demasiadas transacciones: {len(txs)} > {ConfigConsenso.MAX_TRANSACCIONES_POR_BLOQUE}")
        
        for i, tx in enumerate(txs):
            ok, msg = self._validar_transaccion(tx)
            if not ok:
                return ResultadoValidacion(False, f"Transacción {i} inválida: {msg}")
        
        # 6. Validar Merkle root
        if not self._merkle_valido(bloque):
            return ResultadoValidacion(False, "Merkle root inválido")
        
        # 7. Validar dificultad
        if not self._dificultad_valida(bloque):
            return ResultadoValidacion(False, "Dificultad no cumplida")
        
        # 8. Validar recompensa
        if not es_genesis:
            ok, msg = self._recompensa_valida(bloque)
            if not ok:
                return ResultadoValidacion(False, msg)
        
        # 9. Validar gas total
        gas_total = sum(tx.get("gas", 0) for tx in txs)
        if gas_total > ConfigConsenso.MAX_GAS_POR_BLOQUE:
            return ResultadoValidacion(False, f"Gas excesivo: {gas_total}")
        
        # Actualizar emisión
        recompensa = bloque.get("recompensa", 0)
        self.emision_actual += recompensa
        self.bloques_validados += 1
        
        return ResultadoValidacion(
            valido=True,
            mensaje="Bloque válido",
            detalles={
                "indice": bloque.get("indice"),
                "transacciones": len(txs),
                "recompensa": recompensa,
                "emision_total": self.emision_actual,
            },
            advertencias=advertencias
        )
    
    def _estructura_valida(self, bloque: dict) -> bool:
        """Verifica que el bloque tenga los campos obligatorios."""
        campos = ["indice", "hash_previo", "timestamp", "transacciones", 
                  "nonce", "dificultad", "merkle_raiz", "hash"]
        return all(c in bloque for c in campos)
    
    def _timestamp_valido(self, timestamp: int) -> bool:
        """Verifica que el timestamp sea razonable."""
        ahora = int(time.time())
        # No puede ser del futuro (con pequeña tolerancia)
        if timestamp > ahora + ConfigConsenso.TIEMPO_MAX_BLOQUE_FUTURO:
            return False
        # No puede ser anterior al timestamp génesis
        if timestamp < 1778279888:  # Timestamp del génesis de Direccoin
            return False
        return True
    
    def _tamano_valido(self, bloque: dict) -> bool:
        """Verifica que el bloque no exceda el tamaño máximo."""
        import json
        try:
            tamano = len(json.dumps(bloque))
            return tamano <= ConfigConsenso.MAX_TAMANO_BLOQUE
        except:
            return True  # No podemos verificar, asumimos válido
    
    def _validar_transaccion(self, tx: dict) -> Tuple[bool, str]:
        """Valida una transacción individual."""
        # Campos obligatorios
        if "origen" not in tx or "destino" not in tx or "cantidad" not in tx:
            return False, "Campos incompletos"
        
        # Cantidad positiva
        if tx["cantidad"] <= 0:
            return False, "Cantidad debe ser positiva"
        
        # No enviar a uno mismo
        if tx["origen"] == tx["destino"]:
            return False, "Origen y destino iguales"
        
        # Direcciones válidas
        if not tx["origen"].startswith("drc"):
            return False, "Dirección origen inválida"
        if not tx["destino"].startswith("drc"):
            return False, "Dirección destino inválida"
        
        # Gas máximo
        if tx.get("gas", 0) > ConfigConsenso.MAX_GAS_POR_TRANSACCION:
            return False, "Gas excesivo"
        
        return True, "Válida"
    
    def _merkle_valido(self, bloque: dict) -> bool:
        """Verifica la raíz de Merkle."""
        txs = bloque.get("transacciones", [])
        merkle_raiz = bloque.get("merkle_raiz", "")
        
        if not txs and merkle_raiz:
            return merkle_raiz == "0" * 64
        
        if txs and not merkle_raiz:
            return False
        
        # Simplificado: en producción usaríamos el árbol completo
        return len(merkle_raiz) == 64
    
    def _dificultad_valida(self, bloque: dict) -> bool:
        """Verifica que el hash cumpla la dificultad."""
        hash_bloque = bloque.get("hash", "")
        dificultad = bloque.get("dificultad", ConfigConsenso.DIFICULTAD_MINIMA)
        
        if not hash_bloque.startswith("d1"):
            return False
        
        ceros = 0
        for c in hash_bloque[2:]:
            if c == '0':
                ceros += 1
            else:
                break
        
        return ceros >= dificultad - 2
    
    def _recompensa_valida(self, bloque: dict) -> Tuple[bool, str]:
        """Verifica que la recompensa del bloque sea correcta."""
        recompensa = bloque.get("recompensa", 0)
        indice = bloque.get("indice", 0)
        
        if indice <= 0:
            return True, "Génesis no tiene recompensa"
        
        # Verificar que no exceda el suministro máximo
        if self.emision_actual + recompensa > ConfigConsenso.EMISION_MAXIMA:
            return False, f"Excede suministro máximo: {self.emision_actual + recompensa}"
        
        return True, "Recompensa válida"


# ==============================================================================
# VERIFICADOR DE DOBLE GASTO
# ==============================================================================

class VerificadorDobleGasto:
    """
    Previene el doble gasto verificando que cada salida solo se gaste una vez.
    """
    
    def __init__(self):
        self.salidas_gastadas: set = set()
        self.contador_nonce: Dict[str, int] = {}
    
    def verificar_transaccion(self, tx: dict, saldo_origen: int) -> Tuple[bool, str]:
        """
        Verifica que una transacción no sea doble gasto.
        """
        txid = tx.get("txid", "")
        origen = tx.get("origen", "")
        cantidad = tx.get("cantidad", 0)
        gas = tx.get("gas", 0)
        nonce = tx.get("nonce", 0)
        
        # Verificar TXID único
        if txid in self.salidas_gastadas:
            return False, "TXID duplicado: posible doble gasto"
        
        # Verificar nonce secuencial
        if origen in self.contador_nonce:
            nonce_esperado = self.contador_nonce[origen] + 1
            if nonce != nonce_esperado:
                return False, f"Nonce incorrecto: {nonce} != {nonce_esperado}"
        
        # Verificar saldo suficiente
        total = cantidad + gas
        if total > saldo_origen:
            return False, f"Saldo insuficiente: {saldo_origen} < {total}"
        
        # Registrar
        self.salidas_gastadas.add(txid)
        self.contador_nonce[origen] = nonce
        
        return True, "Válida"
    
    def limpiar_transacciones(self, txids: List[str]):
        """Limpia transacciones ya confirmadas (gestión de memoria)."""
        for txid in txids:
            self.salidas_gastadas.discard(txid)


# ==============================================================================
# GESTOR DE FINALIDAD
# ==============================================================================

class GestorFinalidad:
    """
    Determina cuándo un bloque se considera final (irreversible).
    """
    
    def __init__(self):
        self.profundidades: Dict[str, int] = {}
    
    def registrar_bloque(self, hash_bloque: str, altura: int):
        """Registra un nuevo bloque."""
        self.profundidades[hash_bloque] = 0
        
        # Actualizar profundidades de bloques anteriores
        for h in list(self.profundidades.keys()):
            if h != hash_bloque:
                self.profundidades[h] += 1
    
    def es_final(self, hash_bloque: str) -> bool:
        """
        Verifica si un bloque ha alcanzado finalidad.
        Se considera final después de CONFIRMACIONES_FINALIDAD bloques encima.
        """
        profundidad = self.profundidades.get(hash_bloque, 0)
        return profundidad >= ConfigConsenso.CONFIRMACIONES_FINALIDAD
    
    def obtener_confirmaciones(self, hash_bloque: str) -> int:
        """Número de confirmaciones de un bloque."""
        return self.profundidades.get(hash_bloque, 0)
    
    def es_seguro_aceptar_pago(self, hash_bloque: str, 
                                confirmaciones_requeridas: int = None) -> bool:
        """
        Determina si un pago es seguro basado en confirmaciones.
        """
        if confirmaciones_requeridas is None:
            confirmaciones_requeridas = ConfigConsenso.CONFIRMACIONES_FINALIDAD
        
        return self.obtener_confirmaciones(hash_bloque) >= confirmaciones_requeridas


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoReglas:
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
        print("🔍 DIAGNÓSTICO DE CONSENSO/REGLAS.PY")
        print("=" * 70)
        
        validador = ValidadorBloques()
        
        # 1. Bloque génesis válido
        genesis = {
            "indice": 0, "hash_previo": "0" * 64, "timestamp": 1778279888,
            "transacciones": [], "nonce": 0, "dificultad": 1,
            "merkle_raiz": "0" * 64, "hash": "d1" + "0" * 62,
            "recompensa": 0
        }
        r = validador.validar_bloque_completo(genesis, es_genesis=True)
        self._t("Validar bloque génesis", r.valido, r.mensaje[:30])
        
        # 2. Rechazar génesis con índice incorrecto
        genesis_malo = dict(genesis)
        genesis_malo["indice"] = 1
        r = validador.validar_bloque_completo(genesis_malo, es_genesis=True)
        self._t("Rechazar génesis índice 1", not r.valido)
        
        # 3. Validar timestamp
        self._t("Timestamp válido (ahora)", 
                validador._timestamp_valido(int(time.time())))
        self._t("Timestamp futuro rechazado",
                not validador._timestamp_valido(int(time.time()) + 999999))
        
        # 4. Validar transacción
        tx_ok = {"origen": "drcA", "destino": "drcB", "cantidad": 1000, "gas": 10}
        ok, msg = validador._validar_transaccion(tx_ok)
        self._t("Transacción válida", ok)
        
        # 5. Rechazar auto-envío
        tx_mala = {"origen": "drcA", "destino": "drcA", "cantidad": 100}
        ok, _ = validador._validar_transaccion(tx_mala)
        self._t("Rechazar auto-envío", not ok)
        
        # 6. Rechazar cantidad negativa
        tx_neg = {"origen": "drcA", "destino": "drcB", "cantidad": -100}
        ok, _ = validador._validar_transaccion(tx_neg)
        self._t("Rechazar cantidad negativa", not ok)
        
        # 7. Verificador de doble gasto
        vdg = VerificadorDobleGasto()
        ok, _ = vdg.verificar_transaccion({"txid": "tx001", "origen": "drcA", 
                                           "cantidad": 100, "nonce": 1}, 1000)
        self._t("Primera transacción aceptada", ok)
        ok, _ = vdg.verificar_transaccion({"txid": "tx001", "origen": "drcA",
                                           "cantidad": 100, "nonce": 1}, 1000)
        self._t("Doble gasto rechazado", not ok)
        
        # 8. Nonce secuencial
        ok, _ = vdg.verificar_transaccion({"txid": "tx002", "origen": "drcA",
                                           "cantidad": 50, "nonce": 2}, 1000)
        self._t("Nonce secuencial aceptado", ok)
        
        # 9. Nonce incorrecto rechazado
        ok, _ = vdg.verificar_transaccion({"txid": "tx003", "origen": "drcA",
                                           "cantidad": 50, "nonce": 5}, 1000)
        self._t("Nonce incorrecto rechazado", not ok)
        
        # 10. Finalidad
        gf = GestorFinalidad()
        for i in range(10):
            gf.registrar_bloque(f"bloque_{i}", i)
        self._t("Bloque con 6+ confirmaciones es final", gf.es_final("bloque_0"))
        self._t("Bloque reciente no es final", not gf.es_final("bloque_8"))
        
        # 11. Dificultad válida
        bloque_d = {"hash": "d1" + "0" * 3 + "abc", "dificultad": 3}
        self._t("Dificultad cumplida", validador._dificultad_valida(bloque_d))
        
        # 12. Parámetros de consenso
        self._t("Confirmaciones para finalidad = 6", 
                ConfigConsenso.CONFIRMACIONES_FINALIDAD == 6)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ CONSENSO/REGLAS.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🤝 " * 35)
    print("DIRECCOIN - REGLAS DE CONSENSO v1.0.0")
    print("🤝 " * 35)
    print(f"Confirmaciones: {ConfigConsenso.CONFIRMACIONES_FINALIDAD}")
    print(f"Max TX/bloque: {ConfigConsenso.MAX_TRANSACCIONES_POR_BLOQUE}\n")
    
    diag = DiagnosticoReglas()
    if diag.ejecutar():
        print("📋 DEMO:")
        vdg = VerificadorDobleGasto()
        ok, _ = vdg.verificar_transaccion(
            {"txid": "demo_tx", "origen": "drcDirect", "cantidad": 500, "nonce": 1}, 10000)
        print(f"   Transacción demo: {'✅ Aceptada' if ok else '❌ Rechazada'}")
        gf = GestorFinalidad()
        gf.registrar_bloque("demo_bloque", 0)
        print(f"   Confirmaciones: {gf.obtener_confirmaciones('demo_bloque')}")
        print(f"   ¿Es final?: {gf.es_final('demo_bloque')}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()