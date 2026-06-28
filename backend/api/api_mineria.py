from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import time
import threading

app = Flask(__name__)
CORS(app)

ARCHIVO_SALDOS = 'saldos.json'
ARCHIVO_BLOQUES = 'bloques.json'
ultimo_bloque = None

def cargar_saldos():
    if os.path.exists(ARCHIVO_SALDOS):
        with open(ARCHIVO_SALDOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_saldos(saldos):
    with open(ARCHIVO_SALDOS, 'w') as f:
        json.dump(saldos, f)

def cargar_bloques():
    if os.path.exists(ARCHIVO_BLOQUES):
        with open(ARCHIVO_BLOQUES, 'r') as f:
            return json.load(f)
    return {"altura": 0, "bloques": []}

def guardar_bloques(bloques):
    with open(ARCHIVO_BLOQUES, 'w') as f:
        json.dump(bloques, f)

@app.route('/api/v1/estado')
def estado():
    bloques = cargar_bloques()
    return jsonify({"altura": bloques.get("altura", 0), "minando": ultimo_bloque is not None})

@app.route('/api/v1/saldo/<direccion>')
def saldo(direccion):
    saldos = cargar_saldos()
    return jsonify({"saldo": saldos.get(direccion, 0)})

@app.route('/api/v1/minar', methods=['POST'])
def minar():
    global ultimo_bloque
    data = request.json
    minero = data.get('minero')
    
    if not minero:
        return jsonify({"exito": False, "error": "No minero especificado"})
    
    bloques = cargar_bloques()
    nueva_altura = bloques.get("altura", 0) + 1
    
    # Recompensa de 100 DRC por bloque
    recompensa = 100
    
    # Actualizar saldo del minero
    saldos = cargar_saldos()
    saldos[minero] = saldos.get(minero, 0) + recompensa
    guardar_saldos(saldos)
    
    # Registrar bloque
    nuevo_bloque = {
        "altura": nueva_altura,
        "minero": minero,
        "recompensa": recompensa,
        "timestamp": time.time()
    }
    
    bloques["altura"] = nueva_altura
    bloques["bloques"].append(nuevo_bloque)
    guardar_bloques(bloques)
    
    ultimo_bloque = nuevo_bloque
    
    return jsonify({
        "exito": True,
        "altura": nueva_altura,
        "recompensa": recompensa,
        "saldo_nuevo": saldos[minero]
    })

@app.route('/api/v1/ultimo_bloque')
def ultimo_bloque_api():
    global ultimo_bloque
    if ultimo_bloque:
        return jsonify(ultimo_bloque)
    return jsonify({"altura": 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8339)
