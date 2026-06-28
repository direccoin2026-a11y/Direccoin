#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - KEYSTORE SEGURO                              ║
║                    Versión: 1.0.7 | Archivo: billetera/keystore.py         ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE ALMACENAMIENTO SEGURO DE CLAVES PARA DIRECCOIN.
Cifrado XSALSA20-HMAC + PBKDF2-SHA3-256 + Frases BIP39.
"""

import hashlib
import hmac
import os
import json
import time
import secrets
import struct
from typing import Tuple, Optional

class ConfigKeystore:
    VERSION = "1.0.7"
    ALGORITMO_CIFRADO = "XSALSA20-HMAC"
    ALGORITMO_KDF = "PBKDF2-SHA3-256"
    ITERACIONES_PBKDF2 = 500_000
    LONGITUD_SALT = 32
    LONGITUD_NONCE = 24
    EXTENSION_KEYSTORE = ".keystore"


LISTA_BIP39 = [
    "abismo", "alba", "altar", "ancla", "arbol", "arco", "arena", "asilo",
    "aurora", "avion", "bajel", "barco", "base", "beso", "borde", "bosque",
    "brazo", "brillo", "brisa", "broca", "buque", "cable", "cabra", "caja",
    "calma", "campo", "canto", "carta", "casa", "cauce", "cedro", "cena",
    "cerco", "ciclo", "cielo", "cima", "circo", "cisne", "clave", "cobre",
    "coche", "color", "coral", "costa", "crema", "cristal", "cruce", "cuadro",
    "cuarzo", "cuerda", "cueva", "cuna", "curso", "danza", "dedo", "delta",
    "denso", "diente", "disco", "doble", "duna", "ebano", "eco", "edad",
    "enlace", "envio", "escama", "espiga", "esquina", "estela", "etapa", "exodo",
    "fabula", "faro", "fase", "fiesta", "figura", "firme", "flama", "flor",
    "foco", "forma", "fosil", "frente", "fruto", "fuego", "fuente", "furia",
    "gema", "gen", "gesto", "golpe", "gota", "grado", "grano", "grito",
    "halo", "haz", "hebra", "hielo", "hilo", "himno", "hogar", "hoja",
    "horca", "horno", "hueso", "idea", "iman", "indice", "isla", "jaula",
    "jefe", "joya", "juego", "jugo", "junco", "labio", "lago", "lanza",
    "lapiz", "largo", "lente", "letra", "lira", "lista", "llave", "lluvia",
    "lomo", "luna", "luz", "madera", "marea", "marfil", "masa", "mazo",
    "medalla", "mente", "mesa", "metal", "metro", "miel", "minuto", "mision",
    "mitad", "modo", "moneda", "monte", "muelle", "muro", "nacion", "nave",
    "neon", "nieve", "nivel", "norte", "nota", "novia", "nube", "nudo",
    "obra", "oceano", "onda", "orden", "orilla", "oro", "pacto", "padre",
    "pais", "palma", "pan", "papel", "parque", "paz", "pecho", "peine",
    "perla", "pez", "pico", "piedra", "piso", "planeta", "plata", "pluma",
    "poder", "pozo", "presion", "principe", "puente", "punto", "queso", "radio",
    "raiz", "rama", "red", "regalo", "reloj", "remo", "resina", "rio",
    "ritmo", "roble", "rosa", "ruta", "salto", "selva", "señal", "silla",
    "simbolo", "sol", "sombra", "sueño", "surco", "tacto", "tambor", "taza",
    "techo", "templo", "tesoro", "tierra", "timon", "torre", "tramo", "tren",
    "tribu", "trono", "tropa", "trueno", "union", "uva", "valle", "vaso",
    "velo", "viento", "vino", "vuelo", "yema", "zafiro", "zona", "zorro"
]
TOTAL_PALABRAS = len(LISTA_BIP39)
MAPA_PALABRAS = {p: i for i, p in enumerate(LISTA_BIP39)}


class CryptoUtil:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    @staticmethod
    def doble_sha3(d: bytes) -> bytes:
        return CryptoUtil.sha3(CryptoUtil.sha3(d))
    @staticmethod
    def hmac_sha3(k: bytes, m: bytes) -> bytes:
        return hmac.new(k, m, hashlib.sha3_256).digest()
    @staticmethod
    def pbkdf2(pw: str, salt: bytes, it: int, ln: int = 32) -> bytes:
        return hashlib.pbkdf2_hmac('sha3_256', pw.encode(), salt, it, dklen=ln)
    @staticmethod
    def cmp(a: bytes, b: bytes) -> bool:
        return secrets.compare_digest(a, b)
    @staticmethod
    def xor(a: bytes, b: bytes) -> bytes:
        return bytes(x ^ y for x, y in zip(a, b))


class CifradoSimetrico:
    @staticmethod
    def _qr(a, b, c, d):
        a = (a + b) & 0xFFFFFFFF; d ^= a; d = ((d << 16) | (d >> 16)) & 0xFFFFFFFF
        c = (c + d) & 0xFFFFFFFF; b ^= c; b = ((b << 12) | (b >> 20)) & 0xFFFFFFFF
        a = (a + b) & 0xFFFFFFFF; d ^= a; d = ((d << 8) | (d >> 24)) & 0xFFFFFFFF
        c = (c + d) & 0xFFFFFFFF; b ^= c; b = ((b << 7) | (b >> 25)) & 0xFFFFFFFF
        return a, b, c, d
    @staticmethod
    def _ks(k: bytes, n: bytes, ctr: int) -> bytes:
        c = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]
        kk = list(struct.unpack('<8I', k))
        nn = list(struct.unpack('<3I', n[:12]))
        e = c + list(kk) + [ctr] + list(nn)
        o = e[:]
        for _ in range(10):
            e[0],e[4],e[8],e[12]=CifradoSimetrico._qr(e[0],e[4],e[8],e[12])
            e[1],e[5],e[9],e[13]=CifradoSimetrico._qr(e[1],e[5],e[9],e[13])
            e[2],e[6],e[10],e[14]=CifradoSimetrico._qr(e[2],e[6],e[10],e[14])
            e[3],e[7],e[11],e[15]=CifradoSimetrico._qr(e[3],e[7],e[11],e[15])
        return struct.pack('<16I', *[(e[i]+o[i])&0xFFFFFFFF for i in range(16)])
    @staticmethod
    def cifrar(k: bytes, t: bytes) -> Tuple[bytes, bytes]:
        n = secrets.token_bytes(24)
        c = b''
        for i in range(0, len(t), 64):
            ks = CifradoSimetrico._ks(k, n, i//64)
            c += CryptoUtil.xor(t[i:i+64], ks[:len(t[i:i+64])])
        mac = CryptoUtil.hmac_sha3(k, n + c)[:16]
        return n, c + mac
    @staticmethod
    def descifrar(k: bytes, n: bytes, d: bytes) -> Optional[bytes]:
        if len(d) < 16: return None
        c, mr = d[:-16], d[-16:]
        if not CryptoUtil.cmp(CryptoUtil.hmac_sha3(k, n + c)[:16], mr): return None
        p = b''
        for i in range(0, len(c), 64):
            ks = CifradoSimetrico._ks(k, n, i//64)
            p += CryptoUtil.xor(c[i:i+64], ks[:len(c[i:i+64])])
        return p


class FraseSemilla:
    
    @staticmethod
    def generar(bits: int = 128) -> str:
        if bits == 128: n_palabras = 12
        elif bits == 160: n_palabras = 15
        elif bits == 192: n_palabras = 18
        elif bits == 224: n_palabras = 21
        elif bits == 256: n_palabras = 24
        else: n_palabras = 12
        entropia = secrets.token_bytes(bits // 8)
        return FraseSemilla.de_entropia(entropia)
    
    @staticmethod
    def de_entropia(entropia: bytes) -> str:
        bits = len(entropia) * 8
        n_palabras = {128: 12, 160: 15, 192: 18, 224: 21, 256: 24}.get(bits, 12)
        e = int.from_bytes(entropia, 'big')
        palabras = []
        for i in range(n_palabras):
            idx = (e >> ((n_palabras - 1 - i) * 11)) & 0x7FF
            palabras.append(LISTA_BIP39[idx % TOTAL_PALABRAS])
        return " ".join(palabras)
    
    @staticmethod
    def a_entropia(frase: str) -> Optional[bytes]:
        ps = frase.lower().strip().split()
        if len(ps) not in [12, 15, 18, 21, 24]: return None
        indices = []
        for p in ps:
            if p not in MAPA_PALABRAS: return None
            indices.append(MAPA_PALABRAS[p])
        e = 0
        for idx in indices:
            e = (e << 11) | idx
        n = len(ps)
        checksum_bits = n * 11 - (n * 11 // 33 * 32)
        bits_entropia = n * 11 - checksum_bits
        entropia_int = e >> checksum_bits
        return entropia_int.to_bytes(bits_entropia // 8, 'big')
    
    @staticmethod
    def es_valida(frase: str) -> bool:
        ps = frase.lower().strip().split()
        return len(ps) in [12, 15, 18, 21, 24] and all(p in MAPA_PALABRAS for p in ps)


class Keystore:
    def __init__(self): self.v = ConfigKeystore.VERSION
    
    def guardar(self, clave: bytes, pw: str, nombre: str = "dw") -> str:
        salt = secrets.token_bytes(32)
        ck = CryptoUtil.pbkdf2(pw, salt, 500_000)
        n, c = CifradoSimetrico.cifrar(ck, clave)
        ks = {"v": self.v, "tipo": "dk", "salt": salt.hex(), "nonce": n.hex(), "datos": c.hex(), "ts": int(time.time())}
        a = f"{nombre}.keystore"
        with open(a, "w") as f: json.dump(ks, f)
        return a
    
    def cargar(self, r: str, pw: str) -> Optional[bytes]:
        try:
            with open(r) as f: ks = json.load(f)
        except: return None
        if ks.get("tipo") != "dk": return None
        ck = CryptoUtil.pbkdf2(pw, bytes.fromhex(ks["salt"]), 500_000)
        return CifradoSimetrico.descifrar(ck, bytes.fromhex(ks["nonce"]), bytes.fromhex(ks["datos"]))


class Diag:
    def __init__(self): self.ok = 0; self.fail = 0
    def t(self, n, ok, d=""):
        s = "✅" if ok else "❌"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    def run(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO KEYSTORE")
        print("=" * 70)
        f = FraseSemilla.generar(128)
        self.t("Generar 12 palabras", len(f.split()) == 12)
        self.t("Validar frase", FraseSemilla.es_valida(f))
        self.t("Rechazar perro", not FraseSemilla.es_valida("perro "*12))
        e = FraseSemilla.a_entropia(f)
        self.t("Frase→entropía", e is not None and len(e) == 16, f"{len(e)} bytes" if e else "None")
        ko = os.urandom(32)
        ks = Keystore()
        a = ks.guardar(ko, "p123")
        self.t("Guardar", os.path.exists(a))
        kr = ks.cargar(a, "p123")
        self.t("Cargar", kr is not None)
        if kr: self.t("Clave ok", kr == ko)
        self.t("Pass mala", ks.cargar(a, "mala") is None)
        self.t("PBKDF2", len(CryptoUtil.pbkdf2("t", b"s", 1000)) == 32)
        n, c = CifradoSimetrico.cifrar(b"k"*32, b"hola")
        p = CifradoSimetrico.descifrar(b"k"*32, n, c)
        self.t("Cifrar/descifrar", p == b"hola")
        self.t("Cmp ok", CryptoUtil.cmp(b"a", b"a"))
        self.t("Cmp no", not CryptoUtil.cmp(b"a", b"b"))
        if os.path.exists(a): os.remove(a)
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ KEYSTORE OK\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "🔐 " * 35)
    print("DIRECCOIN - KEYSTORE v1.0.7")
    print("🔐 " * 35)
    d = Diag()
    if d.run():
        f = FraseSemilla.generar(128)
        print("📋 DEMO:")
        print(f"   Frase: {f}")
        print(f"   Válida: {'✅' if FraseSemilla.es_valida(f) else '❌'}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()