#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         DIRECCOIN - BLOQUE GÉNESIS                          ║
║                         Versión: 1.0.3 | Archivo: core/genesis.py           ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════╗
║  🛡️  NUNCA genera wallet.                ║
║  🛡️  SOLO LEE ../billetera/direct.json   ║
╚═══════════════════════════════════════════╝
"""

import hashlib
import time
import os
import sys
import json
from typing import Dict, List, Any

# Forzar directorio de trabajo a core/
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigRed:
    NOMBRE = "Direccoin"
    SIMBOLO = "DRC"
    DECIMALES = 6
    SUMINISTRO_TOTAL = 100_000_000
    PREMINE_TOTAL = 3_000_000
    PREMINE_LIQUIDO = 1_000_000
    PREMINE_BLOQUEADO = 2_000_000
    TIEMPO_BLOQUEO_SEGUNDOS = 86400 * 365
    VERSION_BLOQUE = 1
    VERSION_PROTOCOLO = "1.0.3"
    PUERTO_RED = 8338
    PUERTO_RPC = 8339
    PREFIJO_DIRECCION = "drc"

    # Rutas relativas desde core/
    RUTA_DIRECT_JSON = os.path.join("..", "billetera", "direct.json")
    RUTA_GENESIS_JSON = os.path.join("..", "data", "genesis.json")
    RUTA_GENESIS_INFO = os.path.join("..", "data", "genesis_info.txt")


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3_256(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    @staticmethod
    def doble(d: bytes) -> bytes:
        return HashUtil.sha3_256(HashUtil.sha3_256(d))
    @staticmethod
    def hex(d: bytes) -> str:
        return d.hex()


class MerkleTree:
    def __init__(self, datos: List[bytes]):
        self.hojas = datos
        self.raiz = self._construir(datos)
    def _hash_par(self, a, b):
        return HashUtil.doble(a+b if a<b else b+a)
    def _construir(self, datos):
        nivel = [HashUtil.doble(d) for d in datos]
        while len(nivel) > 1:
            sig = []
            for i in range(0, len(nivel), 2):
                if i+1 < len(nivel):
                    sig.append(self._hash_par(nivel[i], nivel[i+1]))
                else:
                    sig.append(nivel[i])
            nivel = sig
        return nivel[0]


# ==============================================================================
# GESTOR DE IDENTIDAD
# ==============================================================================

class GestorIdentidadDirect:
    @staticmethod
    def cargar() -> Dict[str, Any]:
        ruta = ConfigRed.RUTA_DIRECT_JSON
        if not os.path.exists(ruta):
            print(f"\n❌ No se encontró: {os.path.abspath(ruta)}")
            print("   Ejecuta primero: billetera/crear_wallet.py\n")
            sys.exit(1)
        with open(ruta) as f:
            return json.load(f)


# ==============================================================================
# TRANSACCIÓN PREMINE
# ==============================================================================

class TransaccionPremine:
    def __init__(self, direccion: str):
        self.timestamp = int(time.time())
        self.salidas = [
            {"indice":0, "direccion":direccion, "cantidad":ConfigRed.PREMINE_LIQUIDO, "tipo":"LIQUIDO_INMEDIATO"},
            {"indice":1, "direccion":direccion, "cantidad":ConfigRed.PREMINE_BLOQUEADO, "tipo":"BLOQUEADO_TEMPORAL",
             "script_bloqueo": {"tipo":"CHECKLOCKTIMEVERIFY", "liberacion": self.timestamp + ConfigRed.TIEMPO_BLOQUEO_SEGUNDOS}}
        ]
        self.mensaje = f"Direccoin Genesis | Direct Premine | 1% Liq | 2% Bloq | {ConfigRed.SUMINISTRO_TOTAL} DRC"
        self.txid = self._txid()

    def _txid(self) -> str:
        c = f"{self.timestamp}{self.salidas[0]['direccion']}{self.salidas[0]['cantidad']}{self.salidas[1]['cantidad']}{self.salidas[1]['script_bloqueo']['liberacion']}{self.mensaje}"
        return HashUtil.hex(HashUtil.doble(c.encode()))


# ==============================================================================
# BLOQUE GÉNESIS
# ==============================================================================

class BloqueGenesis:
    def __init__(self, identidad: Dict):
        self.direccion = identidad["direccion"]
        self.transaccion = TransaccionPremine(self.direccion)
        self.version = ConfigRed.VERSION_BLOQUE
        self.indice = 0
        self.hash_previo = "0"*64
        self.timestamp = self.transaccion.timestamp
        self.dificultad = 1
        self.nonce = 0
        self.merkle_tree = MerkleTree([str(s["cantidad"]).encode()+s["direccion"].encode() for s in self.transaccion.salidas])
        self.merkle_raiz = self.merkle_tree.raiz
        self.hash = self._minar()
        self.integridad = HashUtil.hex(HashUtil.sha3_256(self.hash.encode()+self.transaccion.txid.encode()+self.merkle_raiz+self.direccion.encode()))[:16]

    def _minar(self) -> str:
        for nonce in range(2**24):
            c = f"{self.version}{self.indice}{self.hash_previo}{self.timestamp}{self.dificultad}{nonce}{self.transaccion.txid}{HashUtil.hex(self.merkle_raiz)}"
            h = HashUtil.hex(HashUtil.doble(c.encode()))
            if h.startswith("d1"):
                self.nonce = nonce
                return h
        self.nonce = 2**24-1
        return h

    def exportar(self) -> Dict:
        return {
            "bloque": {"version":self.version, "indice":self.indice, "hash":self.hash, "hash_previo":self.hash_previo,
                        "timestamp":self.timestamp, "timestamp_humano":time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(self.timestamp)),
                        "dificultad":self.dificultad, "nonce":self.nonce, "merkle_raiz":HashUtil.hex(self.merkle_raiz), "integridad":self.integridad},
            "premine": {"suministro_total":ConfigRed.SUMINISTRO_TOTAL, "premine_total":ConfigRed.PREMINE_TOTAL,
                         "porcentaje":"3%", "txid":self.transaccion.txid, "salidas":self.transaccion.salidas, "mensaje":self.transaccion.mensaje},
            "direct": {"rol":"direct", "direccion":self.direccion}
        }


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoGenesis:
    def __init__(self, g: BloqueGenesis):
        self.g = g
        self.ok = 0
        self.fail = 0
    def _t(self, n, ok, d):
        print(f"   {'✅' if ok else '❌'} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    def ejecutar(self) -> bool:
        g = self.g
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DEL BLOQUE GÉNESIS")
        print("=" * 70)
        recalc = HashUtil.hex(HashUtil.sha3_256(g.hash.encode()+g.transaccion.txid.encode()+g.merkle_raiz+g.direccion.encode()))[:16]
        self._t("Checksum", recalc == g.integridad, "OK")
        total = sum(s["cantidad"] for s in g.transaccion.salidas)
        self._t("Suministro premine", total == ConfigRed.PREMINE_TOTAL, f"{total:,} DRC")
        self._t("Porcentaje 3%", abs((total/ConfigRed.SUMINISTRO_TOTAL)*100 - 3.0) < 0.01, f"{(total/ConfigRed.SUMINISTRO_TOTAL)*100:.2f}%")
        liq = g.transaccion.salidas[0]["cantidad"]
        bloq = g.transaccion.salidas[1]["cantidad"]
        self._t("1% líq / 2% bloq", liq==1000000 and bloq==2000000, f"Líq: {liq:,} | Bloq: {bloq:,}")
        self._t("Dirección drc", g.direccion.startswith("drc"), g.direccion[:20]+"...")
        self._t("Hash prefijo d1", g.hash.startswith("d1"), g.hash[:16]+"...")
        self._t("TXID 64 hex", len(g.transaccion.txid)==64, g.transaccion.txid[:16]+"...")
        print("─" * 70)
        print(f"📊 {self.ok}/7 | {self.fail} fallos")
        print("─" * 70)
        if self.fail == 0:
            print("✅ BLOQUE GÉNESIS VÁLIDO\n")
        else:
            print("❌ INVÁLIDO\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🏗️ " * 35)
    print("DIRECCOIN - BLOQUE GÉNESIS v1.0.3")
    print("🏗️ " * 35)
    print(f"📂 Directorio: {os.getcwd()}")

    identidad = GestorIdentidadDirect.cargar()
    print(f"👤 Direct: {identidad['direccion'][:24]}...")

    print("\n⛏️  Minando bloque génesis...")
    genesis = BloqueGenesis(identidad)
    print("✅ Bloque creado\n")

    print("─" * 70)
    print(f"🔑 Dirección: {genesis.direccion}")
    print(f"📦 Hash:      {genesis.hash}")
    print(f"🧾 TXID:      {genesis.transaccion.txid}")
    print(f"🕐 Timestamp: {genesis.timestamp}")
    print(f"🔒 Integridad:{genesis.integridad}")
    print("─" * 70)

    diag = DiagnosticoGenesis(genesis)
    if not diag.ejecutar():
        sys.exit(1)

    # Guardar
    os.makedirs(os.path.dirname(ConfigRed.RUTA_GENESIS_JSON), exist_ok=True)
    export = genesis.exportar()
    with open(ConfigRed.RUTA_GENESIS_JSON, "w") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    with open(ConfigRed.RUTA_GENESIS_INFO, "w") as f:
        f.write(f"DIRECCOIN - BLOQUE GÉNESIS\n")
        f.write(f"Dirección: {genesis.direccion}\n")
        f.write(f"Hash: {genesis.hash}\n")
        f.write(f"TXID: {genesis.transaccion.txid}\n")
        f.write(f"Timestamp: {genesis.timestamp}\n")

    print(f"💾 Guardado:")
    print(f"   ✅ {os.path.abspath(ConfigRed.RUTA_GENESIS_JSON)}")
    print(f"   ✅ {os.path.abspath(ConfigRed.RUTA_GENESIS_INFO)}")
    print("\n⚠️  Clave privada solo en billetera/direct.json")
    print("🎯 DIRECCOIN LISTO PARA LA SIGUIENTE FASE\n")

if __name__ == "__main__":
    main()