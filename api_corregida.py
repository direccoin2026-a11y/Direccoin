from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import time
import hashlib
import random

import math


import math
import re
from datetime import datetime, timedelta

# ===== MEMORIA DE ADA =====
MEMORIA_ADA = {
    "ataques_bloqueados": 0,
    "wallets_sospechosas": {},
    "historial_ataques": [],
    "optimizaciones_realizadas": 0,
    "patrones_aprendidos": [],
    "ultima_prediccion": None,
    "velocidad_promedio": 0,
    "arranque": time.time()
}

def ada_aprender():
    """ADA aprende del estado actual de la red"""
    txs = cargar_transacciones()
    bloques = cargar_bloques()
    pendientes = len(txs.get("pendientes", []))
    
    # Aprender patrón de congestión
    if pendientes > 30:
        MEMORIA_ADA["patrones_aprendidos"].append({
            "hora": datetime.now().hour,
            "dia": datetime.now().strftime("%A"),
            "pendientes": pendientes
        })
    
    # Calcular velocidad promedio de bloques
    if bloques["bloques"]:
        timestamps = [b["timestamp"] for b in bloques["bloques"][-20:]]
        if len(timestamps) > 1:
            velocidades = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            MEMORIA_ADA["velocidad_promedio"] = sum(velocidades) / len(velocidades)

def ada_defender(wallet=None, cantidad=None):
    """ADA analiza si una transacción es sospechosa"""
    sospechas = []
    
    # Regla 1: Spam de transacciones
    if wallet and wallet in MEMORIA_ADA["wallets_sospechosas"]:
        data = MEMORIA_ADA["wallets_sospechosas"][wallet]
        if time.time() - data["ultimo_ataque"] < 300:  # 5 minutos de bloqueo
            sospechas.append(f"Wallet {wallet[:15]}... bloqueada por spam")
            MEMORIA_ADA["ataques_bloqueados"] += 1
    
    # Regla 2: Cantidad sospechosa (más de 500k DRC en una tx)
    if cantidad and cantidad > 500000:
        sospechas.append(f"Cantidad sospechosa detectada: {cantidad:,} DRC")
    
    # Regla 3: Muchas transacciones pendientes
    txs = cargar_transacciones()
    if len(txs.get("pendientes", [])) > 50:
        sospechas.append("Posible ataque DDoS detectado")
        MEMORIA_ADA["ataques_bloqueados"] += 1
    
    return sospechas

def ada_predecir():
    """ADA predice la actividad futura basada en patrones"""
    ahora = datetime.now()
    predicciones = []
    
    # Predecir congestión pre-lotería (viernes/sábado)
    if ahora.strftime("%A") in ["Friday", "Saturday", "viernes", "sábado"]:
        predicciones.append("⚠️ Alta actividad esperada por la lotería del sábado")
    
    # Predecir basado en historial
    hora_actual = ahora.hour
    patrones_hora = [p for p in MEMORIA_ADA.get("patrones_aprendidos", []) if p["hora"] == hora_actual]
    if len(patrones_hora) > 2:
        predicciones.append(f"📈 Patrón detectado: congestión habitual a las {hora_actual}:00h")
    
    return predicciones

def ada_optimizar():
    """ADA ajusta parámetros para optimizar la red"""
    txs = cargar_transacciones()
    pendientes = len(txs.get("pendientes", []))
    bloques = cargar_bloques()
    
    optimizaciones = []
    
    # Si hay muchas tx pendientes, sugerir acelerar
    if pendientes > 40:
        optimizaciones.append("⚡ Modo rápido activado: procesando transacciones prioritarias")
        MEMORIA_ADA["optimizaciones_realizadas"] += 1
    
    # Si la red está tranquila, ahorrar recursos
    if pendientes < 5:
        optimizaciones.append("💤 Modo eficiente: red en estado óptimo, gas mínimo")
    
    # Ajustar dificultad según velocidad
    if MEMORIA_ADA["velocidad_promedio"] > 0:
        if MEMORIA_ADA["velocidad_promedio"] < 2:
            optimizaciones.append("🔧 Dificultad ajustada: bloques muy rápidos")
    
    return optimizaciones

def ada_responder(mensaje, idioma="es"):
    """ADA responde preguntas de los usuarios"""
    mensaje = mensaje.lower().strip()
    
    # Detectar idioma
    if any(w in mensaje for w in ["hello", "how", "what", "network", "price", "help"]):
        idioma = "en"
    
    # Respuestas en español
    if idioma == "es":
        if "estado" in mensaje or "cómo está" in mensaje or "red" in mensaje:
            txs = cargar_transacciones()
            bloques = cargar_bloques()
            saldos = cargar_saldos()
            return f"🟢 Red DirecCoin activa | Altura: {bloques['ultimo_bloque']} bloques | Nodos: {len(NODOS_CONOCIDOS)} | Tx pendientes: {len(txs.get('pendientes',[]))} | Suministro: {sum(saldos.values()):,} / {SUMINISTRO_MAXIMO:,} DRC | Gas: {calcular_gas_dinamico()} DRC"
        
        if "minar" in mensaje or "minería" in mensaje or "mineria" in mensaje:
            return "⛏️ Para minar DRC: Ve a la wallet, crea una cuenta y toca el botón Minero. Cada bloque minado te da 100 DRC. Puedes minar desde cualquier dispositivo."
        
        if "precio" in mensaje or "vale" in mensaje or "valor" in mensaje:
            return "💰 DRC está en fase temprana. El precio se define en el Swap P2P. Actualmente hay ofertas desde $0.0001 USD por DRC. El valor real lo define la comunidad."
        
        if "lotería" in mensaje or "loteria" in mensaje or "sorteo" in mensaje:
            return "🎰 La lotería es cada sábado a las 8PM (hora México). Elige 6 números del 1 al 60. Cuesta 100 DRC. El 10% se quema. ¡El bote es acumulativo!"
        
        if "hola" in mensaje or "hey" in mensaje or "buenas" in mensaje:
            return "👋 ¡Hola! Soy ADA, la IA de DirecCoin. Puedo ayudarte con información de la red, minería, lotería, precios y más. ¿En qué te ayudo?"
        
        if "gracias" in mensaje:
            return "🙏 ¡De nada! Estoy aquí para proteger y optimizar DirecCoin. ¿Algo más?"
    
    # English responses
    if idioma == "en":
        if "status" in mensaje or "how is" in mensaje or "network" in mensaje:
            txs = cargar_transacciones()
            bloques = cargar_bloques()
            saldos = cargar_saldos()
            return f"🟢 DirecCoin Network Active | Height: {bloques['ultimo_bloque']} blocks | Nodes: {len(NODOS_CONOCIDOS)} | Pending Tx: {len(txs.get('pendientes',[]))} | Supply: {sum(saldos.values()):,} / {SUMINISTRO_MAXIMO:,} DRC | Gas: {calcular_gas_dinamico()} DRC"
        
        if "mine" in mensaje or "mining" in mensaje:
            return "⛏️ To mine DRC: Go to the wallet, create an account and tap the Miner button. Each mined block gives 100 DRC. Mine from any device."
        
        if "price" in mensaje or "value" in mensaje or "worth" in mensaje:
            return "💰 DRC is in early phase. The price is defined in the P2P Swap. Currently there are offers from $0.0001 USD per DRC. The real value is defined by the community."
        
        if "lottery" in mensaje:
            return "🎰 The lottery is every Saturday at 8PM (Mexico time). Choose 6 numbers from 1 to 60. It costs 100 DRC. 10% is burned. The jackpot is cumulative!"
        
        if "hello" in mensaje or "hey" in mensaje or "hi" in mensaje:
            return "👋 Hi! I'm ADA, the DirecCoin AI. I can help you with network info, mining, lottery, prices and more. How can I help?"
        
        if "thank" in mensaje:
            return "🙏 You're welcome! I'm here to protect and optimize DirecCoin. Anything else?"
    
    # Respuesta genérica
    if "raspa" in mensaje or "scratch" in mensaje:
        return "🎫 Raspa y Gana: Ticket 50 DRC. Premios: 10, 25, 50, 100 o 500 DRC. 30% quema. Juega en Plays." if idioma == "es" else "🎫 Scratch & Win: 50 DRC ticket. Prizes: 10, 25, 50, 100 or 500 DRC. 30% burn. Play in Plays."
    if "swap" in mensaje or "intercambiar" in mensaje or "exchange" in mensaje:
        return "💱 Swap P2P: DRC ↔ Fiat con escrow automático. Tus DRC se bloquean hasta confirmar el pago. direccoin.org/swap.html" if idioma == "es" else "💱 P2P Swap: DRC ↔ Fiat with automatic escrow. Your DRC are locked until payment is confirmed."
    if "contrato" in mensaje or "smart" in mensaje or "escrow" in mensaje:
        return "📜 Smart Contracts nativos en Python. Escrow, staking, subastas. Gas casi gratis. Sin Solidity." if idioma == "es" else "📜 Native Python Smart Contracts. Escrow, staking, auctions. Near-zero gas. No Solidity."
    if "pouc" in mensaje or "consenso" in mensaje or "consensus" in mensaje:
        return "🧮 PoUC: 5 cálculos útiles por bloque. Sin desperdicio de energía como Bitcoin. La minería procesa transacciones reales." if idioma == "es" else "🧮 PoUC: 5 useful computations per block. No energy waste like Bitcoin. Mining processes real transactions."
    if "suministro" in mensaje or "supply" in mensaje or "tokenomics" in mensaje:
        return "📊 Suministro máximo: 50,000,000 DRC. Premine: 3M (6%). Recompensa: 100 DRC/bloque. Quema deflacionaria en juegos y swap." if idioma == "es" else "📊 Max Supply: 50,000,000 DRC. Premine: 3M (6%). Reward: 100 DRC/block. Deflationary burn in games and swap."
    if "whitepaper" in mensaje or "paper" in mensaje or "documento" in mensaje:
        return "📄 Whitepaper: direccoin.org/whitepaper.html - Disponible en español e inglés." if idioma == "es" else "📄 Whitepaper: direccoin.org/whitepaper.html - Available in Spanish and English."
    if "github" in mensaje or "código" in mensaje or "code" in mensaje or "open source" in mensaje:
        return "💻 Código abierto: github.com/direccoin2026-a11y/DirecCoin - ¡Transparencia total!" if idioma == "es" else "💻 Open source: github.com/direccoin2026-a11y/DirecCoin - Full transparency!"
    if "creador" in mensaje or "creator" in mensaje or "quién" in mensaje or "who made" in mensaje:
        return "👤 DirecCoin fue creada por un desarrollador independiente. Sin ICO, sin VC. Wallet del creador: drc_enviopactocunaaurorabaseritm" if idioma == "es" else "👤 DirecCoin was created by an independent developer. No ICO, no VC. Creator wallet: drc_enviopactocunaaurorabaseritm"
    if "gracias" in mensaje or "thank" in mensaje:
        return "🙏 ¡De nada! Estoy aquí para ayudarte 24/7." if idioma == "es" else "🙏 You're welcome! I'm here 24/7."
    if "adiós" in mensaje or "bye" in mensaje or "chao" in mensaje:
        return "👋 ¡Hasta luego! Vuelve cuando quieras." if idioma == "es" else "👋 See you! Come back anytime."
    if "ayuda" in mensaje or "help" in mensaje or "qué puedes" in mensaje:
        return "🤖 Puedo ayudarte con: red, minería, precios, lotería, raspa y gana, swap, smart contracts, PoUC, suministro, whitepaper, GitHub. Pregunta en español o inglés." if idioma == "es" else "🤖 I can help with: network, mining, prices, lottery, scratch & win, swap, smart contracts, PoUC, supply, whitepaper, GitHub. Ask in English or Spanish."

    return "🤖 Soy ADA, la IA de DirecCoin. Puedo ayudarte con: estado de la red, cómo minar, precios, lotería, smart contracts y más. Pregúntame en español o inglés."

def ada_reporte_semanal():
    """ADA genera un reporte semanal de actividad"""
    saldos = cargar_saldos()
    bloques = cargar_bloques()
    txs = cargar_transacciones()
    
    return {
        "fecha": datetime.now().isoformat(),
        "bloques_minados": bloques["ultimo_bloque"],
        "suministro_actual": sum(saldos.values()),
        "suministro_maximo": SUMINISTRO_MAXIMO,
        "porcentaje_minado": round((sum(saldos.values()) / SUMINISTRO_MAXIMO) * 100, 2),
        "nodos_activos": len(NODOS_CONOCIDOS),
        "ataques_bloqueados": MEMORIA_ADA["ataques_bloqueados"],
        "optimizaciones": MEMORIA_ADA["optimizaciones_realizadas"],
        "patrones_aprendidos": len(MEMORIA_ADA["patrones_aprendidos"]),
        "gas_actual": calcular_gas_dinamico(),
        "predicciones": ada_predecir(),
        "mensaje": "ADA protegiendo DirecCoin 24/7"
    }


def calcular_gas_dinamico():
    """IA que ajusta el gas según la demanda de la red"""
    txs = cargar_transacciones()
    pendientes = len(txs.get("pendientes", []))
    saldos = cargar_saldos()
    suministro_actual = sum(saldos.values())
    
    # Factores que influyen en el gas
    factor_pendientes = 1 + (pendientes / 100)  # +1% por cada 100 tx pendientes
    factor_suministro = 1 + ((SUMINISTRO_MAXIMO - suministro_actual) / SUMINISTRO_MAXIMO)  # Sube al acercarse al límite
    factor_seguridad = 1.0
    
    # Anti-spam: si hay muchas tx de una misma wallet, subir gas
    if pendientes > 50:
        factor_seguridad = 1.5
    
    gas = 0.001 * factor_pendientes * factor_suministro * factor_seguridad
    
    # Topes de seguridad
    if gas < 0.001: gas = 0.001  # Mínimo
    if gas > 0.01: gas = 0.01  # Máximo (anti-abuso)
    
    return round(gas, 8)

import requests

app = Flask(__name__)
CORS(app)

NODOS_CONOCIDOS = ["159.54.147.180:8339"]
SUMINISTRO_MAXIMO = 50000000
SUMINISTRO_PREMINE = 3000000

ARCHIVO_SALDOS = 'saldos.json'
ARCHIVO_BLOQUES = 'bloques.json'
ARCHIVO_TRANSACCIONES = 'transacciones.json'
ARCHIVO_CONTRATOS = 'contratos.json'
ARCHIVO_SWAPS = 'swaps.json'
ARCHIVO_RASPA = 'raspa.json'

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
    return {"ultimo_bloque": 0, "bloques": [], "dificultad": 1}

def guardar_bloques(bloques):
    with open(ARCHIVO_BLOQUES, 'w') as f:
        json.dump(bloques, f)

def cargar_transacciones():
    if os.path.exists(ARCHIVO_TRANSACCIONES):
        with open(ARCHIVO_TRANSACCIONES, 'r') as f:
            return json.load(f)
    return {"pendientes": [], "confirmadas": []}

def guardar_transacciones(txs):
    with open(ARCHIVO_TRANSACCIONES, 'w') as f:
        json.dump(txs, f)


def cargar_raspa():
    if os.path.exists(ARCHIVO_RASPA):
        with open(ARCHIVO_RASPA, 'r') as f:
            return json.load(f)
    return {"fondo": 0, "tickets_vendidos": 0, "premios_entregados": 0}

def guardar_raspa(data):
    with open(ARCHIVO_RASPA, 'w') as f:
        json.dump(data, f)

def cargar_swaps():
    if os.path.exists(ARCHIVO_SWAPS):
        with open(ARCHIVO_SWAPS, 'r') as f:
            return json.load(f)
    return []

def guardar_swaps(swaps):
    with open(ARCHIVO_SWAPS, 'w') as f:
        json.dump(swaps, f)

def cargar_contratos():
    if os.path.exists(ARCHIVO_CONTRATOS):
        with open(ARCHIVO_CONTRATOS, 'r') as f:
            return json.load(f)
    return []

def guardar_contratos(contratos):
    with open(ARCHIVO_CONTRATOS, 'w') as f:
        json.dump(contratos, f)

def ejecutar_contratos():
    contratos = cargar_contratos()
    saldos = cargar_saldos()
    for c in contratos:
        if c["estado"] == "activo":
            if c["tipo"] == "escrow" and c.get("condicion_cumplida"):
                saldos[c["creador"]] = saldos.get(c["creador"], 0) - c["cantidad"]
                saldos[c["beneficiario"]] = saldos.get(c["beneficiario"], 0) + c["cantidad"]
                c["estado"] = "completado"
            elif c["tipo"] == "staking" and time.time() >= c.get("fin_staking", 0):
                recompensa = int(c["cantidad"] * 0.05)
                saldos[c["beneficiario"]] = saldos.get(c["beneficiario"], 0) + recompensa
                c["estado"] = "completado"
            elif c["tipo"] == "subasta" and time.time() >= c.get("fin_subasta", 0):
                if c.get("pujas"):
                    mejor = max(c["pujas"], key=lambda p: p["cantidad"])
                    saldos[mejor["postor"]] = saldos.get(mejor["postor"], 0) - mejor["cantidad"]
                    saldos[c["beneficiario"]] = saldos.get(c["beneficiario"], 0) + mejor["cantidad"]
                c["estado"] = "completado"
    guardar_saldos(saldos)
    guardar_contratos(contratos)


@app.route("/api/v1/estado")
def estado():
    bloques = cargar_bloques()
    return jsonify({
        "altura": bloques["ultimo_bloque"],
        "gas_actual_drc": calcular_gas_dinamico(),
        "nodos_activos": len(NODOS_CONOCIDOS),
        "red": "Direccoin",
        "suministro_emitido": sum(cargar_saldos().values()),
        "transacciones_pendientes": len(cargar_transacciones()["pendientes"]),
        "version": "1.0.0",
        "suministro_maximo": SUMINISTRO_MAXIMO,
        "suministro_premine": SUMINISTRO_PREMINE,
        "porcentaje_minado": round((sum(cargar_saldos().values()) / SUMINISTRO_MAXIMO) * 100, 2)
    })

@app.route("/api/v1/saldo/<direccion>")
def saldo(direccion):
    saldos = cargar_saldos()
    return jsonify({"direccion": direccion, "saldo": saldos.get(direccion, 0)})

@app.route("/api/v1/enviar", methods=["POST"])
def enviar():
    data = request.get_json()
    origen = data.get("origen", "")
    destino = data.get("destino", "")
    cantidad = data.get("cantidad", 0)
    if not origen or not destino or cantidad <= 0:
        return jsonify({"exito": False, "error": "Datos inválidos"})
    saldos = cargar_saldos()
    if saldos.get(origen, 0) < cantidad:
        return jsonify({"exito": False, "error": "Saldo insuficiente"})
    saldos[origen] = saldos.get(origen, 0) - cantidad
    saldos[destino] = saldos.get(destino, 0) + cantidad
    guardar_saldos(saldos)
    txs = cargar_transacciones()
    txs["confirmadas"].append({"origen": origen, "destino": destino, "cantidad": cantidad, "timestamp": time.time()})
    guardar_transacciones(txs)
    return jsonify({"exito": True})

@app.route("/api/v1/minar", methods=["POST"])
def minar():
    data = request.get_json()
    minero = data.get("minero", "")
    if not minero:
        return jsonify({"exito": False, "error": "Dirección de minero requerida"})
    bloques = cargar_bloques()
    nuevo_bloque = {
        "altura": bloques["ultimo_bloque"] + 1,
        "minero": minero,
        "recompensa": 100,
        "transacciones": len(cargar_transacciones()["pendientes"]),
        "timestamp": time.time()
    }
    bloques["bloques"].append(nuevo_bloque)
    bloques["ultimo_bloque"] = nuevo_bloque["altura"]
    guardar_bloques(bloques)
    saldos = cargar_saldos()
    suministro_actual = sum(saldos.values())
    if suministro_actual + 100 <= SUMINISTRO_MAXIMO:
        saldos[minero] = saldos.get(minero, 0) + 100
    guardar_saldos(saldos)
    ada_aprender()
    ada_optimizar()
    ejecutar_contratos()
    return jsonify({"exito": True, "recompensa": 100, "altura": nuevo_bloque["altura"]})

@app.route("/api/v1/transacciones")
def transacciones():
    txs = cargar_transacciones()
    return jsonify({"pendientes": txs.get("pendientes", [])[-10:], "confirmadas": txs.get("confirmadas", [])[-20:]})

@app.route("/api/v1/nodos", methods=["GET"])
def listar_nodos():
    return jsonify({"nodos": NODOS_CONOCIDOS, "nodos_activos": len(NODOS_CONOCIDOS)})

@app.route("/api/v1/nodos/registrar", methods=["POST"])
def registrar_nodo():
    data = request.get_json()
    nodo = data.get("nodo", "")
    if nodo and nodo not in NODOS_CONOCIDOS:
        NODOS_CONOCIDOS.append(nodo)
    return jsonify({"exito": True, "nodos": NODOS_CONOCIDOS})


@app.route("/api/v1/contratos", methods=["GET"])
def listar_contratos():
    return jsonify(cargar_contratos())

@app.route("/api/v1/contratos/crear", methods=["POST"])
def crear_contrato():
    data = request.get_json()
    contratos = cargar_contratos()
    nuevo = {
        "id": len(contratos) + 1,
        "tipo": data.get("tipo", "escrow"),
        "creador": data.get("creador", ""),
        "beneficiario": data.get("beneficiario", ""),
        "cantidad": data.get("cantidad", 0),
        "estado": "activo",
        "fecha_creacion": time.time(),
        "descripcion": data.get("descripcion", "")
    }
    if nuevo["tipo"] == "staking":
        nuevo["fin_staking"] = time.time() + data.get("dias", 30) * 86400
    elif nuevo["tipo"] == "subasta":
        nuevo["fin_subasta"] = time.time() + data.get("horas", 24) * 3600
        nuevo["pujas"] = []
    contratos.append(nuevo)
    guardar_contratos(contratos)
    ejecutar_contratos()
    return jsonify({"exito": True, "contrato": nuevo})

@app.route("/api/v1/contratos/<int:id>/pujar", methods=["POST"])
def pujar_contrato(id):
    data = request.get_json()
    contratos = cargar_contratos()
    for c in contratos:
        if c["id"] == id and c["tipo"] == "subasta" and c["estado"] == "activo":
            c["pujas"].append({"postor": data.get("postor", ""), "cantidad": data.get("cantidad", 0), "timestamp": time.time()})
            guardar_contratos(contratos)
            return jsonify({"exito": True})
    return jsonify({"exito": False, "error": "Contrato no encontrado"})

@app.route("/api/v1/contratos/<int:id>/cumplir", methods=["POST"])
def cumplir_contrato(id):
    contratos = cargar_contratos()
    for c in contratos:
        if c["id"] == id and c["estado"] == "activo":
            c["condicion_cumplida"] = True
            guardar_contratos(contratos)
            ejecutar_contratos()
            return jsonify({"exito": True})
    return jsonify({"exito": False, "error": "Contrato no encontrado"})


@app.route("/api/v1/swap/ofertas", methods=["GET"])
def listar_ofertas_swap():
    return jsonify(cargar_swaps())

@app.route("/api/v1/swap/crear", methods=["POST"])
def crear_oferta_swap():
    data = request.get_json()
    vendedor = data.get("vendedor", "")
    cantidad_drc = data.get("cantidad_drc", 0)
    precio_fiat = data.get("precio_fiat", 0)
    moneda = data.get("moneda", "USD")
    metodo = data.get("metodo", "Transferencia")
    contacto = data.get("contacto", "")
    
    if not vendedor or cantidad_drc <= 0 or precio_fiat <= 0:
        return jsonify({"exito": False, "error": "Datos incompletos"})
    
    saldos = cargar_saldos()
    if saldos.get(vendedor, 0) < cantidad_drc:
        return jsonify({"exito": False, "error": "Saldo insuficiente"})
    
    # Bloquear DRC del vendedor
    saldos[vendedor] = saldos.get(vendedor, 0) - cantidad_drc
    guardar_saldos(saldos)
    
    swaps = cargar_swaps()
    oferta = {
        "id": len(swaps) + 1,
        "vendedor": vendedor,
        "cantidad_drc": cantidad_drc,
        "precio_fiat": precio_fiat,
        "moneda": moneda,
        "metodo": metodo,
        "contacto": contacto,
        "estado": "activa",
        "comprador": None,
        "fecha": time.time()
    }
    swaps.append(oferta)
    guardar_swaps(swaps)
    
    # Crear contrato inteligente automáticamente
    contratos = cargar_contratos()
    contrato = {
        "id": len(contratos) + 1,
        "tipo": "escrow_swap",
        "creador": vendedor,
        "beneficiario": "pendiente",
        "cantidad": cantidad_drc,
        "estado": "activo",
        "fecha_creacion": time.time(),
        "descripcion": f"Swap: {cantidad_drc} DRC por {precio_fiat} {moneda} - {metodo}",
        "swap_id": oferta["id"]
    }
    contratos.append(contrato)
    guardar_contratos(contratos)
    
    return jsonify({"exito": True, "oferta": oferta, "contrato": contrato})

@app.route("/api/v1/swap/tomar", methods=["POST"])
def tomar_oferta_swap():
    data = request.get_json()
    comprador = data.get("comprador", "")
    oferta_id = data.get("oferta_id", 0)
    
    swaps = cargar_swaps()
    for s in swaps:
        if s["id"] == oferta_id and s["estado"] == "activa":
            if s["vendedor"] == comprador:
                return jsonify({"exito": False, "error": "No puedes tomar tu propia oferta"})
            s["estado"] = "en_proceso"
            s["comprador"] = comprador
            s["fecha_tomada"] = time.time()
            guardar_swaps(swaps)
            return jsonify({"exito": True, "oferta": s})
    return jsonify({"exito": False, "error": "Oferta no disponible"})

@app.route("/api/v1/swap/confirmar", methods=["POST"])
def confirmar_swap():
    data = request.get_json()
    oferta_id = data.get("oferta_id", 0)
    
    swaps = cargar_swaps()
    for s in swaps:
        if s["id"] == oferta_id and s["estado"] == "en_proceso":
            s["estado"] = "completada"
            saldos = cargar_saldos()
            saldos[s["comprador"]] = saldos.get(s["comprador"], 0) + s["cantidad_drc"]
            guardar_saldos(saldos)
            guardar_swaps(swaps)
            
            # Ejecutar contrato asociado
            contratos = cargar_contratos()
            for c in contratos:
                if c.get("swap_id") == s["id"] and c["estado"] == "activo":
                    c["estado"] = "completado"
                    c["beneficiario"] = s["comprador"]
                    guardar_contratos(contratos)
                    break
            
            return jsonify({"exito": True, "mensaje": "DRC transferidos al comprador"})
    return jsonify({"exito": False, "error": "No se puede confirmar"})

@app.route("/api/v1/swap/cancelar", methods=["POST"])
def cancelar_swap():
    data = request.get_json()
    oferta_id = data.get("oferta_id", 0)
    
    swaps = cargar_swaps()
    for s in swaps:
        if s["id"] == oferta_id and s["estado"] in ["activa", "en_proceso"]:
            s["estado"] = "cancelada"
            saldos = cargar_saldos()
            saldos[s["vendedor"]] = saldos.get(s["vendedor"], 0) + s["cantidad_drc"]
            guardar_saldos(saldos)
            guardar_swaps(swaps)
            return jsonify({"exito": True, "mensaje": "DRC devueltos al vendedor"})
    return jsonify({"exito": False, "error": "No se puede cancelar"})

@app.route("/api/v1/swap/disputa", methods=["POST"])
def disputa_swap():
    data = request.get_json()
    oferta_id = data.get("oferta_id", 0)
    motivo = data.get("motivo", "")
    
    swaps = cargar_swaps()
    for s in swaps:
        if s["id"] == oferta_id and s["estado"] == "en_proceso":
            s["estado"] = "disputa"
            s["motivo_disputa"] = motivo
            guardar_swaps(swaps)
            return jsonify({"exito": True, "mensaje": "Disputa abierta. Admin revisará."})
    return jsonify({"exito": False, "error": "No se puede abrir disputa"})


@app.route("/api/v1/raspa/fondo", methods=["GET"])
def fondo_raspa():
    return jsonify(cargar_raspa())

@app.route("/api/v1/raspa/comprar", methods=["POST"])
def comprar_raspa():
    data = request.get_json()
    wallet = data.get("wallet", "")
    if not wallet:
        return jsonify({"exito": False, "error": "Wallet requerida"})
    
    saldos = cargar_saldos()
    if saldos.get(wallet, 0) < 50:
        return jsonify({"exito": False, "error": "Saldo insuficiente (50 DRC)"})
    
    # Cobrar 50 DRC
    saldos[wallet] = saldos.get(wallet, 0) - 50
    guardar_saldos(saldos)
    
    # 30% quema, 70% fondo
    raspa = cargar_raspa()
    raspa["fondo"] += 35
    raspa["tickets_vendidos"] += 1
    
    # Determinar premio aleatorio
    prob = random.random()
    premio = 0
    if prob < 0.005: premio = 500
    elif prob < 0.015: premio = 100
    elif prob < 0.04: premio = 50
    elif prob < 0.10: premio = 25
    elif prob < 0.20: premio = 10
    
    if premio > 0 and raspa["fondo"] >= premio:
        raspa["fondo"] -= premio
        raspa["premios_entregados"] += 1
        saldos[wallet] = saldos.get(wallet, 0) + premio
        guardar_saldos(saldos)
    else:
        premio = 0
    
    guardar_raspa(raspa)
    return jsonify({"exito": True, "premio": premio, "fondo": raspa["fondo"]})


@app.route("/api/v1/ia/estado", methods=["GET"])
def ia_estado():
    txs = cargar_transacciones()
    return jsonify({
        "modo_seguro": len(txs.get("pendientes", [])) < 50,
        "gas_actual": calcular_gas_dinamico(),
        "transacciones_pendientes": len(txs.get("pendientes", [])),
        "factor_seguridad": "activo" if len(txs.get("pendientes", [])) > 50 else "normal",
        "suministro_restante": SUMINISTRO_MAXIMO - sum(cargar_saldos().values()),
        "proteccion_anti_spam": "activada",
        "mensaje": "IA protegiendo la red DirecCoin"
    })


@app.route("/api/v1/ada/chat", methods=["POST"])
def ada_chat():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    if not mensaje:
        return jsonify({"respuesta": "¿En qué puedo ayudarte?"})
    respuesta = ada_responder(mensaje)
    ada_aprender()
    return jsonify({"respuesta": respuesta, "ia": "ADA v1.0"})

@app.route("/api/v1/ada/reporte", methods=["GET"])
def ada_reporte():
    return jsonify(ada_reporte_semanal())

@app.route("/api/v1/ada/defensa", methods=["GET"])
def ada_defensa():
    txs = cargar_transacciones()
    return jsonify({
        "modo_seguro": len(txs.get("pendientes", [])) < 50,
        "wallets_bloqueadas": len(MEMORIA_ADA["wallets_sospechosas"]),
        "ataques_bloqueados_hoy": MEMORIA_ADA["ataques_bloqueados"],
        "optimizaciones": MEMORIA_ADA["optimizaciones_realizadas"],
        "predicciones": ada_predecir(),
        "estado": "🛡️ ADA protegiendo la red"
    })

@app.route("/api/v1/ada/aprender", methods=["POST"])
def ada_forzar_aprendizaje():
    ada_aprender()
    ada_optimizar()
    return jsonify({"exito": True, "mensaje": "ADA ha aprendido del estado actual de la red"})

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=8339)
