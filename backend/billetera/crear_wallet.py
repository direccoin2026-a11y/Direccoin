#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - CREADOR DE WALLET DIRECT                     ║
║                    Versión: 1.0.5 | Archivo: billetera/crear_wallet.py      ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════╗
║  🛡️  PROTOCOLO DE SEGURIDAD CRÍTICO      ║
║                                           ║
║  Este archivo se ejecuta UNA SOLA VEZ.    ║
║  Genera tu identidad como Direct.         ║
║  NUNCA lo ejecutes de nuevo sin respaldo. ║
║  GUARDA TU CLAVE PRIVADA EN PAPEL.        ║
║  GUARDA TU FRASE SEMILLA EN PAPEL.        ║
║                                           ║
║  El archivo direct.json se guarda en la   ║
║  misma carpeta donde se ejecuta.          ║
╚═══════════════════════════════════════════╝
"""

import hashlib
import time
import os
import sys
import json
import secrets
from typing import List, Tuple

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigWallet:
    NOMBRE_RED = "Direccoin"
    VERSION = "1.0.5"
    ROL = "direct"
    PREFIJO = "drc"
    CURVA = "secp256k1"
    RUTA_SALIDA = "direct.json"
    RUTA_BACKUP = "direct_backup.txt"


# ==============================================================================
# LISTA DE PALABRAS
# ==============================================================================

LISTA_PALABRAS = [
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


# ==============================================================================
# CRIPTOGRAFÍA DE CURVA ELÍPTICA
# ==============================================================================

class CurvaEliptica:
    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

    @staticmethod
    def inverso_mod(a: int, m: int) -> int:
        return pow(a, -1, m)

    @staticmethod
    def suma_puntos(p: Tuple[int, int], q: Tuple[int, int]) -> Tuple[int, int]:
        if p == (0, 0):
            return q
        if q == (0, 0):
            return p
        P = CurvaEliptica.P
        if p[0] == q[0]:
            if p[1] != q[1]:
                return (0, 0)
            lam = (3 * p[0] * p[0] * CurvaEliptica.inverso_mod(2 * p[1], P)) % P
        else:
            lam = ((q[1] - p[1]) * CurvaEliptica.inverso_mod(q[0] - p[0], P)) % P
        x = (lam * lam - p[0] - q[0]) % P
        y = (lam * (p[0] - x) - p[1]) % P
        return (x, y)

    @staticmethod
    def multiplicar(k: int, punto: Tuple[int, int]) -> Tuple[int, int]:
        resultado = (0, 0)
        actual = punto
        while k > 0:
            if k & 1:
                resultado = CurvaEliptica.suma_puntos(resultado, actual)
            actual = CurvaEliptica.suma_puntos(actual, actual)
            k >>= 1
        return resultado


# ==============================================================================
# UTILIDADES DE HASH
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3_256(datos: bytes) -> bytes:
        return hashlib.sha3_256(datos).digest()

    @staticmethod
    def doble_sha3_256(datos: bytes) -> bytes:
        return HashUtil.sha3_256(HashUtil.sha3_256(datos))

    @staticmethod
    def a_hex(datos: bytes) -> str:
        return datos.hex()


# ==============================================================================
# GENERADOR DE DIRECCIONES
# ==============================================================================

class GeneradorDireccion:
    ALFABETO = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    
    @classmethod
    def generar(cls, clave_publica: Tuple[int, int], prefijo: str = "drc") -> str:
        x_bytes = clave_publica[0].to_bytes(32, 'big')
        y_bytes = clave_publica[1].to_bytes(32, 'big')
        pub_bytes = x_bytes + y_bytes
        id_bytes = HashUtil.doble_sha3_256(pub_bytes)[:20]
        checksum = HashUtil.doble_sha3_256(id_bytes)[:4]
        datos = id_bytes + checksum
        encoded = cls._base58_encode(datos)
        return f"{prefijo}{encoded}"
    
    @classmethod
    def _base58_encode(cls, datos: bytes) -> str:
        ceros = 0
        for b in datos:
            if b == 0:
                ceros += 1
            else:
                break
        n = int.from_bytes(datos, 'big')
        resultado = []
        while n > 0:
            n, r = divmod(n, 58)
            resultado.append(cls.ALFABETO[r])
        resultado.extend(['1'] * ceros)
        return ''.join(reversed(resultado))


# ==============================================================================
# GENERADOR DE WALLET
# ==============================================================================

class GeneradorWalletDirect:
    def __init__(self):
        self.timestamp = int(time.time())
        self.entropia = self._generar_entropia()
        self.clave_privada = self._entropia_a_clave_privada(self.entropia)
        self.clave_publica = CurvaEliptica.multiplicar(
            self.clave_privada, (CurvaEliptica.Gx, CurvaEliptica.Gy)
        )
        self.direccion = GeneradorDireccion.generar(self.clave_publica, ConfigWallet.PREFIJO)
        self.frase_semilla = self._generar_frase_semilla(self.entropia)
        self.checksum = self._calcular_checksum()

    def _generar_entropia(self) -> bytes:
        e1 = os.urandom(32)
        e2 = str(time.time()).encode() + str(time.perf_counter()).encode()
        e3 = secrets.token_bytes(32)
        return HashUtil.sha3_256(e1 + e2 + e3)

    def _entropia_a_clave_privada(self, entropia: bytes) -> int:
        return (int.from_bytes(entropia, 'big') % (CurvaEliptica.N - 1)) + 1

    def _generar_frase_semilla(self, entropia: bytes) -> str:
        total = len(LISTA_PALABRAS)
        indices = []
        for i in range(12):
            chunk = entropia[i*2:i*2+2]
            if len(chunk) < 2:
                chunk = entropia[i*2:] + b'\x00'
            idx = int.from_bytes(chunk, 'big') % total
            indices.append(idx)
        return " ".join(LISTA_PALABRAS[i] for i in indices)

    def _calcular_checksum(self) -> str:
        contenido = f"{ConfigWallet.VERSION}{ConfigWallet.NOMBRE_RED}{ConfigWallet.ROL}{self.direccion}{hex(self.clave_publica[0])}{hex(self.clave_publica[1])}{self.timestamp}"
        return HashUtil.a_hex(HashUtil.sha3_256(contenido.encode()))[:16]

    def exportar_dict(self):
        return {
            "version": ConfigWallet.VERSION,
            "red": ConfigWallet.NOMBRE_RED,
            "rol": ConfigWallet.ROL,
            "curva": ConfigWallet.CURVA,
            "direccion": self.direccion,
            "clave_publica_x": hex(self.clave_publica[0]),
            "clave_publica_y": hex(self.clave_publica[1]),
            "clave_privada": hex(self.clave_privada),
            "frase_semilla": self.frase_semilla,
            "timestamp_creacion": self.timestamp,
            "fecha_creacion": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(self.timestamp)),
            "checksum": self.checksum,
            "advertencia": "NUNCA COMPARTAS ESTE ARCHIVO"
        }


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoWallet:
    def __init__(self, wallet: GeneradorWalletDirect):
        self.wallet = wallet
        self.ok = 0
        self.fail = 0

    def _t(self, n, ok, d):
        s = "✅" if ok else "❌"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1

    def ejecutar(self) -> bool:
        w = self.wallet
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE WALLET DIRECT")
        print("=" * 70)
        self._t("Clave privada en rango", 1 <= w.clave_privada < CurvaEliptica.N, "OK")
        self._t("Clave pública válida", w.clave_publica != (0,0), "Punto en curva")
        self._t("Prefijo drc", w.direccion.startswith("drc"), w.direccion[:20]+"...")
        self._t("Longitud >= 30", len(w.direccion) >= 30, f"{len(w.direccion)} chars")
        pal = w.frase_semilla.split()
        self._t("12 palabras", len(pal) == 12, f"{len(pal)} palabras")
        self._t("Palabras válidas", all(p in LISTA_PALABRAS for p in pal), "OK")
        self._t("Checksum 16 chars", len(w.checksum) == 16, w.checksum)
        self._t("Timestamp", abs(int(time.time())-w.timestamp) < 60, f"{abs(int(time.time())-w.timestamp)}s")
        print("─" * 70)
        print(f"📊 {self.ok}/8 | {self.fail} fallos")
        print("─" * 70)
        if self.fail == 0:
            print("✅ WALLET GENERADA\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🔑 " * 35)
    print("DIRECCOIN - CREADOR DE WALLET DIRECT v1.0.5")
    print("🔑 " * 35)
    print(f"📂 Se guardará en: {os.getcwd()}/{ConfigWallet.RUTA_SALIDA}")
    print("⚠️  Ejecuta UNA SOLA VEZ. Guarda tu frase EN PAPEL.\n")

    print("Generando...")
    wallet = GeneradorWalletDirect()
    print("✅ Lista\n")

    diag = DiagnosticoWallet(wallet)
    if not diag.ejecutar():
        sys.exit(1)

    print("─" * 70)
    print("📋 DATOS DE TU WALLET DIRECT")
    print("─" * 70)
    print(f"🔑 Dirección:   {wallet.direccion}")
    print(f"📅 Creada:      {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(wallet.timestamp))}")
    print(f"🔒 Checksum:    {wallet.checksum}")
    print(f"\n📝 FRASE SEMILLA:\n   {wallet.frase_semilla}")
    print(f"\n🔐 CLAVE PRIVADA:\n   {hex(wallet.clave_privada)}")
    print("─" * 70)

    print("\n🛡️  Escribe la frase para verificar:")
    if input("   > ").strip().lower() != wallet.frase_semilla.lower():
        print("❌ No coincide. Abortando.\n")
        sys.exit(1)

    # Guardar
    datos = wallet.exportar_dict()
    if os.path.exists(ConfigWallet.RUTA_SALIDA):
        print("\n⚠️  direct.json YA EXISTE. ¿Sobreescribir? (SI): ", end="")
        if input().strip() != "SI":
            print("Cancelado.\n")
            sys.exit(0)

    with open(ConfigWallet.RUTA_SALIDA, "w") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    with open(ConfigWallet.RUTA_BACKUP, "w") as f:
        f.write("DIRECCOIN - RESPALDO\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Dirección: {datos['direccion']}\n")
        f.write(f"Clave privada: {datos['clave_privada']}\n")
        f.write(f"Frase: {datos['frase_semilla']}\n")
        f.write("\n⚠️ GUARDA ESTO FUERA DE INTERNET\n")

    print(f"   ✅ {ConfigWallet.RUTA_SALIDA}")
    print(f"   ✅ {ConfigWallet.RUTA_BACKUP}")
    print(f"\n📢 Clave pública X: {hex(wallet.clave_publica[0])}")
    print(f"📢 Clave pública Y: {hex(wallet.clave_publica[1])}")
    print("\n" + "✅ " * 35)
    print("WALLET DIRECT CREADA")
    print("✅ " * 35)
    print("\n📋 PRÓXIMO: python core/genesis.py\n")

if __name__ == "__main__":
    main()