#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DIRECCOIN - SERVIDOR WEB LOCAL (SOLUCIÓN DEFINITIVA)          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ejecuta ESTE archivo para ver tu página web con el logo correctamente.
Abre http://localhost:8080 en tu navegador.
"""

import http.server
import os
import webbrowser
import threading

# Cambiar a la carpeta web
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "web"))

# Iniciar servidor
print("🌐 Servidor iniciado: http://localhost:8080")
print("📁 Sirviendo desde:", os.getcwd())
print("⏹️  Presiona Ctrl+C para detener")

webbrowser.open("http://localhost:8080")
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=8080)