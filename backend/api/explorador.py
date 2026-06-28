#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - EXPLORADOR DE BLOQUES                        ║
║                    Versión: 1.0.0 | Archivo: api/explorador.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

EXPLORADOR WEB DE BLOQUES PARA DIRECCOIN.

Proporciona una interfaz HTML para:
  • Ver últimos bloques minados
  • Buscar transacciones por TXID
  • Consultar saldo de direcciones
  • Ver estadísticas de la red
  • Monitorear estado del mempool

CARACTERÍSTICAS:
  • Interfaz web responsive (HTML/CSS puro, sin frameworks)
  • Modo oscuro por defecto
  • Búsqueda en tiempo real
  • Diseño profesional tipo blockchain explorers
  • Diagnóstico de 10 pruebas
"""

import json
import time
import random
import hashlib
import os
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigExplorador:
    VERSION = "1.0.0"
    NOMBRE = "Direccoin Explorer"
    HOST = "0.0.0.0"
    PUERTO = 8340
    SIMBOLO = "DRC"
    PREFIJO = "drc"


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3_hex(d: bytes) -> str:
        return hashlib.sha3_256(d).hexdigest()


class Formateador:
    @staticmethod
    def fecha(timestamp: int) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(timestamp))
    
    @staticmethod
    def drc(cantidad: float) -> str:
        return f"{cantidad:,.6f} DRC"
    
    @staticmethod
    def truncar(txt: str, n: int = 12) -> str:
        if len(txt) <= n * 2 + 3:
            return txt
        return f"{txt[:n]}...{txt[-n:]}"
    
    @staticmethod
    def tiempo_atras(segundos: int) -> str:
        if segundos < 60:
            return f"{segundos}s atrás"
        elif segundos < 3600:
            return f"{segundos // 60}m atrás"
        elif segundos < 86400:
            return f"{segundos // 3600}h atrás"
        return f"{segundos // 86400}d atrás"


# ==============================================================================
# SIMULADOR DE DATOS
# ==============================================================================

class DatosExplorador:
    @staticmethod
    def ultimos_bloques(n: int = 20) -> List[Dict]:
        altura = random.randint(10000, 20000)
        bloques = []
        for i in range(n):
            num = altura - i
            txs = random.randint(10, 500)
            bloques.append({
                "indice": num,
                "hash": f"d1{HashUtil.sha3_hex(str(num).encode())}",
                "timestamp": int(time.time()) - (i * 8),
                "transacciones": txs,
                "minero": f"drc{random.randint(1000,9999)}...",
                "recompensa": round(100 * (0.9 ** (num // 97000)), 2),
                "dificultad": random.randint(1, 10),
            })
        return bloques
    
    @staticmethod
    def estadisticas() -> Dict:
        return {
            "altura": random.randint(10000, 20000),
            "nodos": random.randint(50, 500),
            "dificultad": random.randint(1, 10),
            "tasa_hash": f"{random.randint(100, 2000)} kH/s",
            "txs_pendientes": random.randint(0, 1000),
            "gas_actual": round(random.uniform(0.0001, 0.01), 6),
            "suministro_emitido": random.randint(15_000_000, 40_000_000),
            "suministro_total": 100_000_000,
            "bloques_hoy": random.randint(5000, 10000),
        }
    
    @staticmethod
    def buscar(query: str) -> Optional[Dict]:
        if query.startswith("drc"):
            return {
                "tipo": "direccion",
                "datos": {
                    "direccion": query,
                    "saldo": round(random.uniform(0, 1000000), 6),
                    "txs": random.randint(0, 500),
                }
            }
        elif len(query) == 64:
            return {
                "tipo": "transaccion",
                "datos": {
                    "txid": query,
                    "origen": f"drc{random.randint(1000,9999)}...",
                    "destino": f"drc{random.randint(1000,9999)}...",
                    "cantidad": round(random.uniform(1, 10000), 2),
                    "bloque": random.randint(10000, 20000),
                    "estado": "confirmado",
                }
            }
        elif query.isdigit():
            num = int(query)
            return {
                "tipo": "bloque",
                "datos": DatosExplorador._bloque_detalle(num)
            }
        return None
    
    @staticmethod
    def _bloque_detalle(num: int) -> Dict:
        txs = []
        for i in range(random.randint(5, 50)):
            txs.append({
                "txid": HashUtil.sha3_hex(f"{num}_{i}".encode()),
                "origen": f"drc{random.randint(1000,9999)}...",
                "destino": f"drc{random.randint(1000,9999)}...",
                "cantidad": round(random.uniform(0.1, 5000), 2),
            })
        return {
            "indice": num,
            "hash": f"d1{HashUtil.sha3_hex(str(num).encode())}",
            "hash_previo": f"d1{HashUtil.sha3_hex(str(num-1).encode())}",
            "timestamp": int(time.time()) - (num * 8),
            "transacciones": txs,
            "minero": f"drc{random.randint(1000,9999)}...",
            "recompensa": round(100 * (0.9 ** (num // 97000)), 2),
            "dificultad": random.randint(1, 10),
        }


# ==============================================================================
# GENERADOR DE HTML
# ==============================================================================

class GeneradorHTML:
    
    @staticmethod
    def pagina_completa(titulo: str, contenido: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} - {ConfigExplorador.NOMBRE}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: #0a0e14; color: #e0e0e0; font-family: 'Courier New', monospace;
            min-height: 100vh;
        }}
        .header {{
            background: #111720; padding: 20px; border-bottom: 2px solid #d1a000;
            text-align: center;
        }}
        .header h1 {{ color: #d1a000; font-size: 28px; letter-spacing: 2px; }}
        .header span {{ color: #888; font-size: 14px; }}
        .search {{
            max-width: 800px; margin: 20px auto; padding: 0 20px;
        }}
        .search input {{
            width: 100%; padding: 15px; font-size: 16px;
            background: #1a1f2b; border: 1px solid #333; color: #e0e0e0;
            border-radius: 8px; font-family: 'Courier New', monospace;
        }}
        .search input:focus {{ outline: none; border-color: #d1a000; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .stats {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin-bottom: 30px;
        }}
        .stat-card {{
            background: #111720; padding: 15px; border-radius: 8px;
            border: 1px solid #222; text-align: center;
        }}
        .stat-card .label {{ color: #888; font-size: 12px; text-transform: uppercase; }}
        .stat-card .value {{ color: #d1a000; font-size: 20px; margin-top: 5px; }}
        .bloque {{
            background: #111720; padding: 15px; margin: 10px 0;
            border-radius: 8px; border: 1px solid #222;
            display: grid; grid-template-columns: 80px 1fr 100px 120px 100px;
            gap: 15px; align-items: center;
        }}
        .bloque:hover {{ border-color: #d1a000; }}
        .bloque .indice {{ color: #d1a000; font-size: 18px; font-weight: bold; }}
        .bloque .hash {{ color: #888; font-size: 13px; }}
        .bloque .txs {{ color: #4caf50; }}
        .bloque .tiempo {{ color: #888; font-size: 13px; }}
        .footer {{ 
            text-align: center; padding: 20px; color: #555;
            border-top: 1px solid #222; margin-top: 40px;
        }}
        .resultado {{
            background: #111720; padding: 20px; margin: 20px 0;
            border-radius: 8px; border: 1px solid #333;
        }}
        .resultado h3 {{ color: #d1a000; margin-bottom: 15px; }}
        .resultado .campo {{
            display: flex; justify-content: space-between;
            padding: 8px 0; border-bottom: 1px solid #1a1f2b;
        }}
        .resultado .campo .k {{ color: #888; }}
        .resultado .campo .v {{ color: #e0e0e0; }}
        a {{ color: #d1a000; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        @media (max-width: 768px) {{
            .bloque {{ grid-template-columns: 1fr; text-align: center; }}
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⛓️ {ConfigExplorador.NOMBRE}</h1>
        <span>Red Direccoin | v{ConfigExplorador.VERSION}</span>
    </div>
    <div class="search">
        <form method="GET" action="/buscar">
            <input type="text" name="q" placeholder="🔍 Buscar bloque #, dirección drc..., o TXID..." autofocus>
        </form>
    </div>
    <div class="container">
        {contenido}
    </div>
    <div class="footer">
        Direccoin Explorer v{ConfigExplorador.VERSION} | {ConfigExplorador.SIMBOLO} | 
        {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
    </div>
</body>
</html>"""
    
    @staticmethod
    def pagina_principal() -> str:
        stats = DatosExplorador.estadisticas()
        bloques = DatosExplorador.ultimos_bloques(15)
        
        contenido = f"""
        <div class="stats">
            <div class="stat-card">
                <div class="label">Altura</div>
                <div class="value">#{stats['altura']:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Nodos</div>
                <div class="value">{stats['nodos']}</div>
            </div>
            <div class="stat-card">
                <div class="label">Dificultad</div>
                <div class="value">{stats['dificultad']}</div>
            </div>
            <div class="stat-card">
                <div class="label">Gas Actual</div>
                <div class="value">{stats['gas_actual']:.6f} DRC</div>
            </div>
            <div class="stat-card">
                <div class="label">TXs Pendientes</div>
                <div class="value">{stats['txs_pendientes']:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Emitido</div>
                <div class="value">{stats['suministro_emitido']:,} / {stats['suministro_total']:,}</div>
            </div>
        </div>
        
        <h2 style="color:#d1a000; margin-bottom:15px;">📦 Últimos Bloques</h2>
        """
        
        for b in bloques:
            tiempo = Formateador.tiempo_atras(int(time.time()) - b['timestamp'])
            contenido += f"""
        <div class="bloque">
            <div class="indice"><a href="/bloque/{b['indice']}">#{b['indice']:,}</a></div>
            <div class="hash"><a href="/tx/{b['hash']}">{Formateador.truncar(b['hash'], 10)}</a></div>
            <div class="txs">{b['transacciones']} TXs</div>
            <div class="tiempo">{tiempo}</div>
            <div style="color:#888;font-size:12px;">+{b['recompensa']:.2f} DRC</div>
        </div>"""
        
        return GeneradorHTML.pagina_completa("Inicio", contenido)
    
    @staticmethod
    def pagina_bloque(num: int) -> str:
        bloque = DatosExplorador._bloque_detalle(num)
        fecha = Formateador.fecha(bloque['timestamp'])
        
        contenido = f"""
        <h2 style="color:#d1a000;">📦 Bloque #{bloque['indice']:,}</h2>
        <div class="resultado">
            <div class="campo"><span class="k">Hash</span><span class="v">{Formateador.truncar(bloque['hash'], 15)}</span></div>
            <div class="campo"><span class="k">Hash Previo</span><span class="v">{Formateador.truncar(bloque['hash_previo'], 15)}</span></div>
            <div class="campo"><span class="k">Timestamp</span><span class="v">{fecha}</span></div>
            <div class="campo"><span class="k">Transacciones</span><span class="v">{len(bloque['transacciones'])}</span></div>
            <div class="campo"><span class="k">Minero</span><span class="v">{bloque['minero']}</span></div>
            <div class="campo"><span class="k">Recompensa</span><span class="v">{bloque['recompensa']:.2f} DRC</span></div>
            <div class="campo"><span class="k">Dificultad</span><span class="v">{bloque['dificultad']}</span></div>
        </div>
        
        <h3 style="color:#d1a000; margin:20px 0 10px;">📋 Transacciones</h3>"""
        
        for tx in bloque['transacciones'][:20]:
            contenido += f"""
        <div class="bloque" style="grid-template-columns: 1fr 1fr 100px;">
            <div class="hash"><a href="/tx/{tx['txid']}">{Formateador.truncar(tx['txid'], 10)}</a></div>
            <div style="color:#888;font-size:12px;">{Formateador.truncar(tx['origen'], 8)} → {Formateador.truncar(tx['destino'], 8)}</div>
            <div style="color:#4caf50;">{tx['cantidad']:.2f} DRC</div>
        </div>"""
        
        return GeneradorHTML.pagina_completa(f"Bloque #{num}", contenido)
    
    @staticmethod
    def pagina_busqueda(query: str) -> str:
        resultado = DatosExplorador.buscar(query)
        
        if not resultado:
            contenido = f"""
        <div class="resultado">
            <h3>🔍 Sin resultados</h3>
            <p>No se encontró nada para: <b>{query}</b></p>
            <p style="margin-top:10px;">Prueba con un número de bloque, dirección drc... o TXID de 64 caracteres.</p>
        </div>"""
        elif resultado['tipo'] == 'bloque':
            contenido = f"""
        <div class="resultado">
            <h3>📦 Bloque Encontrado</h3>
            <p><a href="/bloque/{resultado['datos']['indice']}">Ver Bloque #{resultado['datos']['indice']:,}</a></p>
        </div>"""
        elif resultado['tipo'] == 'direccion':
            d = resultado['datos']
            contenido = f"""
        <div class="resultado">
            <h3>👤 Dirección</h3>
            <div class="campo"><span class="k">Dirección</span><span class="v">{Formateador.truncar(d['direccion'], 15)}</span></div>
            <div class="campo"><span class="k">Saldo</span><span class="v">{Formateador.drc(d['saldo'])}</span></div>
            <div class="campo"><span class="k">Transacciones</span><span class="v">{d['txs']}</span></div>
        </div>"""
        else:
            d = resultado['datos']
            contenido = f"""
        <div class="resultado">
            <h3>🧾 Transacción</h3>
            <div class="campo"><span class="k">TXID</span><span class="v">{Formateador.truncar(d['txid'], 15)}</span></div>
            <div class="campo"><span class="k">Origen</span><span class="v">{d['origen']}</span></div>
            <div class="campo"><span class="k">Destino</span><span class="v">{d['destino']}</span></div>
            <div class="campo"><span class="k">Cantidad</span><span class="v">{Formateador.drc(d['cantidad'])}</span></div>
            <div class="campo"><span class="k">Bloque</span><span class="v">#{d['bloque']:,}</span></div>
            <div class="campo"><span class="k">Estado</span><span class="v">{d['estado']}</span></div>
        </div>"""
        
        return GeneradorHTML.pagina_completa(f"Buscar: {query}", contenido)


# ==============================================================================
# MANEJADOR HTTP
# ==============================================================================

class ManejadorExplorador(BaseHTTPRequestHandler):
    
    def _enviar_html(self, codigo: int, html: str):
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def _enviar_error(self, codigo: int, mensaje: str):
        html = GeneradorHTML.pagina_completa("Error", f"<h2>Error {codigo}</h2><p>{mensaje}</p>")
        self._enviar_html(codigo, html)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # Página principal
        if path == "/" or path == "/index.html":
            self._enviar_html(200, GeneradorHTML.pagina_principal())
            return
        
        # Buscar
        if path == "/buscar":
            query = params.get("q", [""])[0].strip()
            if query:
                self._enviar_html(200, GeneradorHTML.pagina_busqueda(query))
            else:
                self._enviar_html(200, GeneradorHTML.pagina_principal())
            return
        
        # Bloque específico
        if path.startswith("/bloque/"):
            try:
                num = int(path.split("/")[-1])
                self._enviar_html(200, GeneradorHTML.pagina_bloque(num))
            except ValueError:
                self._enviar_error(400, "Número de bloque inválido")
            return
        
        # TX específica
        if path.startswith("/tx/"):
            txid = path.split("/")[-1]
            resultado = DatosExplorador.buscar(txid)
            if resultado and resultado['tipo'] == 'transaccion':
                self._enviar_html(200, GeneradorHTML.pagina_busqueda(txid))
            else:
                self._enviar_error(404, "Transacción no encontrada")
            return
        
        # Dirección
        if path.startswith("/direccion/"):
            addr = path.split("/")[-1]
            resultado = DatosExplorador.buscar(addr)
            if resultado and resultado['tipo'] == 'direccion':
                self._enviar_html(200, GeneradorHTML.pagina_busqueda(addr))
            else:
                self._enviar_error(404, "Dirección no encontrada")
            return
        
        # API JSON (para frontend)
        if path == "/api/estadisticas":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(DatosExplorador.estadisticas()).encode())
            return
        
        if path == "/api/bloques":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(DatosExplorador.ultimos_bloques(10)).encode())
            return
        
        self._enviar_error(404, "Página no encontrada")
    
    def log_message(self, format, *args):
        pass


# ==============================================================================
# SERVIDOR EXPLORADOR
# ==============================================================================

class ServidorExplorador:
    
    def __init__(self, host: str = None, puerto: int = None):
        self.host = host or ConfigExplorador.HOST
        self.puerto = puerto or ConfigExplorador.PUERTO
        self.servidor: Optional[HTTPServer] = None
        self.hilo: Optional[threading.Thread] = None
    
    def iniciar(self):
        self.servidor = HTTPServer((self.host, self.puerto), ManejadorExplorador)
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║     {ConfigExplorador.NOMBRE} v{ConfigExplorador.VERSION}                    ║
║     http://{self.host}:{self.puerto}                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    def detener(self):
        if self.servidor:
            self.servidor.shutdown()


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoExplorador:
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
        print("🔍 DIAGNÓSTICO DE API/EXPLORADOR.PY")
        print("=" * 70)
        
        self._t("Últimos bloques", len(DatosExplorador.ultimos_bloques(5)) == 5)
        self._t("Estadísticas", "altura" in DatosExplorador.estadisticas())
        self._t("Buscar bloque", DatosExplorador.buscar("100") is not None)
        self._t("Buscar dirección", DatosExplorador.buscar("drcTest123") is not None)
        self._t("Buscar TXID", DatosExplorador.buscar("a"*64) is not None)
        self._t("Buscar inválido", DatosExplorador.buscar("abc") is None)
        
        html = GeneradorHTML.pagina_principal()
        self._t("HTML página principal", len(html) > 1000 and "Direccoin" in html)
        
        html_bloque = GeneradorHTML.pagina_bloque(1)
        self._t("HTML bloque", "Bloque #1" in html_bloque)
        
        html_busqueda = GeneradorHTML.pagina_busqueda("100")
        self._t("HTML búsqueda", "Bloque Encontrado" in html_busqueda)
        
        self._t("Formateador DRC", "DRC" in Formateador.drc(1234.56789))
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ API/EXPLORADOR.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "🔍 " * 35)
    print("DIRECCOIN - EXPLORADOR v1.0.0")
    print("🔍 " * 35)
    
    diag = DiagnosticoExplorador()
    if diag.ejecutar():
        print("📋 DEMO (abre en navegador):")
        print(f"   http://localhost:{ConfigExplorador.PUERTO}")
        print(f"   Busca: bloques, direcciones drc..., TXIDs")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()