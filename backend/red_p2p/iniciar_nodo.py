from nodo import NodoDireccoin
import time

nodo = NodoDireccoin(modo="minero")
nodo.iniciar()

print("⛏️  NODO MINERO EN EJECUCIÓN CONTINUA")
print("Presiona Ctrl+C para detener")

while True:
    try:
        resultado = nodo.minar(1000)
        if resultado.get("encontrado"):
            print(f"💎 Bloque minado! Hash: {resultado.get('hash', 'N/A')}")
            print(f"💰 Recompensa: {resultado.get('recompensa_drc', 0)} DRC")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Nodo detenido")
        break
