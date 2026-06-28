#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - CADENA DE BLOQUES                            ║
║                    Versión: 1.0.2 | Archivo: core/cadena.py                ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO CENTRAL DE LA BLOCKCHAIN DIRECCOIN.
Autocontenido: no depende de otros módulos del proyecto.
"""

import hashlib
import time
import os
import json
from typing import Dict, List, Optional, Tuple

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigCadena:
    VERSION = "1.0.2"
    VERSION_BLOQUE = 1
    TIEMPO_OBJETIVO = 8
    DIFICULTAD_INICIAL = 1
    MAX_TRANSACCIONES_POR_BLOQUE = 5_000
    TAMANO_MAX_BLOQUE_BYTES = 4_194_304
    CONFIRMACIONES_SEGURAS = 6
    PREFIJO_HASH_OBJETIVO = "d1"
    DECIMALES = 6
    SUMINISTRO_TOTAL = 100_000_000
    PREMINE_TOTAL = 3_000_000
    RECOMPENSA_INICIAL = 100_000_000
    BLOQUES_POR_AÑO = 97_000
    REDUCCION_ANUAL = 0.90


# ==============================================================================
# UTILIDADES DE HASH
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    
    @staticmethod
    def doble(d: bytes) -> bytes:
        return HashUtil.sha3(HashUtil.sha3(d))
    
    @staticmethod
    def sha3_hex(d: bytes) -> str:
        return HashUtil.sha3(d).hex()
    
    @staticmethod
    def doble_hex(d: bytes) -> str:
        return HashUtil.doble(d).hex()
    
    @staticmethod
    def hex_a_bytes(h: str) -> bytes:
        return bytes.fromhex(h)
    
    @staticmethod
    def bytes_a_hex(b: bytes) -> str:
        return b.hex()


class MerkleTree:
    def __init__(self, hojas: List[bytes]):
        if not hojas:
            raise ValueError("Merkle Tree requiere al menos una hoja")
        self.hojas = hojas
        self.hashes = [HashUtil.doble(h) for h in hojas]
        self.raiz = self._construir(self.hashes)
    
    def _hash_par(self, a: bytes, b: bytes) -> bytes:
        return HashUtil.doble(a + b if a < b else b + a)
    
    def _construir(self, nivel: List[bytes]) -> bytes:
        while len(nivel) > 1:
            sig = []
            for i in range(0, len(nivel), 2):
                if i + 1 < len(nivel):
                    sig.append(self._hash_par(nivel[i], nivel[i + 1]))
                else:
                    sig.append(self._hash_par(nivel[i], nivel[i]))
            nivel = sig
        return nivel[0]


# ==============================================================================
# TRANSACCIÓN
# ==============================================================================

class Transaccion:
    def __init__(self, origen: str, destino: str, cantidad: int,
                 timestamp: Optional[int] = None, nonce: int = 0):
        self.version = 1
        self.origen = origen
        self.destino = destino
        self.cantidad = cantidad
        self.timestamp = timestamp or int(time.time())
        self.nonce = nonce
        self.firma = ""
        self.txid = self._calcular_txid()
    
    def _calcular_txid(self) -> str:
        contenido = f"{self.version}{self.origen}{self.destino}{self.cantidad}{self.timestamp}{self.nonce}".encode()
        return HashUtil.sha3_hex(contenido)
    
    def es_valida(self) -> Tuple[bool, str]:
        if self.cantidad <= 0:
            return False, "Cantidad debe ser positiva"
        if self.origen == self.destino:
            return False, "No se puede enviar a la misma dirección"
        if not self.origen.startswith("drc"):
            return False, "Origen inválido"
        if not self.destino.startswith("drc"):
            return False, "Destino inválido"
        return True, "Válida"
    
    def a_dict(self) -> dict:
        return {
            "version": self.version,
            "origen": self.origen,
            "destino": self.destino,
            "cantidad": self.cantidad,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "firma": self.firma,
            "txid": self.txid,
        }
    
    @classmethod
    def desde_dict(cls, datos: dict) -> 'Transaccion':
        tx = cls(
            origen=datos["origen"],
            destino=datos["destino"],
            cantidad=datos["cantidad"],
            timestamp=datos.get("timestamp"),
            nonce=datos.get("nonce", 0)
        )
        tx.firma = datos.get("firma", "")
        tx.txid = datos.get("txid", tx._calcular_txid())
        return tx


# ==============================================================================
# BLOQUE
# ==============================================================================

class Bloque:
    def __init__(self, indice: int, hash_previo: str,
                 transacciones: List[Transaccion] = None,
                 timestamp: Optional[int] = None,
                 dificultad: int = ConfigCadena.DIFICULTAD_INICIAL):
        self.version = ConfigCadena.VERSION_BLOQUE
        self.indice = indice
        self.hash_previo = hash_previo
        self.timestamp = timestamp or int(time.time())
        self.transacciones = transacciones or []
        self.nonce = 0
        self.dificultad = dificultad
        self.merkle_raiz = b'\x00' * 32
        self.hash = ""
        self._actualizar_merkle()
    
    def _actualizar_merkle(self):
        if not self.transacciones:
            self.merkle_raiz = b'\x00' * 32
            return
        hojas = [tx.txid.encode() for tx in self.transacciones]
        self.merkle_raiz = MerkleTree(hojas).raiz
    
    def agregar_transaccion(self, tx: Transaccion):
        if len(self.transacciones) >= ConfigCadena.MAX_TRANSACCIONES_POR_BLOQUE:
            raise ValueError("Límite de transacciones alcanzado")
        self.transacciones.append(tx)
        self._actualizar_merkle()
    
    def minar(self) -> str:
        self._actualizar_merkle()
        merkle_hex = HashUtil.bytes_a_hex(self.merkle_raiz)
        
        for nonce in range(2**24):
            contenido = f"{self.version}{self.indice}{self.hash_previo}{self.timestamp}{self.dificultad}{nonce}{merkle_hex}".encode()
            h = HashUtil.doble_hex(contenido)
            if h.startswith(ConfigCadena.PREFIJO_HASH_OBJETIVO):
                self.nonce = nonce
                self.hash = h
                return h
        
        self.nonce = 2**24 - 1
        contenido = f"{self.version}{self.indice}{self.hash_previo}{self.timestamp}{self.dificultad}{self.nonce}{merkle_hex}".encode()
        self.hash = HashUtil.doble_hex(contenido)
        return self.hash
    
    def es_valido(self, bloque_anterior: Optional['Bloque'] = None) -> Tuple[bool, str]:
        # Validar hash previo e índice
        if self.indice == 0:
            if self.hash_previo != "0" * 64:
                return False, "Génesis debe tener hash_previo = 0"
        else:
            if bloque_anterior is None:
                return False, "Se requiere bloque anterior"
            if self.hash_previo != bloque_anterior.hash:
                return False, f"Hash previo no coincide"
            if self.indice != bloque_anterior.indice + 1:
                return False, f"Índice {self.indice} != {bloque_anterior.indice + 1}"
        
        # Validar timestamp (solo si hay bloque anterior)
        if self.indice > 0 and bloque_anterior is not None:
            if self.timestamp < bloque_anterior.timestamp:
                return False, "Timestamp anterior al bloque previo"
        
        # Validar Merkle
        if self.transacciones:
            hojas = [tx.txid.encode() for tx in self.transacciones]
            raiz_calculada = MerkleTree(hojas).raiz
            if raiz_calculada != self.merkle_raiz:
                return False, "Merkle incorrecto"
        else:
            if self.merkle_raiz != b'\x00' * 32:
                return False, "Merkle debe ser cero sin transacciones"
        
        # Validar hash minado
        merkle_hex = HashUtil.bytes_a_hex(self.merkle_raiz)
        contenido = f"{self.version}{self.indice}{self.hash_previo}{self.timestamp}{self.dificultad}{self.nonce}{merkle_hex}".encode()
        hash_esperado = HashUtil.doble_hex(contenido)
        if hash_esperado != self.hash:
            return False, "Hash incorrecto"
        
        return True, "Válido"
    
    def a_dict(self) -> dict:
        return {
            "version": self.version,
            "indice": self.indice,
            "hash_previo": self.hash_previo,
            "timestamp": self.timestamp,
            "dificultad": self.dificultad,
            "nonce": self.nonce,
            "merkle_raiz": HashUtil.bytes_a_hex(self.merkle_raiz),
            "hash": self.hash,
            "transacciones": [tx.a_dict() for tx in self.transacciones],
        }
    
    @classmethod
    def desde_dict(cls, datos: dict) -> 'Bloque':
        bloque = cls(
            indice=datos["indice"],
            hash_previo=datos["hash_previo"],
            timestamp=datos.get("timestamp"),
            dificultad=datos.get("dificultad", ConfigCadena.DIFICULTAD_INICIAL)
        )
        bloque.nonce = datos.get("nonce", 0)
        bloque.hash = datos.get("hash", "")
        bloque.merkle_raiz = HashUtil.hex_a_bytes(datos.get("merkle_raiz", "00" * 32))
        bloque.transacciones = [Transaccion.desde_dict(tx) for tx in datos.get("transacciones", [])]
        return bloque


# ==============================================================================
# CADENA DE BLOQUES
# ==============================================================================

class CadenaBloques:
    def __init__(self):
        self.bloques: List[Bloque] = []
    
    @property
    def ultimo_bloque(self) -> Optional[Bloque]:
        return self.bloques[-1] if self.bloques else None
    
    @property
    def altura(self) -> int:
        return len(self.bloques) - 1
    
    def agregar_genesis(self, genesis: Bloque):
        if self.bloques:
            raise ValueError("Ya existe génesis")
        if genesis.indice != 0:
            raise ValueError("Índice debe ser 0")
        ok, msg = genesis.es_valido()
        if not ok:
            raise ValueError(f"Génesis inválido: {msg}")
        self.bloques.append(genesis)
    
    def crear_bloque(self, transacciones: List[Transaccion] = None) -> Bloque:
        if not self.bloques:
            raise ValueError("Sin génesis")
        return Bloque(
            indice=len(self.bloques),
            hash_previo=self.ultimo_bloque.hash,
            transacciones=transacciones or [],
            dificultad=ConfigCadena.DIFICULTAD_INICIAL
        )
    
    def agregar_bloque(self, bloque: Bloque) -> Tuple[bool, str]:
        anterior = self.ultimo_bloque
        
        # Validar enlace con la cadena
        if anterior:
            if bloque.indice != anterior.indice + 1:
                return False, f"Índice {bloque.indice} != {anterior.indice + 1}"
            if bloque.hash_previo != anterior.hash:
                return False, "Hash previo no enlaza con la cadena"
        
        # Validar el bloque en sí
        valido, msg = bloque.es_valido(anterior)
        if not valido:
            return False, msg
        
        # Validar transacciones
        for tx in bloque.transacciones:
            ok, msg = tx.es_valida()
            if not ok:
                return False, f"Transacción inválida: {msg}"
        
        self.bloques.append(bloque)
        return True, "Añadido"
    
    def validar(self) -> Tuple[bool, str]:
        if not self.bloques:
            return False, "Vacía"
        for i, bloque in enumerate(self.bloques):
            anterior = self.bloques[i - 1] if i > 0 else None
            ok, msg = bloque.es_valido(anterior)
            if not ok:
                return False, f"Bloque {i}: {msg}"
        return True, "Válida"
    
    def trabajo_acumulado(self) -> int:
        return sum(b.dificultad for b in self.bloques)
    
    def estadisticas(self) -> dict:
        if not self.bloques:
            return {"altura": 0, "bloques": 0}
        return {
            "altura": self.altura,
            "bloques": len(self.bloques),
            "hash_ultimo": (self.ultimo_bloque.hash[:16] + "...") if self.ultimo_bloque else "",
            "trabajo": self.trabajo_acumulado(),
            "valida": self.validar()[0],
        }


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoCadena:
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
        print("🔍 DIAGNÓSTICO DE CORE/CADENA.PY")
        print("=" * 70)
        
        # 1. Bloque génesis
        genesis = Bloque(0, "0" * 64)
        genesis.minar()
        ok, msg = genesis.es_valido()
        self._t("Génesis válido", ok, msg[:20])
        
        # 2. Transacción
        tx = Transaccion("drcA1111111111111111111111111111111", 
                         "drcB2222222222222222222222222222222", 1_000_000)
        self._t("TX creada", len(tx.txid) == 64)
        
        # 3. TX válida
        ok, _ = tx.es_valida()
        self._t("TX válida", ok)
        
        # 4. Rechazar auto-envío
        tx_m = Transaccion("drcA", "drcA", 100)
        ok, _ = tx_m.es_valida()
        self._t("Rechazar auto-envío", not ok)
        
        # 5. Rechazar cantidad negativa
        tx_m2 = Transaccion("drcA", "drcB", -100)
        ok, _ = tx_m2.es_valida()
        self._t("Rechazar negativo", not ok)
        
        # 6. Bloque 1 con tx
        b1 = Bloque(1, genesis.hash, [tx])
        b1.minar()
        ok, msg = b1.es_valido(genesis)
        self._t("Bloque 1 válido", ok, msg[:20])
        
        # 7. Cadena
        c = CadenaBloques()
        c.agregar_genesis(genesis)
        self._t("Añadir génesis", c.altura == 0)
        
        # 8. Agregar bloque a cadena
        ok, msg = c.agregar_bloque(b1)
        self._t("Agregar bloque a cadena", ok, msg[:20])
        
        # 9. Cadena completa válida
        ok, msg = c.validar()
        self._t("Cadena válida", ok)
        
        # 10. Rechazar índice malo
        b_malo = Bloque(5, b1.hash)
        ok, _ = b_malo.es_valido(b1)
        self._t("Rechazar índice incorrecto", not ok)
        
        # 11. Serialización
        d = b1.a_dict()
        b2 = Bloque.desde_dict(d)
        self._t("Serializar/Deserializar", b2.hash == b1.hash)
        
        # 12. Merkle 5 tx
        txs = [Transaccion("drcA", "drcB", i * 100) for i in range(1, 6)]
        b_tx = Bloque(2, b1.hash, txs)
        self._t("Merkle 5 tx", len(b_tx.merkle_raiz) == 32)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0:
            print("✅ CORE/CADENA.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "⛓️ " * 35)
    print("DIRECCOIN - CADENA DE BLOQUES v1.0.2")
    print("⛓️ " * 35)
    print(f"Versión: {ConfigCadena.VERSION}")
    print(f"Bloques: {ConfigCadena.TIEMPO_OBJETIVO}s objetivo")
    print(f"Max TX/bloque: {ConfigCadena.MAX_TRANSACCIONES_POR_BLOQUE}\n")
    
    diag = DiagnosticoCadena()
    if diag.ejecutar():
        genesis = Bloque(0, "0" * 64)
        genesis.minar()
        print("📋 DEMO:")
        print(f"   Génesis: {genesis.hash[:24]}...")
        print(f"   Nonce: {genesis.nonce}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()