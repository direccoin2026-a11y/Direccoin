#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - API REST                                     ║
║                    Versión: 1.0.0 | Archivo: api/rest_api.py              ║
╚══════════════════════════════════════════════════════════════════════════════╝

API REST PARA DIRECCOIN.

Endpoints:
  GET  /api/v1/estado          → Estado de la red
  GET  /api/v1/bloque/:num     → Datos de un bloque
  GET  /api/v1/bloques/recent  → Últimos bloques
  GET  /api/v1/tx/:txid        → Datos de una transacción
  POST /api/v1/tx/enviar       → Enviar transacción
  GET  /api/v1/direccion/:addr → Saldo y datos de una dirección
  GET  /api/v1/gas             → Gas sugerido actual
  GET  /api/v1/estadisticas    → Estadísticas generales

CARACTERÍSTICAS:
  • Servidor HTTP sin dependencias externas
  • JSON como formato de respuesta
  • Rate limiting por IP
  • Caché de respuestas frecuentes
  • CORS habilitado
  • Diagnóstico de 10 pruebas
"""

import json
import time
import random
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigAPI:
    VERSION = "1.0.0"
    HOST = "0.0.0.0"
    PUERTO = 8339
    MAX_REQUEST_SIZE = 1_048_576  # 1 MB
    RATE_LIMIT_VENTANA = 60       # Segundos
    RATE_LIMIT_MAX = 100          # Requests por ventana
    CACHE_TTL = 10                # Segundos de caché


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3_hex(d: bytes) -> str:
        return hashlib.sha3_256(d).hexdigest()


# ==============================================================================
# SIMULADOR DE DATOS (En producción usa la blockchain real)
# ==============================================================================

class DatosRed:
    """Simula datos de la red para la API."""
    
    @staticmethod
    def estado_red() -> Dict:
        return {
            "red": "Direccoin",
            "version": ConfigAPI.VERSION,
            "altura": random.randint(5000, 10000),
            "nodos_activos": random.randint(20, 200),
            "dificultad": random.randint(1, 10),
            "gas_actual_drc": round(random.uniform(0.0001, 0.001), 6),
            "tasa_hash_khs": random.randint(100, 1000),
            "transacciones_pendientes": random.randint(0, 500),
            "timestamp": int(time.time()),
        }
    
    @staticmethod
    def bloque(num: int) -> Optional[Dict]:
        if num < 0:
            return None
        return {
            "indice": num,
            "hash": f"d1{HashUtil.sha3_hex(str(num).encode())}",
            "hash_previo": f"d1{HashUtil.sha3_hex(str(num-1).encode())}",
            "timestamp": int(time.time()) - (num * 8),
            "transacciones": random.randint(5, 500),
            "dificultad": random.randint(1, 10),
            "nonce": random.randint(0, 9999999),
            "minero": f"drc{random.randint(1000,9999)}...",
            "recompensa_drc": round(100 * (0.9 ** (num // 97000)), 2),
        }
    
    @staticmethod
    def bloques_recientes(n: int = 10) -> List[Dict]:
        altura_actual = random.randint(5000, 10000)
        return [DatosRed.bloque(altura_actual - i) for i in range(n)]
    
    @staticmethod
    def transaccion(txid: str) -> Optional[Dict]:
        return {
            "txid": txid,
            "origen": f"drc{random.randint(1000,9999)}...",
            "destino": f"drc{random.randint(1000,9999)}...",
            "cantidad_drc": round(random.uniform(1, 10000), 2),
            "gas_drc": round(random.uniform(0.0001, 0.01), 6),
            "timestamp": int(time.time()) - random.randint(0, 3600),
            "bloque": random.randint(5000, 10000),
            "confirmaciones": random.randint(1, 100),
            "estado": "confirmado" if random.random() > 0.1 else "pendiente",
        }
    
    @staticmethod
    def direccion(addr: str) -> Dict:
        return {
            "direccion": addr,
            "saldo_liquido_drc": round(random.uniform(0, 1000000), 6),
            "saldo_bloqueado_drc": round(random.uniform(0, 2000000), 6),
            "total_transacciones": random.randint(0, 500),
            "primera_actividad": int(time.time()) - random.randint(86400, 86400*365),
            "ultima_actividad": int(time.time()) - random.randint(0, 86400),
            "es_contrato": False,
        }
    
    @staticmethod
    def gas_sugerido() -> Dict:
        uso = random.uniform(0, 1)
        nivel = "bajo" if uso < 0.3 else "medio" if uso < 0.6 else "alto" if uso < 0.85 else "critico"
        return {
            "gas_drc": round(random.uniform(0.0001, 0.01), 6),
            "nivel_congestion": nivel,
            "uso_mempool": round(uso * 100, 1),
            "modo_spam": random.random() < 0.05,
        }
    
    @staticmethod
    def estadisticas() -> Dict:
        return {
            "suministro_total": 100_000_000,
            "suministro_emitido": random.randint(10_000_000, 30_000_000),
            "bloques_totales": random.randint(5000, 10000),
            "transacciones_totales": random.randint(100_000, 5_000_000),
            "mineros_activos": random.randint(100, 5000),
            "precio_drc_usd": round(random.uniform(0.001, 0.1), 6),
        }


# ==============================================================================
# MANEJADOR HTTP
# ==============================================================================

class ManejadorAPI(BaseHTTPRequestHandler):
    """Maneja las peticiones HTTP para la API REST."""
    
    # Rate limiting simple
    _rate_limit: Dict[str, List[float]] = {}
    
    def _verificar_rate_limit(self) -> bool:
        """Verifica el rate limiting por IP."""
        ip = self.client_address[0]
        ahora = time.time()
        ventana = ahora - ConfigAPI.RATE_LIMIT_VENTANA
        
        if ip not in self._rate_limit:
            self._rate_limit[ip] = []
        
        self._rate_limit[ip] = [t for t in self._rate_limit[ip] if t > ventana]
        
        if len(self._rate_limit[ip]) >= ConfigAPI.RATE_LIMIT_MAX:
            return False
        
        self._rate_limit[ip].append(ahora)
        return True
    
    def _enviar_respuesta(self, codigo: int, datos: Any, cache: bool = False):
        """Envía una respuesta JSON."""
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        
        if cache:
            self.send_header("Cache-Control", f"public, max-age={ConfigAPI.CACHE_TTL}")
        else:
            self.send_header("Cache-Control", "no-cache")
        
        self.end_headers()
        
        respuesta = json.dumps(datos, ensure_ascii=False, indent=2)
        self.wfile.write(respuesta.encode("utf-8"))
    
    def _enviar_error(self, codigo: int, mensaje: str):
        """Envía una respuesta de error."""
        self._enviar_respuesta(codigo, {
            "error": True,
            "codigo": codigo,
            "mensaje": mensaje,
            "timestamp": int(time.time()),
        })
    
    def _leer_cuerpo(self) -> Optional[Dict]:
        """Lee el cuerpo JSON de la petición."""
        try:
            longitud = int(self.headers.get("Content-Length", 0))
            if longitud > ConfigAPI.MAX_REQUEST_SIZE:
                return None
            datos = self.rfile.read(longitud)
            return json.loads(datos)
        except:
            return None
    
    def _rutas(self, metodo: str, path: str):
        """Enruta la petición al endpoint correspondiente."""
        partes = path.strip("/").split("/")
        
        # GET /api/v1/estado
        if metodo == "GET" and path == "/api/v1/estado":
            self._enviar_respuesta(200, DatosRed.estado_red(), cache=True)
            return
        
        # GET /api/v1/estadisticas
        if metodo == "GET" and path == "/api/v1/estadisticas":
            self._enviar_respuesta(200, DatosRed.estadisticas(), cache=True)
            return
        
        # GET /api/v1/gas
        if metodo == "GET" and path == "/api/v1/gas":
            self._enviar_respuesta(200, DatosRed.gas_sugerido(), cache=True)
            return
        
        # GET /api/v1/bloques/recent
        if metodo == "GET" and path == "/api/v1/bloques/recent":
            self._enviar_respuesta(200, DatosRed.bloques_recientes(10), cache=True)
            return
        
        # GET /api/v1/bloque/:num
        if metodo == "GET" and len(partes) >= 4 and partes[2] == "bloque":
            try:
                num = int(partes[3])
                bloque = DatosRed.bloque(num)
                if bloque:
                    self._enviar_respuesta(200, bloque, cache=True)
                else:
                    self._enviar_error(404, "Bloque no encontrado")
            except ValueError:
                self._enviar_error(400, "Número de bloque inválido")
            return
        
        # GET /api/v1/tx/:txid
        if metodo == "GET" and len(partes) >= 4 and partes[2] == "tx":
            txid = partes[3]
            tx = DatosRed.transaccion(txid)
            if tx:
                self._enviar_respuesta(200, tx)
            else:
                self._enviar_error(404, "Transacción no encontrada")
            return
        
        # GET /api/v1/direccion/:addr
        if metodo == "GET" and len(partes) >= 4 and partes[2] == "direccion":
            addr = partes[3]
            if addr.startswith("drc"):
                self._enviar_respuesta(200, DatosRed.direccion(addr), cache=True)
            else:
                self._enviar_error(400, "Dirección inválida")
            return
        
        # POST /api/v1/tx/enviar
        if metodo == "POST" and path == "/api/v1/tx/enviar":
            cuerpo = self._leer_cuerpo()
            if not cuerpo:
                self._enviar_error(400, "Cuerpo JSON inválido")
                return
            
            # Simular envío
            txid = HashUtil.sha3_hex(json.dumps(cuerpo).encode())[:32]
            self._enviar_respuesta(201, {
                "enviado": True,
                "txid": txid,
                "mensaje": "Transacción enviada a la mempool",
                "timestamp": int(time.time()),
            })
            return
        
        # Ruta no encontrada
        self._enviar_error(404, f"Endpoint no encontrado: {metodo} {path}")
    
    def do_GET(self):
        if not self._verificar_rate_limit():
            self._enviar_error(429, "Demasiadas peticiones")
            return
        self._rutas("GET", self.path)
    
    def do_POST(self):
        if not self._verificar_rate_limit():
            self._enviar_error(429, "Demasiadas peticiones")
            return
        self._rutas("POST", self.path)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suprime logs HTTP para no llenar la terminal."""
        pass


# ==============================================================================
# SERVIDOR API
# ==============================================================================

class ServidorAPI:
    """
    Servidor HTTP para la API REST de Direccoin.
    
    Uso:
        servidor = ServidorAPI(host="0.0.0.0", puerto=8339)
        servidor.iniciar()
    """
    
    def __init__(self, host: str = None, puerto: int = None):
        self.host = host or ConfigAPI.HOST
        self.puerto = puerto or ConfigAPI.PUERTO
        self.servidor: Optional[HTTPServer] = None
        self.hilo: Optional[threading.Thread] = None
        self.ejecutando = False
    
    def iniciar(self):
        """Inicia el servidor API en un hilo separado."""
        self.servidor = HTTPServer((self.host, self.puerto), ManejadorAPI)
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()
        self.ejecutando = True
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║           DIRECCOIN API REST v{ConfigAPI.VERSION}                    ║
║           Servidor: http://{self.host}:{self.puerto}                     ║
║           Endpoints disponibles en /api/v1/                    ║
╚══════════════════════════════════════════════════════════════╝
""")
        print(f"  Endpoints:")
        print(f"    GET  /api/v1/estado")
        print(f"    GET  /api/v1/estadisticas")
        print(f"    GET  /api/v1/gas")
        print(f"    GET  /api/v1/bloques/recent")
        print(f"    GET  /api/v1/bloque/<num>")
        print(f"    GET  /api/v1/tx/<txid>")
        print(f"    GET  /api/v1/direccion/<addr>")
        print(f"    POST /api/v1/tx/enviar")
    
    def detener(self):
        """Detiene el servidor."""
        if self.servidor:
            self.servidor.shutdown()
            self.ejecutando = False
            print("🛑 API detenida")


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoAPI:
    def __init__(self):
        self.ok = 0
        self.fail = 0
    
    def _t(self, n, ok, d=""):
        s = "✅" if ok else "❌"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE API/REST_API.PY")
        print("=" * 70)
        
        # 1. Estado de red
        estado = DatosRed.estado_red()
        self._t("Estado de red", "altura" in estado and "nodos_activos" in estado)
        
        # 2. Bloque
        bloque = DatosRed.bloque(1)
        self._t("Obtener bloque", bloque is not None and bloque["indice"] == 1)
        
        # 3. Bloques recientes
        recientes = DatosRed.bloques_recientes(5)
        self._t("Bloques recientes", len(recientes) == 5)
        
        # 4. Bloque no encontrado
        bloque_neg = DatosRed.bloque(-1)
        self._t("Bloque inválido", bloque_neg is None)
        
        # 5. Transacción
        tx = DatosRed.transaccion("tx_test")
        self._t("Transacción", tx is not None and "txid" in tx)
        
        # 6. Dirección
        dir_data = DatosRed.direccion("drcTest")
        self._t("Datos dirección", "saldo_liquido_drc" in dir_data)
        
        # 7. Gas sugerido
        gas = DatosRed.gas_sugerido()
        self._t("Gas sugerido", "nivel_congestion" in gas)
        
        # 8. Estadísticas
        stats = DatosRed.estadisticas()
        self._t("Estadísticas", "suministro_total" in stats)
        
        # 9. Servidor
        servidor = ServidorAPI()
        self._t("Servidor creado", servidor is not None)
        
        # 10. Rate limiting
        ip = "192.168.1.1"
        ManejadorAPI._rate_limit[ip] = [time.time()] * ConfigAPI.RATE_LIMIT_MAX
        manejador = ManejadorAPI.__new__(ManejadorAPI)
        manejador.client_address = (ip, 12345)
        ok = manejador._verificar_rate_limit()
        self._t("Rate limit excedido", not ok)
        ManejadorAPI._rate_limit.clear()
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ API/REST_API.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    import sys
    
    print("\n" + "🌍 " * 35)
    print("DIRECCOIN - API REST v1.0.0")
    print("🌍 " * 35)
    
    diag = DiagnosticoAPI()
    if diag.ejecutar():
        print("📋 ENDPOINTS DE EJEMPLO:")
        print(f"   Estado: {json.dumps(DatosRed.estado_red(), indent=2)[:100]}...")
        print(f"   Gas: {json.dumps(DatosRed.gas_sugerido(), indent=2)[:100]}...")
        print(f"   Estadísticas: {json.dumps(DatosRed.estadisticas(), indent=2)[:100]}...")
        print("\n🎯 LISTO\n")


if __name__ == "__main__":
    from http.server import HTTPServer
    servidor = HTTPServer((ConfigAPI.HOST, ConfigAPI.PUERTO), ManejadorAPI)
    print(f"\n🚀 Servidor API corriendo en http://{ConfigAPI.HOST}:{ConfigAPI.PUERTO}")
    print(f"📡 Endpoints disponibles en /api/v1/")
    print("⚠️  Presione Ctrl+C para detener el servidor\n")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
        servidor.shutdown()
