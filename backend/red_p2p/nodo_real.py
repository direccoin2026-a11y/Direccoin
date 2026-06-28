from nodo import NodoDireccoin
import time
import json
import os

# Cargar bloque génesis
genesis_path = os.path.expanduser("~/direccoin/backend/data/genesis.json")
if os.path.exists(genesis_path):
    print("✅ Bloque génesis cargado")
else:
    print("⚠️ No se encontró genesis.json")

nodo = NodoDireccoin(modo="minero")
nodo.iniciar()

print("⛏️  DIRECCOIN NODO REAL - MINANDO 24/7")
print(f"📡 IP: 159.54.129.215:8338")

bloques = 0
while True:
    try:
        resultado = nodo.minar(1000)
        if resultado.get("encontrado"):
            bloques += 1
            recompensa = resultado.get("recompensa_drc", 0)
            print(f"💎 Bloque #{bloques} | Recompensa: {recompensa} DRC | Total: {bloques * 100} DRC")
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(5)
