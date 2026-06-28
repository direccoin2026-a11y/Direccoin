from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ManejadorReal(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/v1/estado":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            # Leer el log del nodo real para obtener altura
            import os
            log_path = os.path.expanduser("~/nodo_real.log")
            bloques = 0
            if os.path.exists(log_path):
                with open(log_path) as f:
                    for line in f:
                        if "Bloque #" in line:
                            bloques = int(line.split("#")[1].split("|")[0].strip())
            
            respuesta = {
                "red": "Direccoin",
                "version": "1.0.0",
                "altura": bloques,
                "nodos_activos": 1,
                "dificultad": 1,
                "gas_actual_drc": 0.000001,
                "tasa_hash_khs": 0,
                "transacciones_pendientes": 0,
                "timestamp": __import__('time').time()
            }
            self.wfile.write(json.dumps(respuesta).encode())
        else:
            self.send_response(404)
            self.end_headers()

print("🌐 API REAL en puerto 8339")
HTTPServer(("0.0.0.0", 8339), ManejadorReal).serve_forever()
