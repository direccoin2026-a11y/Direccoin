#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - UTILIDADES DE HASH                           ║
║                    Versión: 1.0.1 | Archivo: crypto/hash_utils.py           ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO FUNDACIONAL DE CRIPTOGRAFÍA PARA DIRECCOIN.
"""

import hashlib
import hmac
import os
import struct
from typing import List, Tuple, Optional, Iterator

class ConfigHash:
    ALGORITMO_PRIMARIO = "sha3_256"
    TAMANO_HASH_BYTES = 32
    TAMANO_HASH_HEX = 64
    PREFIJO_DIRECCOIN = b"Direccoin"
    VERSION = "1.0.1"


class HashUtil:
    
    @staticmethod
    def sha3_256(datos: bytes) -> bytes:
        return hashlib.sha3_256(datos).digest()
    
    @staticmethod
    def sha3_256_hex(datos: bytes) -> str:
        return HashUtil.sha3_256(datos).hex()
    
    @staticmethod
    def sha3_512(datos: bytes) -> bytes:
        return hashlib.sha3_512(datos).digest()
    
    @staticmethod
    def doble_sha3_256(datos: bytes) -> bytes:
        return HashUtil.sha3_256(HashUtil.sha3_256(datos))
    
    @staticmethod
    def doble_sha3_256_hex(datos: bytes) -> str:
        return HashUtil.doble_sha3_256(datos).hex()
    
    @staticmethod
    def hash_con_sal(datos: bytes, sal: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        if sal is None:
            sal = os.urandom(32)
        return HashUtil.sha3_256(sal + datos), sal
    
    @staticmethod
    def hmac_sha3_256(clave: bytes, mensaje: bytes) -> bytes:
        return hmac.new(clave, mensaje, hashlib.sha3_256).digest()
    
    @staticmethod
    def hmac_sha3_256_hex(clave: bytes, mensaje: bytes) -> str:
        return HashUtil.hmac_sha3_256(clave, mensaje).hex()
    
    @staticmethod
    def hash_direccoin(datos: bytes, dominio: str = "") -> bytes:
        prefijo = ConfigHash.PREFIJO_DIRECCOIN + dominio.encode()
        return HashUtil.doble_sha3_256(prefijo + datos)
    
    @staticmethod
    def comparacion_segura(a: bytes, b: bytes) -> bool:
        if len(a) != len(b):
            return False
        resultado = 0
        for x, y in zip(a, b):
            resultado |= x ^ y
        return resultado == 0
    
    @staticmethod
    def bytes_a_hex(datos: bytes) -> str:
        return datos.hex()
    
    @staticmethod
    def hex_a_bytes(hex_str: str) -> bytes:
        return bytes.fromhex(hex_str)
    
    @staticmethod
    def int_a_bytes(numero: int, longitud: int = 32) -> bytes:
        return numero.to_bytes(longitud, 'big')
    
    @staticmethod
    def bytes_a_int(datos: bytes) -> int:
        return int.from_bytes(datos, 'big')
    
    @staticmethod
    def hash_stream(datos_iter: Iterator[bytes]) -> bytes:
        hasher = hashlib.sha3_256()
        for chunk in datos_iter:
            hasher.update(chunk)
        return hasher.digest()
    
    @staticmethod
    def prng_determinista(semilla: bytes, indice: int) -> int:
        datos = semilla + struct.pack("<Q", indice)
        hash_result = HashUtil.doble_sha3_256(datos)
        return int.from_bytes(hash_result[:8], 'little')
    
    @staticmethod
    def checksum(datos: bytes, longitud: int = 4) -> bytes:
        return HashUtil.doble_sha3_256(datos)[:longitud]
    
    @staticmethod
    def verificar_checksum(datos: bytes, checksum_esperado: bytes) -> bool:
        return HashUtil.comparacion_segura(
            HashUtil.checksum(datos, len(checksum_esperado)),
            checksum_esperado
        )


class MerkleTree:
    
    def __init__(self, hojas: List[bytes]):
        if not hojas:
            raise ValueError("Merkle Tree requiere al menos una hoja")
        self.hojas_originales = hojas
        self.hojas_hasheadas = [HashUtil.sha3_256(h) for h in hojas]
        self.raiz = self._construir(self.hojas_hasheadas)
    
    def _hash_par(self, a: bytes, b: bytes) -> bytes:
        if a < b:
            return HashUtil.sha3_256(a + b)
        return HashUtil.sha3_256(b + a)
    
    def _construir(self, nivel: List[bytes]) -> bytes:
        while len(nivel) > 1:
            siguiente = []
            for i in range(0, len(nivel), 2):
                if i + 1 < len(nivel):
                    siguiente.append(self._hash_par(nivel[i], nivel[i + 1]))
                else:
                    siguiente.append(self._hash_par(nivel[i], nivel[i]))
            nivel = siguiente
        return nivel[0]
    
    def obtener_prueba(self, indice: int) -> List[dict]:
        if indice < 0 or indice >= len(self.hojas_originales):
            raise ValueError(f"Índice fuera de rango: {indice}")
        
        prueba = []
        nivel = self.hojas_hasheadas[:]
        idx = indice
        
        while len(nivel) > 1:
            es_izquierdo = (idx % 2 == 0)
            if es_izquierdo and idx + 1 < len(nivel):
                prueba.append({"posicion": "derecha", "hash": nivel[idx + 1]})
            elif not es_izquierdo:
                prueba.append({"posicion": "izquierda", "hash": nivel[idx - 1]})
            else:
                prueba.append({"posicion": "izquierda", "hash": nivel[idx]})
            
            idx //= 2
            siguiente = []
            for i in range(0, len(nivel), 2):
                if i + 1 < len(nivel):
                    siguiente.append(self._hash_par(nivel[i], nivel[i + 1]))
                else:
                    siguiente.append(self._hash_par(nivel[i], nivel[i]))
            nivel = siguiente
        
        return prueba
    
    @staticmethod
    def verificar_prueba(prueba: List[dict], hash_hoja: bytes, raiz: bytes) -> bool:
        actual = hash_hoja
        for paso in prueba:
            if paso["posicion"] == "izquierda":
                actual = HashUtil.sha3_256(paso["hash"] + actual)
            else:
                actual = HashUtil.sha3_256(actual + paso["hash"])
        return HashUtil.comparacion_segura(actual, raiz)


class DiagnosticoHash:
    
    def __init__(self):
        self.pasados = 0
        self.fallidos = 0
    
    def _check(self, nombre: str, ok: bool, detalle: str = ""):
        estado = "✅ PASÓ" if ok else "❌ FALLÓ"
        print(f"   {estado} | {nombre}: {detalle}")
        if ok:
            self.pasados += 1
        else:
            self.fallidos += 1
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE CRYPTO/HASH_UTILS.PY")
        print("=" * 70)
        
        h = HashUtil.sha3_256(b"test")
        self._check("SHA3-256 produce 32 bytes", len(h) == 32)
        
        hx = HashUtil.sha3_256_hex(b"test")
        self._check("SHA3-256 hex: 64 caracteres", len(hx) == 64)
        
        h1, h2 = HashUtil.sha3_256(b"test"), HashUtil.sha3_256(b"test")
        self._check("Determinismo", h1 == h2)
        
        ht1, ht2 = HashUtil.sha3_256(b"test"), HashUtil.sha3_256(b"tesu")
        self._check("Efecto avalancha", ht1 != ht2)
        
        dh = HashUtil.doble_sha3_256(b"test")
        self._check("Doble SHA3-256: 32 bytes", len(dh) == 32)
        
        hm = HashUtil.hmac_sha3_256(b"clave", b"mensaje")
        self._check("HMAC-SHA3-256: 32 bytes", len(hm) == 32)
        
        h_sal1, sal1 = HashUtil.hash_con_sal(b"test")
        h_sal2, _ = HashUtil.hash_con_sal(b"test", sal1)
        self._check("Hash con sal", h_sal1 == h_sal2)
        
        self._check("Comparación segura: iguales", HashUtil.comparacion_segura(b"abc", b"abc"))
        self._check("Comparación segura: diferentes", not HashUtil.comparacion_segura(b"abc", b"abd"))
        
        ck = HashUtil.checksum(b"datos", 4)
        self._check("Checksum: 4 bytes", len(ck) == 4)
        self._check("Verificar checksum", HashUtil.verificar_checksum(b"datos", ck))
        
        tree = MerkleTree([b"a", b"b", b"c"])
        self._check("Merkle Tree: raíz", len(tree.raiz) == 32)
        
        prueba = tree.obtener_prueba(0)
        hash_hoja = tree.hojas_hasheadas[0]
        valido = MerkleTree.verificar_prueba(prueba, hash_hoja, tree.raiz)
        self._check("Merkle: prueba inclusión", valido)
        
        n1 = HashUtil.prng_determinista(b"semilla", 0)
        n2 = HashUtil.prng_determinista(b"semilla", 0)
        n3 = HashUtil.prng_determinista(b"semilla", 1)
        self._check("PRNG determinista", n1 == n2)
        self._check("PRNG diferentes índices", n1 != n3)
        
        total = self.pasados + self.fallidos
        print("─" * 70)
        print(f"📊 {self.pasados}/{total} PASADOS | {self.fallidos} FALLIDOS")
        print("─" * 70)
        if self.fallidos == 0:
            print("✅ CRYPTO/HASH_UTILS.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fallidos == 0


def main():
    print("\n" + "#️⃣ " * 35)
    print("DIRECCOIN - HASH UTILS v1.0.1")
    print("#️⃣ " * 35)
    print(f"Algoritmo: {ConfigHash.ALGORITMO_PRIMARIO}\n")
    
    diag = DiagnosticoHash()
    if diag.ejecutar():
        print("📋 EJEMPLOS:")
        print(f"   SHA3-256: {HashUtil.sha3_256_hex(b'Direccoin')[:32]}...")
        print(f"   Doble: {HashUtil.doble_sha3_256_hex(b'Direccoin')[:32]}...")
        print(f"   HMAC: {HashUtil.hmac_sha3_256_hex(b'key', b'msg')[:32]}...")
        print(f"   Checksum: {HashUtil.checksum(b'Direccoin', 4).hex()}")
        print("\n🎯 LISTO\n")


if __name__ == "__main__":
    main()