from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

ARCHIVO_SALDOS = 'saldos.json'

def cargar_saldos():
    if os.path.exists(ARCHIVO_SALDOS):
        with open(ARCHIVO_SALDOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_saldos(saldos):
    with open(ARCHIVO_SALDOS, 'w') as f:
        json.dump(saldos, f)

@app.route('/api/v1/estado')
def estado():
    return jsonify({"altura": 1000, "conexion": "ok"})

@app.route('/api/v1/saldo/<direccion>')
def saldo(direccion):
    saldos = cargar_saldos()
    return jsonify({"saldo": saldos.get(direccion, 0)})

@app.route('/api/v1/transferir', methods=['POST'])
def transferir():
    data = request.json
    from_addr = data.get('from')
    to_addr = data.get('to')
    cantidad = data.get('cantidad')
    
    saldos = cargar_saldos()
    if saldos.get(from_addr, 0) >= cantidad:
        saldos[from_addr] = saldos.get(from_addr, 0) - cantidad
        saldos[to_addr] = saldos.get(to_addr, 0) + cantidad
        guardar_saldos(saldos)
        return jsonify({"exito": True})
    return jsonify({"exito": False, "error": "Saldo insuficiente"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8339)
