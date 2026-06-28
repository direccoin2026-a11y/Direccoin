#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - VALIDADOR DE DIRECCIONES                     ║
║                    Versión: 1.0.0 | Archivo: core/direcciones.py           ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE VALIDACIÓN DE DIRECCIONES A NIVEL DE RED.

Extiende crypto/direccion.py con funciones específicas de la red:
  • Lista negra de direcciones (bloqueo por consenso)
  • Lista blanca para contratos autorizados
  • Verificación de propiedad (posee la clave privada)
  • Límites de transacciones por dirección
  • Protección anti-spam
  • Diagnóstico de 10 pruebas
"""

import hashlib
import os
import sys
import time
import json
from typing import Dict, List, Optional, Tuple, Set

# Importar módulo crypto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crypto.direccion import Direccion, LoteDirecciones

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigRedDirecciones:
    VERSION = "1.0.0"
    
    # Límites de transacciones
    MAX_TX_POR_BLOQUE_POR_DIRECCION = 100
    MAX_TX_POR_HORA_POR_DIRECCION = 1000
    MIN_SALDO_PARA_TX = 0  # Sin mínimo
    
    # Tamaños
    TAMANO_MAX_DIRECCION_BYTES = 20
    
    # Archivos de listas
    ARCHIVO_LISTA_NEGRA = os.path.join("..", "data", "blacklist.json")
    ARCHIVO_LISTA_BLANCA = os.path.join("..", "data", "whitelist.json")


# ==============================================================================
# UTILIDADES DE HASH (independientes)
# ==============================================================================

class _Hash:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()


# ==============================================================================
# GESTOR DE LISTAS NEGRA Y BLANCA
# ==============================================================================

class ListaControl:
    """
    Gestiona listas negras y blancas de direcciones.
    
    Lista negra: Direcciones bloqueadas por consenso (spam, ataques, robos).
    Lista blanca: Contratos y direcciones autorizadas para operaciones especiales.
    """
    
    def __init__(self):
        self.lista_negra: Set[bytes] = set()
        self.lista_blanca: Set[bytes] = set()
        self.motivos_negra: Dict[str, str] = {}
        self.motivos_blanca: Dict[str, str] = {}
        self._cargar()
    
    def _cargar(self):
        """Carga listas desde archivos si existen."""
        try:
            if os.path.exists(ConfigRedDirecciones.ARCHIVO_LISTA_NEGRA):
                with open(ConfigRedDirecciones.ARCHIVO_LISTA_NEGRA) as f:
                    datos = json.load(f)
                    for entrada in datos:
                        b = Direccion.a_bytes(entrada["direccion"])
                        if b:
                            self.lista_negra.add(b)
                            self.motivos_negra[b.hex()] = entrada.get("motivo", "Desconocido")
        except:
            pass
        
        try:
            if os.path.exists(ConfigRedDirecciones.ARCHIVO_LISTA_BLANCA):
                with open(ConfigRedDirecciones.ARCHIVO_LISTA_BLANCA) as f:
                    datos = json.load(f)
                    for entrada in datos:
                        b = Direccion.a_bytes(entrada["direccion"])
                        if b:
                            self.lista_blanca.add(b)
                            self.motivos_blanca[b.hex()] = entrada.get("motivo", "Desconocido")
        except:
            pass
    
    def esta_en_lista_negra(self, direccion: str) -> bool:
        """Verifica si una dirección está bloqueada."""
        b = Direccion.a_bytes(direccion)
        return b is not None and b in self.lista_negra
    
    def esta_en_lista_blanca(self, direccion: str) -> bool:
        """Verifica si una dirección está en la lista blanca."""
        b = Direccion.a_bytes(direccion)
        return b is not None and b in self.lista_blanca
    
    def agregar_a_lista_negra(self, direccion: str, motivo: str = "Spam"):
        """Añade una dirección a la lista negra."""
        if not Direccion.es_valida(direccion):
            raise ValueError(f"Dirección inválida: {direccion}")
        b = Direccion.a_bytes(direccion)
        self.lista_negra.add(b)
        self.motivos_negra[b.hex()] = motivo
    
    def agregar_a_lista_blanca(self, direccion: str, motivo: str = "Contrato autorizado"):
        """Añade una dirección a la lista blanca."""
        if not Direccion.es_valida(direccion):
            raise ValueError(f"Dirección inválida: {direccion}")
        b = Direccion.a_bytes(direccion)
        self.lista_blanca.add(b)
        self.motivos_blanca[b.hex()] = motivo
    
    def remover_de_lista_negra(self, direccion: str):
        """Elimina una dirección de la lista negra."""
        b = Direccion.a_bytes(direccion)
        if b:
            self.lista_negra.discard(b)
            self.motivos_negra.pop(b.hex(), None)
    
    def guardar(self):
        """Persiste las listas en disco."""
        os.makedirs(os.path.dirname(ConfigRedDirecciones.ARCHIVO_LISTA_NEGRA), exist_ok=True)
        
        negra = [{"direccion": Direccion.desde_hash_publico(b), "motivo": self.motivos_negra.get(b.hex(), "")} 
                 for b in self.lista_negra]
        with open(ConfigRedDirecciones.ARCHIVO_LISTA_NEGRA, "w") as f:
            json.dump(negra, f, indent=2)
        
        blanca = [{"direccion": Direccion.desde_hash_publico(b), "motivo": self.motivos_blanca.get(b.hex(), "")} 
                  for b in self.lista_blanca]
        with open(ConfigRedDirecciones.ARCHIVO_LISTA_BLANCA, "w") as f:
            json.dump(blanca, f, indent=2)


# ==============================================================================
# VALIDADOR DE TRANSACCIONES
# ==============================================================================

class ValidadorTransacciones:
    """
    Valida direcciones en el contexto de transacciones.
    Aplica reglas de red: límites, listas, anti-spam.
    """
    
    def __init__(self):
        self.listas = ListaControl()
        self.contador_tx: Dict[bytes, List[float]] = {}
    
    def validar_direccion_origen(self, direccion: str) -> Tuple[bool, str]:
        """
        Valida que una dirección pueda ser origen de una transacción.
        
        Returns:
            (válido, motivo)
        """
        # Validación básica
        if not Direccion.es_valida(direccion):
            return False, "Dirección inválida"
        
        # No testnet en mainnet
        if Direccion.es_testnet(direccion):
            return False, "Dirección de testnet no permitida en mainnet"
        
        # Lista negra
        if self.listas.esta_en_lista_negra(direccion):
            return False, "Dirección bloqueada por la red"
        
        # Verificar tasa de transacciones
        b = Direccion.a_bytes(direccion)
        if not self._verificar_tasa(b):
            return False, "Excede el límite de transacciones por hora"
        
        return True, "Válida"
    
    def validar_direccion_destino(self, direccion: str) -> Tuple[bool, str]:
        """
        Valida que una dirección pueda ser destino de una transacción.
        Menos restrictiva que el origen.
        """
        if not Direccion.es_valida(direccion):
            return False, "Dirección inválida"
        
        if self.listas.esta_en_lista_negra(direccion):
            return False, "No se puede enviar a una dirección bloqueada"
        
        return True, "Válida"
    
    def validar_transaccion_completa(self, origen: str, destino: str, 
                                     cantidad: int) -> Tuple[bool, str]:
        """
        Valida una transacción completa.
        
        Args:
            origen: Dirección del emisor
            destino: Dirección del receptor
            cantidad: Cantidad en unidades mínimas (Direcs)
        
        Returns:
            (válido, motivo)
        """
        # Validar origen
        ok, msg = self.validar_direccion_origen(origen)
        if not ok:
            return False, f"Origen: {msg}"
        
        # Validar destino
        ok, msg = self.validar_direccion_destino(destino)
        if not ok:
            return False, f"Destino: {msg}"
        
        # No enviar a uno mismo
        if Direccion.comparar(origen, destino):
            return False, "No se puede enviar a la misma dirección"
        
        # Cantidad positiva
        if cantidad <= 0:
            return False, "Cantidad debe ser positiva"
        
        # Registrar transacción
        self._registrar_tx(Direccion.a_bytes(origen))
        
        return True, "Transacción válida"
    
    def _verificar_tasa(self, direccion_bytes: bytes) -> bool:
        """Verifica que la dirección no exceda el límite de transacciones."""
        ahora = time.time()
        una_hora_atras = ahora - 3600
        
        if direccion_bytes not in self.contador_tx:
            return True
        
        # Limpiar transacciones viejas
        self.contador_tx[direccion_bytes] = [
            t for t in self.contador_tx[direccion_bytes] if t > una_hora_atras
        ]
        
        return len(self.contador_tx[direccion_bytes]) < ConfigRedDirecciones.MAX_TX_POR_HORA_POR_DIRECCION
    
    def _registrar_tx(self, direccion_bytes: bytes):
        """Registra una transacción para el contador."""
        if direccion_bytes not in self.contador_tx:
            self.contador_tx[direccion_bytes] = []
        self.contador_tx[direccion_bytes].append(time.time())


# ==============================================================================
# GENERADOR DE DIRECCIONES DE RED
# ==============================================================================

class GeneradorDireccionesRed:
    """
    Genera direcciones especiales para la red Direccoin.
    """
    
    @staticmethod
    def direccion_coinbase(numero_bloque: int) -> str:
        """
        Genera una dirección coinbase única para un bloque.
        Las direcciones coinbase son donde se reciben las recompensas de minado.
        """
        datos = f"DIRECCOIN_COINBASE_{numero_bloque}".encode()
        hash_bytes = _Hash.sha3(datos)[:20]
        return Direccion.desde_hash_publico(hash_bytes)
    
    @staticmethod
    def direccion_contrato(codigo_contrato: bytes) -> str:
        """Genera una dirección para un contrato inteligente."""
        hash_contrato = _Hash.sha3(codigo_contrato)[:20]
        return Direccion.desde_hash_publico(hash_contrato)
    
    @staticmethod
    def direccion_quemado() -> str:
        """Dirección de quemado (nadie tiene la clave privada)."""
        return Direccion.desde_hash_publico(b'\x00' * 20)
    
    @staticmethod
    def direccion_fundacion() -> str:
        """Dirección de la fundación Direccoin (si aplica)."""
        return Direccion.desde_hash_publico(_Hash.sha3(b"DIRECCOIN_FOUNDATION")[:20])


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoDireccionesRed:
    def __init__(self):
        self.ok = 0
        self.fail = 0
    
    def _t(self, n, ok, d=""):
        s = "✅ PASÓ" if ok else "❌ FALLÓ"
        print(f"   {s} | {n}: {d}")
        if ok: self.ok += 1
        else: self.fail += 1
    
    def ejecutar(self) -> bool:
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO DE CORE/DIRECCIONES.PY")
        print("=" * 70)
        
        validador = ValidadorTransacciones()
        
        # Direcciones de prueba
        x, y = os.urandom(32), os.urandom(32)
        dir1 = Direccion.desde_clave_publica(x, y)
        dir2 = Direccion.desde_clave_publica(os.urandom(32), os.urandom(32))
        
        # 1. Validar origen
        ok, msg = validador.validar_direccion_origen(dir1)
        self._t("Validar origen válido", ok, msg)
        
        # 2. Validar destino
        ok, msg = validador.validar_direccion_destino(dir2)
        self._t("Validar destino válido", ok, msg)
        
        # 3. Rechazar origen inválido
        ok, msg = validador.validar_direccion_origen("invalida")
        self._t("Rechazar origen inválido", not ok, msg)
        
        # 4. Rechazar destino inválido
        ok, msg = validador.validar_direccion_destino("invalida")
        self._t("Rechazar destino inválido", not ok, msg)
        
        # 5. Validar transacción completa
        ok, msg = validador.validar_transaccion_completa(dir1, dir2, 100)
        self._t("Validar transacción completa", ok, msg)
        
        # 6. Rechazar envío a uno mismo
        ok, msg = validador.validar_transaccion_completa(dir1, dir1, 100)
        self._t("Rechazar envío a sí mismo", not ok, msg)
        
        # 7. Rechazar cantidad negativa
        ok, msg = validador.validar_transaccion_completa(dir1, dir2, -100)
        self._t("Rechazar cantidad negativa", not ok, msg)
        
        # 8. Lista negra
        validador.listas.agregar_a_lista_negra(dir2, "Prueba")
        ok, msg = validador.validar_direccion_destino(dir2)
        self._t("Bloquear destino en lista negra", not ok, msg)
        validador.listas.remover_de_lista_negra(dir2)
        
        # 9. Generar dirección coinbase
        cb = GeneradorDireccionesRed.direccion_coinbase(0)
        self._t("Dirección coinbase", Direccion.es_valida(cb))
        
        # 10. Dirección de quemado
        quema = GeneradorDireccionesRed.direccion_quemado()
        self._t("Dirección de quemado", Direccion.es_valida(quema))
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0:
            print("✅ CORE/DIRECCIONES.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🏦 " * 35)
    print("DIRECCOIN - VALIDADOR DE DIRECCIONES v1.0.0")
    print("🏦 " * 35)
    print(f"Max TX/hora/dir: {ConfigRedDirecciones.MAX_TX_POR_HORA_POR_DIRECCION}\n")
    
    diag = DiagnosticoDireccionesRed()
    if diag.ejecutar():
        print("📋 DEMO:")
        cb = GeneradorDireccionesRed.direccion_coinbase(0)
        quema = GeneradorDireccionesRed.direccion_quemado()
        print(f"   Coinbase (bloque 0): {Direccion.formatear(cb, 12)}")
        print(f"   Quemado: {Direccion.formatear(quema, 12)}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()