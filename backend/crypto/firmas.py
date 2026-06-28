#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - FIRMAS DIGITALES                             ║
║                    Versión: 1.0.1 | Archivo: crypto/firmas.py              ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE FIRMAS DIGITALES PARA DIRECCOIN.
ECDSA sobre curva secp256k1 con nonces deterministas RFC 6979.
"""

import hashlib
import hmac
import os
from typing import Tuple, Optional

class ConfigFirmas:
    CURVA = "secp256k1"
    VERSION = "1.0.1"
    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


class _Hash:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    @staticmethod
    def hmac(k: bytes, m: bytes) -> bytes:
        return hmac.new(k, m, hashlib.sha3_256).digest()


class CurvaEliptica:
    P = ConfigFirmas.P
    N = ConfigFirmas.N
    G = (ConfigFirmas.Gx, ConfigFirmas.Gy)
    
    @staticmethod
    def inv(a: int, m: int) -> int:
        return pow(a, -1, m)
    
    @staticmethod
    def suma(p: Tuple[int, int], q: Tuple[int, int]) -> Tuple[int, int]:
        if p == (0, 0): return q
        if q == (0, 0): return p
        P = CurvaEliptica.P
        if p[0] == q[0]:
            if p[1] != q[1]: return (0, 0)
            lam = (3 * p[0] * p[0] * CurvaEliptica.inv(2 * p[1], P)) % P
        else:
            lam = ((q[1] - p[1]) * CurvaEliptica.inv(q[0] - p[0], P)) % P
        x = (lam * lam - p[0] - q[0]) % P
        y = (lam * (p[0] - x) - p[1]) % P
        return (x, y)
    
    @staticmethod
    def mult(k: int, p: Tuple[int, int]) -> Tuple[int, int]:
        if k == 0 or k >= CurvaEliptica.N:
            raise ValueError("Escalar fuera de rango")
        res = (0, 0)
        act = p
        while k:
            if k & 1: res = CurvaEliptica.suma(res, act)
            act = CurvaEliptica.suma(act, act)
            k >>= 1
        return res
    
    @staticmethod
    def en_curva(p: Tuple[int, int]) -> bool:
        if p == (0, 0): return True
        x, y = p
        return (y * y - x * x * x - 7) % CurvaEliptica.P == 0


class GeneradorNonceRFC6979:
    @staticmethod
    def generar(clave: int, hash_msg: bytes) -> int:
        clave_b = clave.to_bytes(32, 'big')
        V = b'\x01' * 32
        K = b'\x00' * 32
        K = _Hash.hmac(K, V + b'\x00' + clave_b + hash_msg)
        V = _Hash.hmac(K, V)
        K = _Hash.hmac(K, V + b'\x01' + clave_b + hash_msg)
        V = _Hash.hmac(K, V)
        while True:
            T = b''
            while len(T) < 32:
                V = _Hash.hmac(K, V)
                T += V
            nonce = int.from_bytes(T[:32], 'big')
            if 1 <= nonce < CurvaEliptica.N:
                return nonce
            K = _Hash.hmac(K, V + b'\x00')
            V = _Hash.hmac(K, V)


class FirmaECDSA:
    
    @staticmethod
    def generar_par_claves() -> Tuple[int, Tuple[int, int]]:
        while True:
            entropia = os.urandom(32)
            priv = int.from_bytes(entropia, 'big') % (CurvaEliptica.N - 1)
            if priv >= 1: break
        pub = CurvaEliptica.mult(priv, CurvaEliptica.G)
        return priv, pub
    
    @staticmethod
    def firmar(mensaje: bytes, clave_privada: int) -> Tuple[int, int]:
        if clave_privada < 1 or clave_privada >= CurvaEliptica.N:
            raise ValueError("Clave privada inválida")
        z = int.from_bytes(_Hash.sha3(mensaje), 'big')
        k = GeneradorNonceRFC6979.generar(clave_privada, _Hash.sha3(mensaje))
        R = CurvaEliptica.mult(k, CurvaEliptica.G)
        r = R[0] % CurvaEliptica.N
        if r == 0: raise ValueError("r=0")
        k_inv = CurvaEliptica.inv(k, CurvaEliptica.N)
        s = (k_inv * (z + r * clave_privada)) % CurvaEliptica.N
        if s == 0: raise ValueError("s=0")
        if s > CurvaEliptica.N // 2:
            s = CurvaEliptica.N - s
        return (r, s)
    
    @staticmethod
    def verificar(mensaje: bytes, firma: Tuple[int, int], pub: Tuple[int, int]) -> bool:
        r, s = firma
        if r < 1 or r >= CurvaEliptica.N or s < 1 or s >= CurvaEliptica.N:
            return False
        if not CurvaEliptica.en_curva(pub) or pub == (0, 0):
            return False
        z = int.from_bytes(_Hash.sha3(mensaje), 'big')
        w = CurvaEliptica.inv(s, CurvaEliptica.N)
        u1 = (z * w) % CurvaEliptica.N
        u2 = (r * w) % CurvaEliptica.N
        p1 = CurvaEliptica.mult(u1, CurvaEliptica.G)
        p2 = CurvaEliptica.mult(u2, pub)
        p = CurvaEliptica.suma(p1, p2)
        return p != (0, 0) and (p[0] % CurvaEliptica.N) == r
    
    @staticmethod
    def firmar_transaccion(tx: dict, clave_privada: int) -> bytes:
        msg = f"{tx.get('version',1)}{tx.get('origen','')}{tx.get('destino','')}{tx.get('cantidad',0)}{tx.get('timestamp',0)}{tx.get('nonce',0)}".encode()
        r, s = FirmaECDSA.firmar(msg, clave_privada)
        return FirmaECDSA._der(r, s)
    
    @staticmethod
    def _der(r: int, s: int) -> bytes:
        def _enc(n):
            b = n.to_bytes((n.bit_length()+7)//8, 'big')
            if b[0] & 0x80: b = b'\x00' + b
            return b'\x02' + bytes([len(b)]) + b
        seq = _enc(r) + _enc(s)
        return b'\x30' + bytes([len(seq)]) + seq
    
    @staticmethod
    def recuperar_clave(mensaje: bytes, firma: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """EXPERIMENTAL: Recupera clave pública desde firma."""
        r, s = firma
        if r < 1 or r >= CurvaEliptica.N or s < 1 or s >= CurvaEliptica.N:
            return None
        z = int.from_bytes(_Hash.sha3(mensaje), 'big')
        y2 = (r**3 + 7) % CurvaEliptica.P
        y = pow(y2, (CurvaEliptica.P + 1) // 4, CurvaEliptica.P)
        R = (r, y if y % 2 == 0 else CurvaEliptica.P - y)
        r_inv = CurvaEliptica.inv(r, CurvaEliptica.N)
        sR = CurvaEliptica.mult(s, R)
        zG = CurvaEliptica.mult(z, CurvaEliptica.G)
        zG_neg = (zG[0], CurvaEliptica.P - zG[1])
        punto = CurvaEliptica.suma(sR, zG_neg)
        pub = CurvaEliptica.mult(r_inv, punto)
        return pub if CurvaEliptica.en_curva(pub) else None


class DiagnosticoFirmas:
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
        print("🔍 DIAGNÓSTICO DE CRYPTO/FIRMAS.PY")
        print("=" * 70)
        
        priv, pub = FirmaECDSA.generar_par_claves()
        self._t("Generar par de claves", len(str(priv)) > 10 and pub != (0,0))
        self._t("Clave pública en curva", CurvaEliptica.en_curva(pub))
        
        msg = b"Direccoin test message"
        firma = FirmaECDSA.firmar(msg, priv)
        self._t("Firma generada", len(firma) == 2)
        
        self._t("Verificar firma válida", FirmaECDSA.verificar(msg, firma, pub))
        self._t("Rechazar mensaje falso", not FirmaECDSA.verificar(b"fake", firma, pub))
        
        priv2, pub2 = FirmaECDSA.generar_par_claves()
        self._t("Rechazar clave ajena", not FirmaECDSA.verificar(msg, firma, pub2))
        
        self._t("Nonce determinista", FirmaECDSA.firmar(msg, priv) == firma)
        self._t("Nonce diferente", FirmaECDSA.firmar(b"otro", priv) != firma)
        
        der = FirmaECDSA._der(firma[0], firma[1])
        self._t("Codificar DER", len(der) > 10)
        
        tx = {"version":1,"origen":"drcA","destino":"drcB","cantidad":100,"timestamp":123,"nonce":1}
        der_tx = FirmaECDSA.firmar_transaccion(tx, priv)
        self._t("Firmar transacción", len(der_tx) > 10)
        
        pub_rec = FirmaECDSA.recuperar_clave(msg, firma)
        self._t("Recuperar clave (exp)", pub_rec is not None and CurvaEliptica.en_curva(pub_rec),
                "OK" if pub_rec else "N/A")
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0:
            print("✅ CRYPTO/FIRMAS.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "🔑 " * 35)
    print("DIRECCOIN - FIRMAS DIGITALES v1.0.1")
    print("🔑 " * 35)
    print(f"Curva: {ConfigFirmas.CURVA}\n")
    diag = DiagnosticoFirmas()
    if diag.ejecutar():
        priv, pub = FirmaECDSA.generar_par_claves()
        print("📋 DEMO:")
        print(f"   Clave pública X: {hex(pub[0])[:32]}...")
        f = FirmaECDSA.firmar(b"Direccoin", priv)
        print(f"   Firma r: {hex(f[0])[:32]}...")
        print(f"   Verificación: {'✅' if FirmaECDSA.verificar(b'Direccoin', f, pub) else '❌'}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()