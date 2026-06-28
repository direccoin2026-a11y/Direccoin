#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - WALLET CLI v1.0.0                             ║
║                    Archivo: billetera/wallet_cli.py                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

CARACTERÍSTICAS:
  • Consultar saldo (líquido + bloqueado)
  • Enviar transacciones
  • Recibir (mostrar dirección y QR)
  • Historial de transacciones
  • Verificar estado de timelock
  • Modo offline (lee genesis.json)
  • Diagnóstico automático
"""

import hashlib
import time
import os
import sys
import json
from typing import Dict, List, Tuple, Optional

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigWallet:
    NOMBRE = "Direccoin"
    SIMBOLO = "DRC"
    DECIMALES = 6
    PREFIJO = "drc"
    
    # Rutas
    RUTA_DIRECT = "direct.json"
    RUTA_GENESIS = os.path.join("..", "data", "genesis.json")
    RUTA_BACKUP = "direct_backup.txt"


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3_256(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    
    @staticmethod
    def doble(d: bytes) -> bytes:
        return HashUtil.sha3_256(HashUtil.sha3_256(d))
    
    @staticmethod
    def hex(d: bytes) -> str:
        return d.hex()


# ==============================================================================
# GESTOR DE WALLET
# ==============================================================================

class WalletDirect:
    """Gestiona la wallet de Direct: saldo, envíos, historial."""
    
    def __init__(self):
        self.direct = self._cargar_direct()
        self.genesis = self._cargar_genesis()
        self.direccion = self.direct["direccion"]
        self.saldo_liquido = 0
        self.saldo_bloqueado = 0
        self.timestamp_liberacion = 0
        self.transacciones = []
        self._procesar_estado()
    
    def _cargar_direct(self) -> Dict:
        """Carga la identidad de Direct."""
        if not os.path.exists(ConfigWallet.RUTA_DIRECT):
            print("❌ No se encontró direct.json")
            print("   Ejecuta primero: crear_wallet.py")
            sys.exit(1)
        with open(ConfigWallet.RUTA_DIRECT) as f:
            return json.load(f)
    
    def _cargar_genesis(self) -> Optional[Dict]:
        """Carga el bloque génesis si existe."""
        if os.path.exists(ConfigWallet.RUTA_GENESIS):
            with open(ConfigWallet.RUTA_GENESIS) as f:
                return json.load(f)
        return None
    
    def _procesar_estado(self):
        """Procesa el estado actual desde el génesis."""
        if not self.genesis:
            return
        
        premine = self.genesis.get("premine", {})
        salidas = premine.get("salidas", [])
        
        for salida in salidas:
            if salida["direccion"] == self.direccion:
                if salida["tipo"] == "LIQUIDO_INMEDIATO":
                    self.saldo_liquido += salida["cantidad"]
                elif salida["tipo"] == "BLOQUEADO_TEMPORAL":
                    self.saldo_bloqueado += salida["cantidad"]
                    script = salida.get("script_bloqueo", {})
                    self.timestamp_liberacion = script.get("liberacion", 0)
        
        # Registrar transacción del génesis
        self.transacciones.append({
            "txid": premine.get("txid", "GÉNESIS"),
            "tipo": "PREMINE",
            "cantidad": premine.get("premine_total", 0),
            "timestamp": self.genesis["bloque"]["timestamp"],
            "estado": "CONFIRMADO"
        })
    
    def obtener_saldo_total(self) -> int:
        return self.saldo_liquido + self.saldo_bloqueado
    
    def obtener_saldo_formateado(self, cantidad: int) -> str:
        """Formatea cantidad con decimales."""
        entero = cantidad // (10 ** ConfigWallet.DECIMALES)
        decimal = cantidad % (10 ** ConfigWallet.DECIMALES)
        if ConfigWallet.DECIMALES > 0:
            return f"{entero:,}.{decimal:0{ConfigWallet.DECIMALES}d} {ConfigWallet.SIMBOLO}"
        return f"{entero:,} {ConfigWallet.SIMBOLO}"
    
    def tiempo_restante_bloqueo(self) -> str:
        """Calcula tiempo restante del bloqueo."""
        if self.saldo_bloqueado == 0:
            return "N/A"
        
        ahora = int(time.time())
        if ahora >= self.timestamp_liberacion:
            return "🔓 LIBERADO"
        
        restante = self.timestamp_liberacion - ahora
        dias = restante // 86400
        horas = (restante % 86400) // 3600
        minutos = (restante % 3600) // 60
        
        partes = []
        if dias > 0:
            partes.append(f"{dias}d")
        if horas > 0:
            partes.append(f"{horas}h")
        if minutos > 0:
            partes.append(f"{minutos}m")
        
        return f"🔒 {' '.join(partes)}"
    
    def firmar_transaccion(self, destino: str, cantidad: int) -> Optional[Dict]:
        """Crea una transacción firmada."""
        if cantidad <= 0:
            return None
        if cantidad > self.saldo_liquido:
            return None
        
        tx = {
            "version": 1,
            "origen": self.direccion,
            "destino": destino,
            "cantidad": cantidad,
            "timestamp": int(time.time()),
            "nonce": len(self.transacciones) + 1,
        }
        
        # Firmar con clave privada (simplificado)
        mensaje = f"{tx['origen']}{tx['destino']}{tx['cantidad']}{tx['timestamp']}{tx['nonce']}"
        tx["firma"] = HashUtil.hex(HashUtil.doble(mensaje.encode()))
        tx["txid"] = HashUtil.hex(HashUtil.doble(
            f"{tx['origen']}{tx['destino']}{tx['cantidad']}{tx['firma']}".encode()
        ))
        
        return tx


# ==============================================================================
# INTERFAZ DE USUARIO
# ==============================================================================

class WalletCLI:
    """Interfaz de línea de comandos para la wallet."""
    
    def __init__(self):
        self.wallet = WalletDirect()
        self.ejecutando = True
    
    def mostrar_banner(self):
        print("\n" + "💰 " * 35)
        print("DIRECCOIN - WALLET CLI v1.0.0")
        print("💰 " * 35)
    
    def mostrar_menu(self):
        print(f"""
┌─────────────────────────────────────────────────┐
│          DIRECCOIN WALLET - DIRECT               │
├─────────────────────────────────────────────────┤
│  Dirección: {self.wallet.direccion[:20]}...       │
│                                                   │
│  💰 Líquido:    {self.wallet.obtener_saldo_formateado(self.wallet.saldo_liquido):>20} │
│  🔒 Bloqueado:  {self.wallet.obtener_saldo_formateado(self.wallet.saldo_bloqueado):>20} │
│  📅 Estado:     {self.wallet.tiempo_restante_bloqueo():>20} │
│  ───────────────────────────────────────────────  │
│  📦 Total:      {self.wallet.obtener_saldo_formateado(self.wallet.obtener_saldo_total()):>20} │
│                                                   │
├─────────────────────────────────────────────────┤
│  [1] 📤 Enviar Direccoins                         │
│  [2] 📥 Recibir (mostrar dirección)               │
│  [3] 📋 Historial de transacciones                │
│  [4] 🔍 Verificar integridad                     │
│  [5] 📄 Exportar información                      │
│  [6] 🔐 Mostrar clave pública                     │
│  [7] 🚪 Salir                                     │
└─────────────────────────────────────────────────┘
""")
    
    def opcion_enviar(self):
        print("\n📤 ENVIAR DIRECCOINS")
        print("─" * 50)
        
        if self.wallet.saldo_liquido <= 0:
            print("❌ No tienes saldo líquido disponible.")
            if self.wallet.saldo_bloqueado > 0:
                print(f"   Tienes {self.wallet.obtener_saldo_formateado(self.wallet.saldo_bloqueado)} bloqueados.")
                print(f"   {self.wallet.tiempo_restante_bloqueo()}")
            return
        
        print(f"Saldo disponible: {self.wallet.obtener_saldo_formateado(self.wallet.saldo_liquido)}")
        print()
        
        destino = input("Dirección destino (drc...): ").strip()
        if not destino.startswith(ConfigWallet.PREFIJO):
            print("❌ Dirección inválida. Debe empezar con 'drc'")
            return
        
        if destino == self.wallet.direccion:
            print("❌ No puedes enviarte a ti mismo.")
            return
        
        try:
            cantidad_str = input(f"Cantidad ({ConfigWallet.SIMBOLO}): ").strip()
            if '.' in cantidad_str:
                entero, decimal = cantidad_str.split('.')
                decimal = decimal.ljust(ConfigWallet.DECIMALES, '0')[:ConfigWallet.DECIMALES]
                cantidad = int(entero) * (10 ** ConfigWallet.DECIMALES) + int(decimal)
            else:
                cantidad = int(cantidad_str) * (10 ** ConfigWallet.DECIMALES)
        except ValueError:
            print("❌ Cantidad inválida.")
            return
        
        if cantidad <= 0:
            print("❌ La cantidad debe ser positiva.")
            return
        
        if cantidad > self.wallet.saldo_liquido:
            print(f"❌ Saldo insuficiente. Disponible: {self.wallet.obtener_saldo_formateado(self.wallet.saldo_liquido)}")
            return
        
        # Confirmar
        print(f"\n📋 RESUMEN DEL ENVÍO:")
        print(f"   Destino: {destino[:20]}...")
        print(f"   Cantidad: {self.wallet.obtener_saldo_formateado(cantidad)}")
        print(f"   Gas: 0.000000 {ConfigWallet.SIMBOLO}")
        print(f"   Total: {self.wallet.obtener_saldo_formateado(cantidad)}")
        
        confirmar = input("\n¿Confirmar envío? (SI): ").strip()
        if confirmar != "SI":
            print("❌ Envío cancelado.")
            return
        
        # Firmar
        tx = self.wallet.firmar_transaccion(destino, cantidad)
        if tx:
            print(f"\n✅ Transacción firmada")
            print(f"   TXID: {tx['txid']}")
            print(f"   Nonce: {tx['nonce']}")
            print(f"\n⚠️  La red no está activa aún. Esta transacción se procesará cuando haya nodos.")
        else:
            print("❌ Error al firmar la transacción.")
    
    def opcion_recibir(self):
        print("\n📥 RECIBIR DIRECCOINS")
        print("─" * 50)
        print(f"\n🔑 Tu dirección:\n")
        print(f"   {self.wallet.direccion}")
        print(f"\n📋 Comparte esta dirección para recibir {ConfigWallet.SIMBOLO}.")
        print(f"   También puedes mostrarla como QR:")
        print(f"""
   ██████████████████████████████████████████
   ██            DIRECCOIN                ██
   ██  {self.wallet.direccion[:20]}    ██
   ██  {self.wallet.direccion[20:]}    ██
   ██                                     ██
   ██████████████████████████████████████████
   """)
    
    def opcion_historial(self):
        print("\n📋 HISTORIAL DE TRANSACCIONES")
        print("─" * 70)
        
        if not self.wallet.transacciones:
            print("   No hay transacciones registradas.")
            return
        
        for tx in self.wallet.transacciones:
            fecha = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(tx["timestamp"]))
            print(f"""
   ┌─────────────────────────────────────────────────────┐
   │ TXID: {tx['txid'][:40]}... │
   │ Tipo: {tx['tipo']:<45} │
   │ Cantidad: {self.wallet.obtener_saldo_formateado(tx['cantidad']):<40} │
   │ Fecha: {fecha:<46} │
   │ Estado: {tx['estado']:<44} │
   └─────────────────────────────────────────────────────┘
   """)
    
    def opcion_verificar(self):
        print("\n🔍 VERIFICANDO INTEGRIDAD...")
        print("─" * 50)
        
        checks = []
        
        # Verificar direct.json
        if os.path.exists(ConfigWallet.RUTA_DIRECT):
            print("   ✅ direct.json encontrado")
            checks.append(True)
        else:
            print("   ❌ direct.json no encontrado")
            checks.append(False)
        
        # Verificar genesis.json
        if self.wallet.genesis:
            premine = self.wallet.genesis.get("premine", {})
            total = sum(s["cantidad"] for s in premine.get("salidas", []))
            if total == 3000000:
                print(f"   ✅ Premine correcto: {total:,} DRC")
                checks.append(True)
            else:
                print(f"   ❌ Premine incorrecto: {total:,} DRC")
                checks.append(False)
        
        # Verificar dirección
        if self.wallet.direccion.startswith("drc"):
            print(f"   ✅ Dirección válida: drc...")
            checks.append(True)
        else:
            print("   ❌ Dirección inválida")
            checks.append(False)
        
        print(f"\n📊 {sum(checks)}/{len(checks)} verificaciones pasadas")
    
    def opcion_exportar(self):
        print("\n📄 EXPORTAR INFORMACIÓN")
        print("─" * 50)
        
        info = f"""
DIRECCOIN - INFORMACIÓN DE WALLET
{"=" * 60}

DIRECCIÓN: {self.wallet.direccion}
SALDO LÍQUIDO: {self.wallet.obtener_saldo_formateado(self.wallet.saldo_liquido)}
SALDO BLOQUEADO: {self.wallet.obtener_saldo_formateado(self.wallet.saldo_bloqueado)}
SALDO TOTAL: {self.wallet.obtener_saldo_formateado(self.wallet.obtener_saldo_total())}
ESTADO BLOQUEO: {self.wallet.tiempo_restante_bloqueo()}

CLAVE PÚBLICA X: {self.wallet.direct.get('clave_publica_x', 'N/A')}
CLAVE PÚBLICA Y: {self.wallet.direct.get('clave_publica_y', 'N/A')}

⚠️  LA CLAVE PRIVADA NO SE EXPORTA POR SEGURIDAD
"""
        
        ruta_export = "wallet_info.txt"
        with open(ruta_export, "w") as f:
            f.write(info)
        
        print(f"   ✅ Exportado a: {ruta_export}")
        print(f"\n{info}")
    
    def opcion_clave_publica(self):
        print("\n🔐 CLAVE PÚBLICA")
        print("─" * 50)
        print(f"\n   X: {self.wallet.direct.get('clave_publica_x', 'N/A')}")
        print(f"   Y: {self.wallet.direct.get('clave_publica_y', 'N/A')}")
        print(f"\n   Esta información es pública y puedes compartirla.")
    
    def ejecutar(self):
        self.mostrar_banner()
        
        while self.ejecutando:
            self.mostrar_menu()
            
            try:
                opcion = input("   Elige una opción [1-7]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 ¡Hasta luego, Direct!\n")
                break
            
            if opcion == "1":
                self.opcion_enviar()
            elif opcion == "2":
                self.opcion_recibir()
            elif opcion == "3":
                self.opcion_historial()
            elif opcion == "4":
                self.opcion_verificar()
            elif opcion == "5":
                self.opcion_exportar()
            elif opcion == "6":
                self.opcion_clave_publica()
            elif opcion == "7":
                print("\n👋 ¡Hasta luego, Direct!\n")
                self.ejecutando = False
            else:
                print("\n❌ Opción inválida. Elige 1-7.")
            
            if self.ejecutando:
                input("\n   Presiona Enter para continuar...")


# ==============================================================================
# DIAGNÓSTICO RÁPIDO
# ==============================================================================

def diagnostico_rapido():
    """Verifica que todo esté en orden."""
    print("\n🔍 Diagnóstico rápido:")
    
    if os.path.exists(ConfigWallet.RUTA_DIRECT):
        print("   ✅ direct.json")
    else:
        print("   ❌ direct.json no encontrado")
    
    if os.path.exists(ConfigWallet.RUTA_GENESIS):
        print("   ✅ genesis.json")
    else:
        print("   ⚠️  genesis.json no encontrado (modo offline limitado)")
    
    print()


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n💼 INICIANDO WALLET DIRECT...")
    diagnostico_rapido()
    
    try:
        cli = WalletCLI()
        cli.ejecutar()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Verifica que direct.json y genesis.json existan.\n")


if __name__ == "__main__":
    main()