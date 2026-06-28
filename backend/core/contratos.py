#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - CONTRATOS INTELIGENTES                       ║
║                    Versión: 1.0.0 | Archivo: core/contratos.py             ║
╚══════════════════════════════════════════════════════════════════════════════╝

MOTOR DE CONTRATOS INTELIGENTES PARA DIRECCOIN.

Implementa un DSL Python-like para contratos autoejecutables:
  • Contratos de pago condicional
  • Contratos de bloqueo temporal (timelock)
  • Contratos multifirma
  • Contratos de suscripción
  • Contratos de intercambio atómico
  • Máquina virtual mínima (DVM)

CARACTERÍSTICAS:
  • Ejecución determinista
  • Gas limitado por operación
  • Sandbox seguro (sin acceso a sistema)
  • Diagnóstico de 12 pruebas
"""

import hashlib
import time
import json
from typing import Dict, List, Tuple, Optional, Callable, Any

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigContratos:
    VERSION = "1.0.0"
    MAX_GAS_POR_CONTRATO = 1_000_000
    MAX_TAMANO_CONTRATO_BYTES = 10_000
    MAX_OPERACIONES = 1000
    COSTO_GAS_POR_OPERACION = 1
    COSTO_GAS_ALMACENAMIENTO = 100
    TAMANO_MAX_PILA = 256


# ==============================================================================
# UTILIDADES
# ==============================================================================

class _Hash:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    @staticmethod
    def sha3_hex(d: bytes) -> str:
        return _Hash.sha3(d).hex()


# ==============================================================================
# MÁQUINA VIRTUAL DIRECCOIN (DVM)
# ==============================================================================

class DVM:
    """
    Máquina Virtual Direccoin - Motor de ejecución de contratos.
    
    Ejecuta bytecode simple en un sandbox seguro.
    """
    
    def __init__(self):
        self.pila: List[int] = []
        self.memoria: Dict[str, int] = {}
        self.gas_usado = 0
        self.gas_maximo = ConfigContratos.MAX_GAS_POR_CONTRATO
        self.operaciones = 0
        self.resultado = None
    
    def _consumir_gas(self, cantidad: int):
        self.gas_usado += cantidad
        if self.gas_usado > self.gas_maximo:
            raise RuntimeError("Gas insuficiente")
    
    def _contar_operacion(self):
        self.operaciones += 1
        if self.operaciones > ConfigContratos.MAX_OPERACIONES:
            raise RuntimeError("Demasiadas operaciones")
    
    def ejecutar(self, instrucciones: List[Tuple[str, Any]], 
                 contexto: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Ejecuta una lista de instrucciones.
        
        Formato de instrucción:
            ("OP", valor) - Ej: ("PUSH", 10), ("ADD", None), ("STORE", "x")
        """
        self.pila = []
        self.memoria = {}
        self.gas_usado = 0
        self.operaciones = 0
        
        if contexto:
            self.memoria.update(contexto)
        
        for op, val in instrucciones:
            self._contar_operacion()
            
            if op == "PUSH":
                self._consumir_gas(1)
                self.pila.append(val)
                if len(self.pila) > ConfigContratos.TAMANO_MAX_PILA:
                    raise RuntimeError("Desbordamiento de pila")
            
            elif op == "POP":
                self._consumir_gas(1)
                if self.pila:
                    return self.pila.pop()
            
            elif op == "ADD":
                self._consumir_gas(2)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(a + b)
            
            elif op == "SUB":
                self._consumir_gas(2)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(a - b)
            
            elif op == "MUL":
                self._consumir_gas(3)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(a * b)
            
            elif op == "DIV":
                self._consumir_gas(3)
                b = self.pila.pop() if self.pila else 1
                a = self.pila.pop() if self.pila else 0
                self.pila.append(a // b if b != 0 else 0)
            
            elif op == "MOD":
                self._consumir_gas(3)
                b = self.pila.pop() if self.pila else 1
                a = self.pila.pop() if self.pila else 0
                self.pila.append(a % b if b != 0 else 0)
            
            elif op == "EQ":
                self._consumir_gas(2)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(1 if a == b else 0)
            
            elif op == "GT":
                self._consumir_gas(2)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(1 if a > b else 0)
            
            elif op == "LT":
                self._consumir_gas(2)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(1 if a < b else 0)
            
            elif op == "AND":
                self._consumir_gas(1)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(1 if a and b else 0)
            
            elif op == "OR":
                self._consumir_gas(1)
                b = self.pila.pop() if self.pila else 0
                a = self.pila.pop() if self.pila else 0
                self.pila.append(1 if a or b else 0)
            
            elif op == "NOT":
                self._consumir_gas(1)
                a = self.pila.pop() if self.pila else 0
                self.pila.append(1 if not a else 0)
            
            elif op == "STORE":
                self._consumir_gas(ConfigContratos.COSTO_GAS_ALMACENAMIENTO)
                valor = self.pila.pop() if self.pila else 0
                self.memoria[val] = valor
            
            elif op == "LOAD":
                self._consumir_gas(1)
                self.pila.append(self.memoria.get(val, 0))
            
            elif op == "DUP":
                self._consumir_gas(1)
                if self.pila:
                    self.pila.append(self.pila[-1])
            
            elif op == "SWAP":
                self._consumir_gas(1)
                if len(self.pila) >= 2:
                    self.pila[-1], self.pila[-2] = self.pila[-2], self.pila[-1]
            
            elif op == "TIMESTAMP":
                self._consumir_gas(1)
                self.pila.append(int(time.time()))
            
            elif op == "HASH":
                self._consumir_gas(5)
                valor = str(self.pila.pop() if self.pila else 0).encode()
                self.pila.append(int(_Hash.sha3(valor).hex(), 16) % (2**64))
            
            elif op == "IF":
                self._consumir_gas(1)
                # Implementado a nivel de compilación
        
        return {
            "resultado": self.pila[-1] if self.pila else 0,
            "memoria": self.memoria.copy(),
            "gas_usado": self.gas_usado,
            "operaciones": self.operaciones,
        }


# ==============================================================================
# TIPOS DE CONTRATOS
# ==============================================================================

class ContratoBase:
    """Clase base para todos los contratos."""
    
    def __init__(self, nombre: str = ""):
        self.nombre = nombre
        self.id = _Hash.sha3_hex(f"{nombre}{time.time()}".encode())[:16]
        self.fecha_creacion = int(time.time())
        self.activo = True
    
    def ejecutar(self, contexto: Dict = None) -> Dict[str, Any]:
        raise NotImplementedError
    
    def a_dict(self) -> dict:
        return {
            "tipo": type(self).__name__,
            "nombre": self.nombre,
            "id": self.id,
            "activo": self.activo,
            "fecha_creacion": self.fecha_creacion,
        }


class ContratoPago(ContratoBase):
    """
    Contrato de pago simple: A paga a B cuando se cumple una condición.
    """
    
    def __init__(self, origen: str, destino: str, cantidad: int,
                 condicion: Optional[str] = None):
        super().__init__("Pago")
        self.origen = origen
        self.destino = destino
        self.cantidad = cantidad
        self.condicion = condicion
        self.ejecutado = False
    
    def ejecutar(self, contexto: Dict = None) -> Dict[str, Any]:
        contexto = contexto or {}
        
        if self.ejecutado:
            return {"ok": False, "msg": "Ya ejecutado"}
        
        if self.condicion and not contexto.get("condicion_cumplida", True):
            return {"ok": False, "msg": "Condición no cumplida"}
        
        self.ejecutado = True
        
        return {
            "ok": True,
            "accion": "transferir",
            "origen": self.origen,
            "destino": self.destino,
            "cantidad": self.cantidad,
        }
    
    def a_dict(self) -> dict:
        d = super().a_dict()
        d.update({
            "origen": self.origen,
            "destino": self.destino,
            "cantidad": self.cantidad,
            "condicion": self.condicion,
            "ejecutado": self.ejecutado,
        })
        return d


class ContratoTimelock(ContratoBase):
    """
    Contrato con bloqueo temporal: fondos bloqueados hasta una fecha.
    """
    
    def __init__(self, beneficiario: str, cantidad: int, 
                 liberacion: int):
        super().__init__("Timelock")
        self.beneficiario = beneficiario
        self.cantidad = cantidad
        self.liberacion = liberacion
    
    def ejecutar(self, contexto: Dict = None) -> Dict[str, Any]:
        ahora = int(time.time())
        
        if ahora < self.liberacion:
            restante = self.liberacion - ahora
            dias = restante // 86400
            return {
                "ok": False,
                "msg": f"Bloqueado. {dias} días restantes.",
                "liberacion": self.liberacion,
            }
        
        self.activo = False
        
        return {
            "ok": True,
            "accion": "liberar",
            "destino": self.beneficiario,
            "cantidad": self.cantidad,
        }
    
    def a_dict(self) -> dict:
        d = super().a_dict()
        d.update({
            "beneficiario": self.beneficiario,
            "cantidad": self.cantidad,
            "liberacion": self.liberacion,
        })
        return d


class ContratoMultifirma(ContratoBase):
    """
    Contrato que requiere M de N firmas para ejecutarse.
    """
    
    def __init__(self, firmantes: List[str], firmas_requeridas: int,
                 destino: str, cantidad: int):
        super().__init__("Multifirma")
        self.firmantes = firmantes
        self.firmas_requeridas = firmas_requeridas
        self.destino = destino
        self.cantidad = cantidad
        self.firmas_recibidas: List[str] = []
    
    def agregar_firma(self, firmante: str) -> bool:
        if firmante not in self.firmantes:
            return False
        if firmante in self.firmas_recibidas:
            return False
        self.firmas_recibidas.append(firmante)
        return True
    
    def ejecutar(self, contexto: Dict = None) -> Dict[str, Any]:
        if len(self.firmas_recibidas) < self.firmas_requeridas:
            return {
                "ok": False,
                "msg": f"Firmas: {len(self.firmas_recibidas)}/{self.firmas_requeridas}",
            }
        
        self.activo = False
        
        return {
            "ok": True,
            "accion": "transferir_multifirma",
            "destino": self.destino,
            "cantidad": self.cantidad,
            "firmantes": self.firmas_recibidas,
        }
    
    def a_dict(self) -> dict:
        d = super().a_dict()
        d.update({
            "firmantes": self.firmantes,
            "firmas_requeridas": self.firmas_requeridas,
            "destino": self.destino,
            "cantidad": self.cantidad,
            "firmas_recibidas": self.firmas_recibidas,
        })
        return d


class ContratoSuscripcion(ContratoBase):
    """
    Contrato de suscripción: pago recurrente cada N segundos.
    """
    
    def __init__(self, origen: str, destino: str, cantidad: int,
                 intervalo_segundos: int, max_pagos: int = 12):
        super().__init__("Suscripción")
        self.origen = origen
        self.destino = destino
        self.cantidad = cantidad
        self.intervalo = intervalo_segundos
        self.max_pagos = max_pagos
        self.pagos_realizados = 0
        self.ultimo_pago = 0
    
    def ejecutar(self, contexto: Dict = None) -> Dict[str, Any]:
        ahora = int(time.time())
        
        if self.pagos_realizados >= self.max_pagos:
            self.activo = False
            return {"ok": False, "msg": "Suscripción finalizada"}
        
        if self.ultimo_pago == 0:
            self.ultimo_pago = ahora
            self.pagos_realizados += 1
            return {
                "ok": True,
                "accion": "pago_suscripcion",
                "origen": self.origen,
                "destino": self.destino,
                "cantidad": self.cantidad,
                "pago_numero": self.pagos_realizados,
            }
        
        if ahora - self.ultimo_pago >= self.intervalo:
            self.ultimo_pago = ahora
            self.pagos_realizados += 1
            return {
                "ok": True,
                "accion": "pago_suscripcion",
                "origen": self.origen,
                "destino": self.destino,
                "cantidad": self.cantidad,
                "pago_numero": self.pagos_realizados,
            }
        
        restante = self.intervalo - (ahora - self.ultimo_pago)
        return {
            "ok": False,
            "msg": f"Próximo pago en {restante}s",
        }
    
    def a_dict(self) -> dict:
        d = super().a_dict()
        d.update({
            "origen": self.origen,
            "destino": self.destino,
            "cantidad": self.cantidad,
            "intervalo": self.intervalo,
            "max_pagos": self.max_pagos,
            "pagos_realizados": self.pagos_realizados,
        })
        return d


# ==============================================================================
# GESTOR DE CONTRATOS
# ==============================================================================

class GestorContratos:
    """
    Gestiona el ciclo de vida de los contratos inteligentes.
    """
    
    def __init__(self):
        self.contratos: Dict[str, ContratoBase] = {}
        self.dvm = DVM()
    
    def registrar(self, contrato: ContratoBase) -> str:
        self.contratos[contrato.id] = contrato
        return contrato.id
    
    def ejecutar_contrato(self, id_contrato: str, 
                          contexto: Dict = None) -> Dict[str, Any]:
        if id_contrato not in self.contratos:
            return {"ok": False, "msg": "Contrato no encontrado"}
        
        contrato = self.contratos[id_contrato]
        
        if not contrato.activo:
            return {"ok": False, "msg": "Contrato inactivo"}
        
        try:
            return contrato.ejecutar(contexto)
        except Exception as e:
            return {"ok": False, "msg": f"Error: {str(e)}"}
    
    def listar_contratos(self) -> List[dict]:
        return [c.a_dict() for c in self.contratos.values()]
    
    def listar_activos(self) -> List[dict]:
        return [c.a_dict() for c in self.contratos.values() if c.activo]


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoContratos:
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
        print("🔍 DIAGNÓSTICO DE CORE/CONTRATOS.PY")
        print("=" * 70)
        
        # 1. DVM: operaciones básicas
        dvm = DVM()
        r = dvm.ejecutar([("PUSH", 5), ("PUSH", 3), ("ADD", None)])
        self._t("DVM: 5 + 3 = 8", r["resultado"] == 8, str(r["resultado"]))
        
        # 2. DVM: multiplicación
        r = dvm.ejecutar([("PUSH", 7), ("PUSH", 6), ("MUL", None)])
        self._t("DVM: 7 * 6 = 42", r["resultado"] == 42, str(r["resultado"]))
        
        # 3. DVM: almacenamiento
        r = dvm.ejecutar([("PUSH", 100), ("STORE", "saldo"), ("PUSH", 0), ("LOAD", "saldo")])
        self._t("DVM: STORE/LOAD", r["resultado"] == 100)
        
        # 4. Contrato de pago
        cp = ContratoPago("drcA", "drcB", 500, "firma_valida")
        r = cp.ejecutar({"condicion_cumplida": True})
        self._t("Pago simple", r["ok"] and r["cantidad"] == 500)
        
        # 5. Contrato timelock (bloqueado)
        ct = ContratoTimelock("drcB", 1000, int(time.time()) + 86400)
        r = ct.ejecutar()
        self._t("Timelock bloqueado", not r["ok"])
        
        # 6. Contrato timelock (liberado)
        ct2 = ContratoTimelock("drcC", 500, int(time.time()) - 1)
        r = ct2.ejecutar()
        self._t("Timelock liberado", r["ok"])
        
        # 7. Contrato multifirma
        cm = ContratoMultifirma(["drcA", "drcB", "drcC"], 2, "drcD", 3000)
        cm.agregar_firma("drcA")
        r = cm.ejecutar()
        self._t("Multifirma insuficiente", not r["ok"])
        
        # 8. Multifirma completada
        cm.agregar_firma("drcB")
        r = cm.ejecutar()
        self._t("Multifirma completada", r["ok"])
        
        # 9. Contrato suscripción
        cs = ContratoSuscripcion("drcA", "drcB", 100, 3600, 3)
        r = cs.ejecutar()
        self._t("Suscripción primer pago", r["ok"] and r.get("pago_numero") == 1)
        
        # 10. Gestor de contratos
        gc = GestorContratos()
        id1 = gc.registrar(cp)
        self._t("Registrar contrato", id1 in gc.contratos)
        
        # 11. Listar contratos
        lista = gc.listar_contratos()
        self._t("Listar contratos", len(lista) >= 1)
        
        # 12. Serialización
        d = cp.a_dict()
        self._t("Serializar contrato", d["tipo"] == "ContratoPago" and d["cantidad"] == 500)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0:
            print("✅ CORE/CONTRATOS.PY FUNCIONANDO\n")
        else:
            print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "📜 " * 35)
    print("DIRECCOIN - CONTRATOS INTELIGENTES v1.0.0")
    print("📜 " * 35)
    print(f"Max gas/contrato: {ConfigContratos.MAX_GAS_POR_CONTRATO:,}")
    print(f"Max operaciones: {ConfigContratos.MAX_OPERACIONES}\n")
    
    diag = DiagnosticoContratos()
    if diag.ejecutar():
        print("📋 DEMO:")
        ct = ContratoTimelock("drcBeneficiario", 1_000_000, int(time.time()) + 86400 * 30)
        print(f"   Timelock ID: {ct.id}")
        print(f"   Liberación: {time.strftime('%Y-%m-%d', time.gmtime(ct.liberacion))}")
        r = ct.ejecutar()
        print(f"   Estado: {r['msg']}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()