#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - APLICACIÓN COMPLETA v11.0                    ║
║     Logo PNG personalizado · Touch scroll nativo · Encuadre perfecto       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import random
import time
import json
import secrets
import hashlib
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# ==============================================================================
# RUTA DEL LOGO
# ==============================================================================

RUTA_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_direccoin.png")

def cargar_logo(tamano=90):
    """Carga el logo PNG o crea uno por defecto si no existe."""
    if os.path.exists(RUTA_LOGO):
        pixmap = QPixmap(RUTA_LOGO)
        if not pixmap.isNull():
            return pixmap.scaled(tamano, tamano, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # Fallback: logo generado
    return _crear_logo_default(tamano)

def _crear_logo_default(tamano=90):
    """Logo por defecto si no hay PNG."""
    pixmap = QPixmap(tamano, tamano)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#B8860B"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, tamano, tamano)
    painter.setBrush(QColor("#FFFFFF"))
    m = int(tamano * 0.06)
    painter.drawEllipse(m, m, tamano - m*2, tamano - m*2)
    font = QFont("Segoe UI", int(tamano * 0.4), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#B8860B"))
    painter.drawText(QRect(0, 0, tamano, tamano), Qt.AlignCenter, "D")
    painter.end()
    return pixmap

# ==============================================================================
# TEMA
# ==============================================================================

class Tema:
    FONDO = "#F8F6F1"
    CARD = "#FFFFFF"
    BORDE = "#E0DBD0"
    DORADO = "#B8860B"
    DORADO_LIGHT = "#DAA520"
    DORADO_BRIGHT = "#FFD700"
    VERDE = "#2E7D32"
    ROJO = "#C62828"
    AZUL = "#1565C0"
    TEXTO = "#1A1814"
    TEXTO_SEC = "#6B6355"
    TEXTO_LIGHT = "#8B8270"
    INPUT_BG = "#F5F0E8"
    NAV_BG = "#FFFFFF"
    NAV_BORDE = "#E0DBD0"
    NAV_ACTIVO = "#B8860B"
    NAV_INACTIVO = "#8B8270"

def aplicar_tema(app):
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.Window, QColor(Tema.FONDO))
    p.setColor(QPalette.WindowText, QColor(Tema.TEXTO))
    p.setColor(QPalette.Base, QColor(Tema.CARD))
    p.setColor(QPalette.Text, QColor(Tema.TEXTO))
    p.setColor(QPalette.Button, QColor(Tema.CARD))
    p.setColor(QPalette.ButtonText, QColor(Tema.DORADO))
    p.setColor(QPalette.Highlight, QColor(Tema.DORADO))
    app.setPalette(p)
    app.setStyleSheet("* { font-family: 'Segoe UI', 'Inter', sans-serif; }")

# ==============================================================================
# UTILIDADES
# ==============================================================================

class FraseSemilla:
    PALABRAS = [
        "abismo","alba","altar","ancla","arbol","arco","arena","asilo",
        "aurora","avion","bajel","barco","base","beso","borde","bosque",
        "brazo","brillo","brisa","broca","buque","cable","cabra","caja",
        "calma","campo","canto","carta","casa","cauce","cedro","cena",
        "cerco","ciclo","cielo","cima","circo","cisne","clave","cobre",
        "coche","color","coral","costa","crema","cristal","cruce","cuadro",
        "cuarzo","cuerda","cueva","cuna","curso","danza","dedo","delta",
        "denso","diente","disco","doble","duna","ebano","eco","edad",
        "enlace","envio","escama","espiga","esquina","estela","etapa","exodo",
        "fabula","faro","fase","fiesta","figura","firme","flama","flor",
        "foco","forma","fosil","frente","fruto","fuego","fuente","furia",
        "gema","gen","gesto","golpe","gota","grado","grano","grito",
        "halo","haz","hebra","hielo","hilo","himno","hogar","hoja",
        "horca","horno","hueso","idea","iman","indice","isla","jaula",
        "jefe","joya","juego","jugo","junco","labio","lago","lanza",
        "lapiz","largo","lente","letra","lira","lista","llave","lluvia",
        "lomo","luna","luz","madera","marea","marfil","masa","mazo",
        "medalla","mente","mesa","metal","metro","miel","minuto","mision",
        "mitad","modo","moneda","monte","muelle","muro","nacion","nave",
        "neon","nieve","nivel","norte","nota","novia","nube","nudo",
        "obra","oceano","onda","orden","orilla","oro","pacto","padre",
        "pais","palma","pan","papel","parque","paz","pecho","peine",
        "perla","pez","pico","piedra","piso","planeta","plata","pluma",
        "poder","pozo","presion","principe","puente","punto","queso","radio",
        "raiz","rama","red","regalo","reloj","remo","resina","rio",
        "ritmo","roble","rosa","ruta","salto","selva","señal","silla",
        "simbolo","sol","sombra","sueño","surco","tacto","tambor","taza",
        "techo","templo","tesoro","tierra","timon","torre","tramo","tren",
        "tribu","trono","tropa","trueno","union","uva","valle","vaso",
        "velo","viento","vino","vuelo","yema","zafiro","zona","zorro"
    ]
    MAPA = {p:i for i,p in enumerate(PALABRAS)}
    
    @staticmethod
    def generar(bits=128):
        e = int.from_bytes(secrets.token_bytes(bits//8), 'big')
        palabras = []
        for i in range(12):
            idx = (e >> ((11-i)*11)) & 0x7FF
            palabras.append(FraseSemilla.PALABRAS[idx % len(FraseSemilla.PALABRAS)])
        return " ".join(palabras)
    
    @staticmethod
    def validar(frase):
        ps = frase.lower().strip().split()
        return len(ps) == 12 and all(p in FraseSemilla.MAPA for p in ps)

# ==============================================================================
# COMPONENTES
# ==============================================================================

class BotonPrimario(QPushButton):
    def __init__(self, texto):
        super().__init__(texto)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {Tema.DORADO_BRIGHT},stop:1 {Tema.DORADO}); color: white; border: none; border-radius: 10px; padding: 10px; font-size: 13px; font-weight: 700; }}
            QPushButton:hover {{ background: {Tema.DORADO_LIGHT}; }}
            QPushButton:disabled {{ background: #D0D0D0; color: #888; }}
        """)

class BotonOutline(QPushButton):
    def __init__(self, texto):
        super().__init__(texto)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {Tema.DORADO}; border: 2px solid {Tema.DORADO}; border-radius: 10px; padding: 10px; font-size: 13px; font-weight: 700; }}
            QPushButton:hover {{ background: rgba(184,134,11,0.06); }}
        """)

class InputTexto(QLineEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(42)
        self.setStyleSheet(f"""
            QLineEdit {{ background: {Tema.INPUT_BG}; border: 2px solid {Tema.BORDE}; border-radius: 10px; padding: 8px 14px; font-size: 13px; color: {Tema.TEXTO}; }}
            QLineEdit:focus {{ border-color: {Tema.DORADO}; }}
        """)

class Tarjeta(QFrame):
    def __init__(self, dorado=False):
        super().__init__()
        b = Tema.DORADO if dorado else Tema.BORDE
        self.setStyleSheet(f"QFrame {{ background: {Tema.CARD}; border: 1.5px solid {b}; border-radius: 12px; padding: 14px; }}")

class MiniStats(QFrame):
    def __init__(self, icono, valor, etiqueta):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ background: {Tema.CARD}; border: 1px solid {Tema.BORDE}; border-radius: 8px; padding: 8px 10px; }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        l = QVBoxLayout(self)
        l.setSpacing(2)
        l.setContentsMargins(0,0,0,0)
        l.addWidget(QLabel(icono, styleSheet="font-size:13px;"))
        l.addWidget(QLabel(valor, styleSheet=f"color:{Tema.TEXTO};font-size:11px;font-weight:700;"))
        l.addWidget(QLabel(etiqueta, styleSheet=f"color:{Tema.TEXTO_LIGHT};font-size:8px;"))

# ==============================================================================
# VENTANA DE LOGIN
# ==============================================================================

class VentanaLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Direccoin")
        self.resize(400, 580)
        self.setMinimumSize(320, 460)
        self.usuario = None
        self._crear()
    
    def _crear(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        
        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo
        logo = QLabel()
        logo.setPixmap(cargar_logo(80))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        titulo = QLabel("DIRECCOIN")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titulo.setStyleSheet(f"color: {Tema.DORADO}; letter-spacing: 2px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        sub = QLabel("Criptomoneda con IA integrada")
        sub.setStyleSheet(f"color:{Tema.TEXTO_SEC};font-size:10px;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self._bienvenida())
        self.stack.addWidget(self._crear_cuenta())
        self.stack.addWidget(self._ingresar_frase())
        self.stack.addWidget(self._verificar_frase())
        layout.addWidget(self.stack)
        
        scroll.setWidget(contenido)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(scroll)
    
    def _bienvenida(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(12)
        l.addWidget(BotonPrimario("🆕  Crear nueva cuenta"))
        l.addWidget(BotonOutline("🔑  Ya tengo frase semilla"))
        # Conectar botones
        l.itemAt(0).widget().clicked.connect(lambda: self.stack.setCurrentIndex(1))
        l.itemAt(1).widget().clicked.connect(lambda: self.stack.setCurrentIndex(2))
        return p
    
    def _crear_cuenta(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(8)
        
        t = QLabel("🎉 ¡Tu nueva cuenta!")
        t.setFont(QFont("Segoe UI", 13, QFont.Bold))
        t.setAlignment(Qt.AlignCenter)
        l.addWidget(t)
        
        l.addWidget(QLabel("Frase semilla (12 palabras):", styleSheet=f"color:{Tema.TEXTO_SEC};font-size:9px;"))
        
        self.frase_nueva = FraseSemilla.generar()
        f = QLabel(self.frase_nueva)
        f.setFont(QFont("Courier New", 10))
        f.setWordWrap(True)
        f.setAlignment(Qt.AlignCenter)
        f.setStyleSheet(f"background:{Tema.INPUT_BG};border:2px solid {Tema.DORADO_LIGHT};border-radius:8px;padding:8px;color:{Tema.TEXTO};")
        l.addWidget(f)
        
        w = QLabel("⚠️ Guarda estas palabras EN PAPEL.")
        w.setWordWrap(True)
        w.setStyleSheet(f"color:{Tema.ROJO};font-weight:600;font-size:9px;")
        w.setAlignment(Qt.AlignCenter)
        l.addWidget(w)
        
        self.cb = QCheckBox("✅ Guardé mi frase en lugar seguro")
        self.cb.setStyleSheet(f"color:{Tema.TEXTO};font-size:10px;")
        l.addWidget(self.cb)
        
        b = BotonPrimario("🚀  Entrar")
        b.setEnabled(False)
        self.cb.toggled.connect(lambda: b.setEnabled(self.cb.isChecked()))
        b.clicked.connect(lambda: self._finalizar(self.frase_nueva))
        l.addWidget(b)
        
        volver = QPushButton("← Volver")
        volver.setCursor(QCursor(Qt.PointingHandCursor))
        volver.setStyleSheet(f"QPushButton{{background:transparent;color:{Tema.TEXTO_LIGHT};border:none;font-size:9px;}}QPushButton:hover{{color:{Tema.DORADO};}}")
        volver.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        l.addWidget(volver)
        return p
    
    def _ingresar_frase(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(8)
        
        t = QLabel("🔐 Ingresa tu frase")
        t.setFont(QFont("Segoe UI", 13, QFont.Bold))
        t.setAlignment(Qt.AlignCenter)
        l.addWidget(t)
        
        self.input_frase = QTextEdit()
        self.input_frase.setPlaceholderText("12 palabras separadas por espacios...")
        self.input_frase.setMaximumHeight(70)
        self.input_frase.setStyleSheet(f"QTextEdit{{background:{Tema.INPUT_BG};border:2px solid {Tema.BORDE};border-radius:8px;padding:8px;font-size:11px;color:{Tema.TEXTO};font-family:'Courier New';}}")
        l.addWidget(self.input_frase)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color:{Tema.ROJO};font-size:9px;font-weight:600;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        l.addWidget(self.error_label)
        
        b = BotonPrimario("🔓  Desbloquear")
        b.clicked.connect(self._verificar_frase_ingresada)
        l.addWidget(b)
        
        volver = QPushButton("← Volver")
        volver.setCursor(QCursor(Qt.PointingHandCursor))
        volver.setStyleSheet(f"QPushButton{{background:transparent;color:{Tema.TEXTO_LIGHT};border:none;font-size:9px;}}QPushButton:hover{{color:{Tema.DORADO};}}")
        volver.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        l.addWidget(volver)
        return p
    
    def _verificar_frase(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(8)
        
        t = QLabel("🛡️ Verificación")
        t.setFont(QFont("Segoe UI", 13, QFont.Bold))
        t.setAlignment(Qt.AlignCenter)
        l.addWidget(t)
        
        l.addWidget(QLabel("Palabras 3, 7 y 11:", styleSheet=f"color:{Tema.TEXTO_SEC};font-size:9px;"))
        
        self.verify_inputs = []
        for num in [3, 7, 11]:
            self.verify_inputs.append(InputTexto(f"Palabra {num}"))
            l.addWidget(self.verify_inputs[-1])
        
        self.verify_error = QLabel("")
        self.verify_error.setStyleSheet(f"color:{Tema.ROJO};font-size:9px;font-weight:600;")
        self.verify_error.setAlignment(Qt.AlignCenter)
        self.verify_error.setVisible(False)
        l.addWidget(self.verify_error)
        
        b = BotonPrimario("✅  Confirmar")
        b.clicked.connect(self._confirmar_verificacion)
        l.addWidget(b)
        return p
    
    def _verificar_frase_ingresada(self):
        frase = self.input_frase.toPlainText().strip()
        if not FraseSemilla.validar(frase):
            self.error_label.setText("❌ 12 palabras válidas requeridas.")
            self.error_label.setVisible(True)
            return
        self.error_label.setVisible(False)
        self.frase_ingresada = frase
        self.stack.setCurrentIndex(3)
    
    def _confirmar_verificacion(self):
        frase = getattr(self, 'frase_ingresada', getattr(self, 'frase_nueva', ''))
        palabras = frase.split()
        esperadas = [palabras[2], palabras[6], palabras[10]]
        ingresadas = [inp.text().strip().lower() for inp in self.verify_inputs]
        if ingresadas == esperadas:
            self._finalizar(frase)
        else:
            self.verify_error.setText("❌ No coinciden.")
            self.verify_error.setVisible(True)
    
    def _finalizar(self, frase):
        self.usuario = {
            "frase": frase,
            "direccion": "drc" + hashlib.sha3_256(frase.encode()).hexdigest()[:30],
            "autenticado": True,
        }
        self.accept()

# ==============================================================================
# APP PRINCIPAL
# ==============================================================================

class AppDireccoin(QMainWindow):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("Direccoin")
        self.resize(400, 680)
        self.setMinimumSize(340, 480)
        self._crear()
    
    def _crear(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout(central)
        ml.setSpacing(0)
        ml.setContentsMargins(0,0,0,0)
        
        # Barra superior
        barra = QFrame()
        barra.setFixedHeight(46)
        barra.setStyleSheet(f"background:{Tema.CARD};border-bottom:1px solid {Tema.BORDE};")
        bl = QHBoxLayout(barra)
        bl.setContentsMargins(10,0,10,0)
        logo_peq = QLabel()
        logo_peq.setPixmap(cargar_logo(24))
        bl.addWidget(logo_peq)
        bl.addWidget(QLabel("DIRECCOIN", styleSheet=f"color:{Tema.DORADO};font-size:12px;font-weight:800;"))
        bl.addStretch()
        bl.addWidget(QLabel(f"🔑 {self.usuario['direccion'][:10]}...", styleSheet=f"color:{Tema.TEXTO_SEC};font-size:8px;"))
        ml.addWidget(barra)
        
        # Páginas
        self.paginas = QStackedWidget()
        self.paginas.addWidget(self._pagina_wallet())
        self.paginas.addWidget(self._pagina_minero())
        self.paginas.addWidget(self._pagina_explorador())
        self.paginas.addWidget(self._pagina_ia())
        self.paginas.addWidget(self._pagina_red())
        ml.addWidget(self.paginas)
        
        # Navegación inferior
        nav = QFrame()
        nav.setFixedHeight(56)
        nav.setStyleSheet(f"background:{Tema.NAV_BG};border-top:1px solid {Tema.NAV_BORDE};")
        nl = QHBoxLayout(nav)
        nl.setSpacing(0)
        nl.setContentsMargins(0,0,0,0)
        self.nav_btns = []
        for ico,txt,idx in [("💰","Wallet",0),("⛏️","Minero",1),("🔍","Explorar",2),("🤖","IA",3),("🌐","Red",4)]:
            btn = QPushButton(f"{ico}\n{txt}")
            btn.setFont(QFont("Segoe UI", 7))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:{Tema.NAV_INACTIVO};border:none;padding:4px;font-weight:500;}}QPushButton:hover{{color:{Tema.DORADO};}}QPushButton[activo=\"true\"]{{color:{Tema.NAV_ACTIVO};font-weight:700;border-top:2px solid {Tema.DORADO};}}")
            btn.clicked.connect(lambda ch,i=idx: self._cambiar(i))
            self.nav_btns.append(btn)
            nl.addWidget(btn)
        ml.addWidget(nav)
        self._cambiar(0)
    
    def _cambiar(self, i):
        self.paginas.setCurrentIndex(i)
        for j,b in enumerate(self.nav_btns):
            b.setProperty("activo","true" if j==i else "false")
            b.style().polish(b)
    
    def _scroll(self, w):
        p = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        s.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        s.setWidget(w)
        pl = QVBoxLayout(p)
        pl.setContentsMargins(0,0,0,0)
        pl.addWidget(s)
        return p
    
    def _pagina_wallet(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(8)
        l.setContentsMargins(14,12,14,16)
        
        l.addWidget(QLabel("💼 Mi Billetera", styleSheet=f"color:{Tema.TEXTO};font-size:16px;font-weight:800;"))
        
        # Dirección
        df = QFrame()
        df.setStyleSheet(f"background:{Tema.INPUT_BG};border:1px solid {Tema.BORDE};border-radius:6px;padding:5px 8px;")
        dl = QHBoxLayout(df)
        dl.setContentsMargins(0,0,0,0)
        dl.setSpacing(4)
        dl.addWidget(QLabel("🔑"))
        a = QLabel(self.usuario['direccion'])
        a.setStyleSheet(f"color:{Tema.TEXTO_SEC};font-size:9px;font-family:'Courier New';")
        a.setTextInteractionFlags(Qt.TextSelectableByMouse)
        dl.addWidget(a)
        cop = QPushButton("Copiar")
        cop.setCursor(QCursor(Qt.PointingHandCursor))
        cop.setFixedHeight(22)
        cop.setStyleSheet(f"QPushButton{{background:{Tema.FONDO};color:{Tema.DORADO};border:none;border-radius:3px;padding:1px 6px;font-size:8px;font-weight:600;}}QPushButton:hover{{background:{Tema.DORADO};color:white;}}")
        cop.clicked.connect(lambda: QApplication.clipboard().setText(a.text()))
        dl.addWidget(cop)
        l.addWidget(df)
        
        # Saldo
        saldo = Tarjeta(dorado=True)
        sl = QVBoxLayout(saldo)
        sl.setSpacing(3)
        sl.addWidget(QLabel("SALDO DISPONIBLE", styleSheet=f"color:{Tema.TEXTO_LIGHT};font-size:7px;font-weight:600;letter-spacing:1px;"))
        sl.addWidget(QLabel("1,000,000.000000 DRC", styleSheet=f"color:{Tema.VERDE};font-size:18px;font-weight:800;font-family:'Courier New';"))
        sl.addWidget(QLabel("≈ $10,000.00 USD", styleSheet=f"color:{Tema.TEXTO_SEC};font-size:10px;"))
        sl.addWidget(QLabel("🔒 2,000,000 DRC bloqueados • 364 días", styleSheet=f"color:{Tema.DORADO};font-size:8px;font-weight:600;"))
        l.addWidget(saldo)
        
        # Botones
        bl2 = QHBoxLayout()
        bl2.setSpacing(8)
        bl2.addWidget(BotonPrimario("📤 Enviar"))
        bl2.addWidget(BotonOutline("📥 Recibir"))
        l.addLayout(bl2)
        
        # Stats
        grid = QGridLayout()
        grid.setSpacing(6)
        for i,(ico,val,eti) in enumerate([("📊","156","Transacciones"),("⛏️","45.2","Minados"),("⚡","0.000001","Gas"),("🔗","47","Nodos")]):
            grid.addWidget(MiniStats(ico,val,eti), i//2, i%2)
        l.addLayout(grid)
        l.addStretch()
        return self._scroll(w)
    
    def _pagina_minero(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(8)
        l.setContentsMargins(14,12,14,16)
        l.addWidget(QLabel("⛏️ Minero", styleSheet=f"color:{Tema.TEXTO};font-size:16px;font-weight:800;"))
        card = Tarjeta()
        cl = QVBoxLayout(card)
        cl.setSpacing(5)
        cl.addWidget(QLabel("🟢 ACTIVO", styleSheet=f"color:{Tema.VERDE};font-size:9px;font-weight:700;"))
        self.prog = QProgressBar()
        self.prog.setValue(86)
        self.prog.setFixedHeight(16)
        self.prog.setStyleSheet(f"QProgressBar{{background:{Tema.INPUT_BG};border:1px solid {Tema.BORDE};border-radius:8px;text-align:center;font-weight:700;font-size:7px;color:{Tema.TEXTO};}}QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {Tema.DORADO_LIGHT},stop:1 {Tema.DORADO_BRIGHT});border-radius:8px;}}")
        cl.addWidget(self.prog)
        cl.addWidget(QLabel("⏱️ 234 h/s • 💎 +12.5 DRC • 🔥 456 total", styleSheet=f"color:{Tema.TEXTO_LIGHT};font-size:8px;"))
        l.addWidget(card)
        self.btn_minar = BotonOutline("⏸️ Pausar")
        self.btn_minar.clicked.connect(self._toggle)
        l.addWidget(self.btn_minar)
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.prog.setValue((self.prog.value()+random.randint(1,3))%101))
        self.timer.start(2500)
        l.addStretch()
        return self._scroll(w)
    
    def _toggle(self):
        if "Pausar" in self.btn_minar.text():
            self.btn_minar.setText("▶️ Reanudar")
            self.timer.stop()
        else:
            self.btn_minar.setText("⏸️ Pausar")
            self.timer.start()
    
    def _pagina_explorador(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(6)
        l.setContentsMargins(14,12,14,16)
        l.addWidget(QLabel("🔍 Explorador", styleSheet=f"color:{Tema.TEXTO};font-size:16px;font-weight:800;"))
        l.addWidget(InputTexto("Buscar..."))
        l.addWidget(QLabel("ÚLTIMOS BLOQUES", styleSheet=f"color:{Tema.DORADO};font-size:8px;font-weight:700;"))
        for _ in range(4):
            b = QFrame()
            b.setStyleSheet(f"QFrame{{background:{Tema.CARD};border:1px solid {Tema.BORDE};border-radius:6px;padding:5px 8px;}}")
            bl = QHBoxLayout(b)
            bl.setSpacing(5)
            bl.addWidget(QLabel(f"#{random.randint(8000,15000):,}", styleSheet=f"color:{Tema.DORADO};font-size:9px;font-weight:700;"))
            bl.addWidget(QLabel(f"d1{random.randint(1000,9999)}...", styleSheet=f"color:{Tema.TEXTO_SEC};font-size:8px;font-family:'Courier New';"))
            bl.addWidget(QLabel(f"{random.randint(5,500)} TXs", styleSheet=f"color:{Tema.VERDE};font-size:8px;"))
            bl.addWidget(QLabel(f"{random.randint(1,60)}s", styleSheet=f"color:{Tema.TEXTO_LIGHT};font-size:7px;"))
            l.addWidget(b)
        l.addStretch()
        return self._scroll(w)
    
    def _pagina_ia(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(6)
        l.setContentsMargins(14,12,14,16)
        l.addWidget(QLabel("🤖 IA", styleSheet=f"color:{Tema.TEXTO};font-size:16px;font-weight:800;"))
        grid = QGridLayout()
        grid.setSpacing(5)
        for i,(ico,nom,est,col) in enumerate([("💸","Gas","Bajo",Tema.VERDE),("⚡","Red","45ms",Tema.AZUL),("🛡️","Seguridad","Activo",Tema.VERDE),("📊","Monitor","47 nodos",Tema.VERDE)]):
            c = QFrame()
            c.setStyleSheet(f"QFrame{{background:{Tema.CARD};border:1px solid {Tema.BORDE};border-radius:7px;padding:7px;}}")
            cl2 = QVBoxLayout(c)
            cl2.setSpacing(1)
            h = QHBoxLayout()
            h.addWidget(QLabel(ico))
            h.addWidget(QLabel(nom, styleSheet=f"color:{Tema.TEXTO};font-size:10px;font-weight:600;"))
            h.addStretch()
            d = QFrame()
            d.setFixedSize(5,5)
            d.setStyleSheet(f"background:{col};border-radius:2px;")
            h.addWidget(d)
            cl2.addLayout(h)
            cl2.addWidget(QLabel(est, styleSheet=f"color:{col};font-size:9px;font-weight:600;"))
            grid.addWidget(c, i//2, i%2)
        l.addLayout(grid)
        l.addStretch()
        return self._scroll(w)
    
    def _pagina_red(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(6)
        l.setContentsMargins(14,12,14,16)
        l.addWidget(QLabel("🌐 Red", styleSheet=f"color:{Tema.TEXTO};font-size:16px;font-weight:800;"))
        grid = QGridLayout()
        grid.setSpacing(5)
        for i,(ico,val,eti) in enumerate([("🟢","47","Nodos"),("📡","2","Semillas"),("⚡","45ms","Latencia"),("📦","15K","Bloques")]):
            grid.addWidget(MiniStats(ico,val,eti), i//2, i%2)
        l.addLayout(grid)
        for i in range(3):
            n = QFrame()
            n.setStyleSheet(f"QFrame{{background:{Tema.CARD};border:1px solid {Tema.BORDE};border-radius:5px;padding:4px 7px;}}")
            nl = QHBoxLayout(n)
            nl.setSpacing(5)
            nl.addWidget(QLabel("🟢", styleSheet="font-size:5px;"))
            nl.addWidget(QLabel(f"nodo_{i:04d}", styleSheet=f"color:{Tema.TEXTO};font-size:9px;"))
            nl.addWidget(QLabel(f"192.168.{random.randint(1,255)}.{random.randint(1,255)}", styleSheet=f"color:{Tema.TEXTO_SEC};font-size:7px;font-family:'Courier New';"))
            lat = random.randint(5,250)
            col = Tema.VERDE if lat<100 else Tema.DORADO if lat<200 else Tema.ROJO
            nl.addWidget(QLabel(f"{lat}ms", styleSheet=f"color:{col};font-size:7px;font-weight:600;"))
            l.addWidget(n)
        l.addStretch()
        return self._scroll(w)

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    app = QApplication(sys.argv)
    aplicar_tema(app)
    login = VentanaLogin()
    if login.exec() == QDialog.Accepted and login.usuario:
        window = AppDireccoin(login.usuario)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
       