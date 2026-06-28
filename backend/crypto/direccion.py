#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - CODIFICADOR DE DIRECCIONES                   ║
║                    Versión: 1.0.3 | Archivo: crypto/direccion.py           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import os
from typing import Optional, Tuple, List

class ConfigDireccion:
    PREFIJO_PRINCIPAL = "drc"
    PREFIJO_TESTNET = "drct"
    VERSION_BYTES = b'\x00'
    CHECKSUM_BYTES = 4
    LONGITUD_MINIMA = 30
    LONGITUD_MAXIMA = 55
    VERSION = "1.0.3"


class _Hash:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    @staticmethod
    def doble(d: bytes) -> bytes:
        return _Hash.sha3(_Hash.sha3(d))


class Base58:
    ALFABETO = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    MAPA = {c: i for i, c in enumerate(ALFABETO)}
    
    @classmethod
    def codificar(cls, datos: bytes) -> str:
        ceros = 0
        for b in datos:
            if b == 0: ceros += 1
            else: break
        n = int.from_bytes(datos, 'big')
        res = []
        while n > 0:
            n, r = divmod(n, 58)
            res.append(cls.ALFABETO[r])
        res.extend(['1'] * ceros)
        return ''.join(reversed(res))
    
    @classmethod
    def decodificar(cls, texto: str) -> bytes:
        ceros = 0
        for c in texto:
            if c == '1': ceros += 1
            else: break
        n = 0
        for c in texto:
            if c not in cls.MAPA:
                raise ValueError(f"Carácter inválido: '{c}'")
            n = n * 58 + cls.MAPA[c]
        if n == 0: return b'\x00' * ceros
        datos = n.to_bytes((n.bit_length() + 7) // 8, 'big')
        return b'\x00' * ceros + datos


class Direccion:
    
    @staticmethod
    def _prefijo(d: str) -> Optional[str]:
        if d.startswith(ConfigDireccion.PREFIJO_TESTNET):
            return ConfigDireccion.PREFIJO_TESTNET
        if d.startswith(ConfigDireccion.PREFIJO_PRINCIPAL):
            return ConfigDireccion.PREFIJO_PRINCIPAL
        return None
    
    @staticmethod
    def desde_clave_publica(x: bytes, y: bytes, testnet: bool = False) -> str:
        return Direccion.desde_hash_publico(_Hash.doble(x + y)[:20], testnet)
    
    @staticmethod
    def desde_hash_publico(h: bytes, testnet: bool = False) -> str:
        if len(h) != 20: raise ValueError("Hash público debe ser 20 bytes")
        v = ConfigDireccion.VERSION_BYTES + h
        ck = _Hash.doble(v)[:ConfigDireccion.CHECKSUM_BYTES]
        p = ConfigDireccion.PREFIJO_TESTNET if testnet else ConfigDireccion.PREFIJO_PRINCIPAL
        return f"{p}{Base58.codificar(v + ck)}"
    
    @staticmethod
    def es_valida(d: str) -> bool:
        if not isinstance(d, str): return False
        p = Direccion._prefijo(d)
        if p is None: return False
        cod = d[len(p):]
        if len(d) < ConfigDireccion.LONGITUD_MINIMA or len(d) > ConfigDireccion.LONGITUD_MAXIMA:
            return False
        if not all(c in Base58.ALFABETO for c in cod): return False
        try:
            dec = Base58.decodificar(cod)
            if len(dec) < ConfigDireccion.CHECKSUM_BYTES + 1: return False
            dat = dec[:-ConfigDireccion.CHECKSUM_BYTES]
            ck_esp = dec[-ConfigDireccion.CHECKSUM_BYTES:]
            if dat[0:1] != ConfigDireccion.VERSION_BYTES: return False
            return _Hash.doble(dat)[:ConfigDireccion.CHECKSUM_BYTES] == ck_esp
        except: return False
    
    @staticmethod
    def es_testnet(d: str) -> bool:
        return d.startswith(ConfigDireccion.PREFIJO_TESTNET)
    
    @staticmethod
    def es_mainnet(d: str) -> bool:
        return Direccion._prefijo(d) == ConfigDireccion.PREFIJO_PRINCIPAL
    
    @staticmethod
    def analizar(d: str) -> Optional[Tuple[str, bytes, bytes]]:
        p = Direccion._prefijo(d)
        if p is None or not Direccion.es_valida(d): return None
        dec = Base58.decodificar(d[len(p):])
        return (p, dec[1:-ConfigDireccion.CHECKSUM_BYTES], dec[-ConfigDireccion.CHECKSUM_BYTES:])
    
    @staticmethod
    def comparar(d1: str, d2: str) -> bool:
        """Compara dos direcciones por su hash público (ignora prefijo)."""
        a1, a2 = Direccion.analizar(d1), Direccion.analizar(d2)
        return a1 is not None and a2 is not None and a1[1] == a2[1]
    
    @staticmethod
    def identicas(d1: str, d2: str) -> bool:
        """Compara dos direcciones de forma exacta (incluye prefijo)."""
        return d1 == d2
    
    @staticmethod
    def formatear(d: str, ancho: int = 20) -> str:
        if not Direccion.es_valida(d): return "INVÁLIDA"
        if len(d) <= ancho * 2 + 3: return d
        return f"{d[:ancho]}...{d[-ancho:]}"
    
    @staticmethod
    def a_bytes(d: str) -> Optional[bytes]:
        a = Direccion.analizar(d)
        return a[1] if a else None


class LoteDirecciones:
    @staticmethod
    def validar(direcciones: List[str]) -> Tuple[List[str], List[str]]:
        v, i = [], []
        for d in direcciones:
            (v if Direccion.es_valida(d) else i).append(d)
        return v, i
    
    @staticmethod
    def deduplicar(direcciones: List[str]) -> List[str]:
        visto = set()
        unicas = []
        for d in direcciones:
            if not Direccion.es_valida(d): continue
            b = Direccion.a_bytes(d)
            if b not in visto:
                visto.add(b)
                unicas.append(d)
        return unicas
    
    @staticmethod
    def agrupar(direcciones: List[str]) -> dict:
        g = {"drc": [], "drct": [], "invalidas": []}
        for d in direcciones:
            if Direccion.es_mainnet(d): g["drc"].append(d)
            elif Direccion.es_testnet(d): g["drct"].append(d)
            else: g["invalidas"].append(d)
        return g


class DiagnosticoDireccion:
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
        print("🔍 DIAGNÓSTICO DE CRYPTO/DIRECCION.PY")
        print("=" * 70)
        
        xb, yb = os.urandom(32), os.urandom(32)
        x2, y2 = os.urandom(32), os.urandom(32)
        hp = _Hash.doble(xb + yb)[:20]
        
        dm = Direccion.desde_clave_publica(xb, yb)
        self._t("Generar mainnet", Direccion.es_mainnet(dm), dm[:24]+"...")
        
        dt = Direccion.desde_clave_publica(xb, yb, testnet=True)
        self._t("Generar testnet", Direccion.es_testnet(dt), dt[:24]+"...")
        
        self._t("Validar mainnet", Direccion.es_valida(dm))
        self._t("Validar testnet", Direccion.es_valida(dt))
        self._t("Rechazar sin prefijo", not Direccion.es_valida(dm[3:]))
        self._t("Rechazar prefijo falso", not Direccion.es_valida("xxx"+dm[3:]))
        self._t("Rechazar chars inválidos", not Direccion.es_valida(dm[:10]+"0OIl"+dm[14:]))
        self._t("Formatear", "..." in Direccion.formatear(dm, 10))
        self._t("Analizar", Direccion.analizar(dm) is not None)
        
        self._t("Comparar iguales (misma dir)", Direccion.comparar(dm, dm))
        
        # Misma clave, distinto prefijo → MISMO hash público → comparar da True (correcto)
        self._t("Misma clave main/test → mismo hash",
                Direccion.comparar(dm, dt),
                "Correcto: apuntan a la misma entidad")
        
        dm2 = Direccion.desde_clave_publica(x2, y2)
        self._t("Distinta clave → distinto hash",
                not Direccion.comparar(dm, dm2))
        
        self._t("Idénticas (exactas)", Direccion.identicas(dm, dm))
        self._t("No idénticas (main vs test)", not Direccion.identicas(dm, dt))
        
        self._t("A bytes", len(Direccion.a_bytes(dm)) == 20)
        self._t("Desde hash público", Direccion.es_valida(Direccion.desde_hash_publico(hp)))
        
        # Lote: dm y dt tienen el mismo hash público → deduplicar las cuenta como 1
        lote = [dm, dt, "invalida", dm]
        v, i = LoteDirecciones.validar(lote)
        self._t("Validar lote", len(v) == 3 and len(i) == 1, f"V:{len(v)} I:{len(i)}")
        
        u = LoteDirecciones.deduplicar(lote)
        self._t("Deduplicar (mismo hash = 1)", len(u) == 1, f"{len(u)} única (hash público)")
        
        g = LoteDirecciones.agrupar(lote)
        self._t("Agrupar por prefijo", len(g["drc"]) > 0 and len(g["drct"]) > 0,
                f"drc:{len(g['drc'])} drct:{len(g['drct'])}")
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0:
            print("✅ CRYPTO/DIRECCION.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "🏷️ " * 35)
    print("DIRECCOIN - DIRECCIONES v1.0.3")
    print("🏷️ " * 35)
    print(f"Prefijo: {ConfigDireccion.PREFIJO_PRINCIPAL} / {ConfigDireccion.PREFIJO_TESTNET}\n")
    
    diag = DiagnosticoDireccion()
    if diag.ejecutar():
        x, y = os.urandom(32), os.urandom(32)
        dm = Direccion.desde_clave_publica(x, y)
        dt = Direccion.desde_clave_publica(x, y, testnet=True)
        print("📋 DEMO:")
        print(f"   Mainnet: {dm}")
        print(f"   Testnet: {dt}")
        print(f"   Formateada: {Direccion.formatear(dm, 10)}")
        print(f"   Válida: {'✅' if Direccion.es_valida(dm) else '❌'}")
        print(f"   ¿Misma entidad?: {'✅' if Direccion.comparar(dm, dt) else '❌'} (mainnet y testnet apuntan al mismo hash)")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()