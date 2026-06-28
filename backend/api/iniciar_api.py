from http.server import HTTPServer
from rest_api import ManejadorAPI

print("🌐 Iniciando API REST en puerto 8339...")
servidor = HTTPServer(("0.0.0.0", 8339), ManejadorAPI)
print("✅ API REST escuchando en puerto 8339")
servidor.serve_forever()
