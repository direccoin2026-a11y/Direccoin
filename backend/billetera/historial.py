#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - HISTORIAL DE TRANSACCIONES                   ║
║                    Versión: 1.0.2 | Archivo: billetera/historial.py        ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE GESTIÓN DE HISTORIAL DE TRANSACCIONES PARA DIRECCOIN.
"""

import os
import json
import time
import csv
from typing import Dict, List, Optional, Any
from io import StringIO

class ConfigHistorial:
    VERSION = "1.0.2"
    MAX_REGISTROS = 100_000
    ARCHIVO_HISTORIAL = "historial_transacciones.json"
    ARCHIVO_EXPORTACION = "historial_export"
    FORMATOS_EXPORTACION = ["json", "csv"]


class RegistroTransaccion:
    def __init__(self, txid: str, origen: str, destino: str, cantidad: int,
                 timestamp: int = None, tipo: str = "envio", estado: str = "pendiente",
                 bloque: int = None, gas: int = 0, nota: str = ""):
        self.txid = txid
        self.origen = origen
        self.destino = destino
        self.cantidad = cantidad
        self.timestamp = timestamp or int(time.time())
        self.tipo = tipo
        self.estado = estado
        self.bloque = bloque
        self.gas = gas
        self.nota = nota
    
    def a_dict(self) -> dict:
        return {
            "txid": self.txid,
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.timestamp)),
            "timestamp": self.timestamp,
            "tipo": self.tipo,
            "origen": self.origen,
            "destino": self.destino,
            "cantidad": self.cantidad,
            "estado": self.estado,
            "bloque": self.bloque,
            "gas": self.gas,
            "nota": self.nota,
        }
    
    @classmethod
    def desde_dict(cls, datos: dict) -> 'RegistroTransaccion':
        return cls(
            txid=datos["txid"],
            origen=datos["origen"],
            destino=datos["destino"],
            cantidad=datos["cantidad"],
            timestamp=datos.get("timestamp"),
            tipo=datos.get("tipo", "envio"),
            estado=datos.get("estado", "pendiente"),
            bloque=datos.get("bloque"),
            gas=datos.get("gas", 0),
            nota=datos.get("nota", ""),
        )


class GestorHistorial:
    
    def __init__(self, direccion_propia: str = "", persistente: bool = True):
        self.direccion_propia = direccion_propia
        self.transacciones: List[RegistroTransaccion] = []
        self.persistente = persistente
        self.archivo = ConfigHistorial.ARCHIVO_HISTORIAL
        if self.persistente:
            self._cargar()
    
    def _cargar(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r") as f:
                    datos = json.load(f)
                self.transacciones = [RegistroTransaccion.desde_dict(tx) for tx in datos]
            except:
                self.transacciones = []
    
    def _guardar(self):
        if not self.persistente:
            return
        datos = [tx.a_dict() for tx in self.transacciones]
        if len(datos) > ConfigHistorial.MAX_REGISTROS:
            datos = datos[-ConfigHistorial.MAX_REGISTROS:]
            self.transacciones = self.transacciones[-ConfigHistorial.MAX_REGISTROS:]
        with open(self.archivo, "w") as f:
            json.dump(datos, f, indent=2)
    
    def agregar(self, txid: str, origen: str, destino: str, cantidad: int,
                tipo: str = "envio", estado: str = "pendiente",
                bloque: int = None, gas: int = 0, nota: str = "") -> RegistroTransaccion:
        if tipo == "envio" and self.direccion_propia:
            if destino == self.direccion_propia: tipo = "recepcion"
            elif origen == self.direccion_propia: tipo = "envio"
        
        registro = RegistroTransaccion(
            txid=txid, origen=origen, destino=destino, cantidad=cantidad,
            tipo=tipo, estado=estado, bloque=bloque, gas=gas, nota=nota
        )
        self.transacciones.append(registro)
        self._guardar()
        return registro
    
    def buscar(self, direccion: str = None, tipo: str = None,
               estado: str = None, desde: int = None, hasta: int = None,
               cantidad_min: int = None, cantidad_max: int = None,
               limite: int = 50, pagina: int = 0) -> Dict[str, Any]:
        resultados = self.transacciones[:]
        if direccion:
            resultados = [tx for tx in resultados
                         if direccion in tx.origen or direccion in tx.destino]
        if tipo:
            resultados = [tx for tx in resultados if tx.tipo == tipo]
        if estado:
            resultados = [tx for tx in resultados if tx.estado == estado]
        if desde:
            resultados = [tx for tx in resultados if tx.timestamp >= desde]
        if hasta:
            resultados = [tx for tx in resultados if tx.timestamp <= hasta]
        if cantidad_min is not None:
            resultados = [tx for tx in resultados if tx.cantidad >= cantidad_min]
        if cantidad_max is not None:
            resultados = [tx for tx in resultados if tx.cantidad <= cantidad_max]
        
        resultados.sort(key=lambda tx: tx.timestamp, reverse=True)
        total = len(resultados)
        inicio = pagina * limite
        fin = inicio + limite
        
        return {
            "total": total,
            "pagina": pagina,
            "limite": limite,
            "total_paginas": (total + limite - 1) // limite if limite > 0 else 0,
            "resultados": [tx.a_dict() for tx in resultados[inicio:fin]],
        }
    
    def buscar_por_txid(self, txid: str) -> Optional[Dict]:
        for tx in self.transacciones:
            if tx.txid == txid:
                return tx.a_dict()
        return None
    
    def obtener_balance_historico(self, direccion: str = None) -> Dict[str, Any]:
        if direccion is None:
            direccion = self.direccion_propia
        enviado = 0
        recibido = 0
        comisiones = 0
        for tx in self.transacciones:
            if tx.origen == direccion:
                enviado += tx.cantidad
                comisiones += tx.gas
            if tx.destino == direccion:
                recibido += tx.cantidad
        return {
            "direccion": direccion,
            "total_enviado": enviado,
            "total_recibido": recibido,
            "total_comisiones": comisiones,
            "balance_neto": recibido - enviado - comisiones,
            "num_transacciones": len(self.transacciones),
        }
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        if not self.transacciones:
            return {"total": 0}
        tipos = {}
        estados = {}
        cantidades = [tx.cantidad for tx in self.transacciones]
        timestamps = [tx.timestamp for tx in self.transacciones]
        for tx in self.transacciones:
            tipos[tx.tipo] = tipos.get(tx.tipo, 0) + 1
            estados[tx.estado] = estados.get(tx.estado, 0) + 1
        return {
            "total_transacciones": len(self.transacciones),
            "primera_fecha": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(min(timestamps))),
            "ultima_fecha": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(max(timestamps))),
            "cantidad_maxima": max(cantidades),
            "cantidad_minima": min(cantidades),
            "cantidad_promedio": sum(cantidades) // len(cantidades),
            "por_tipo": tipos,
            "por_estado": estados,
        }
    
    def exportar_json(self, ruta: str = None) -> str:
        if ruta is None:
            ruta = f"{ConfigHistorial.ARCHIVO_EXPORTACION}.json"
        with open(ruta, "w") as f:
            json.dump([tx.a_dict() for tx in self.transacciones], f, indent=2, ensure_ascii=False)
        return ruta
    
    def exportar_csv(self, ruta: str = None) -> str:
        if ruta is None:
            ruta = f"{ConfigHistorial.ARCHIVO_EXPORTACION}.csv"
        with open(ruta, "w", newline="") as f:
            campos = ["txid", "fecha", "tipo", "origen", "destino",
                     "cantidad", "estado", "bloque", "gas", "nota"]
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
            writer.writeheader()
            for tx in self.transacciones:
                writer.writerow(tx.a_dict())
        return ruta
    
    def exportar_csv_string(self) -> str:
        output = StringIO()
        campos = ["txid", "fecha", "tipo", "origen", "destino",
                 "cantidad", "estado", "bloque", "gas", "nota"]
        writer = csv.DictWriter(output, fieldnames=campos, extrasaction='ignore')
        writer.writeheader()
        for tx in self.transacciones:
            writer.writerow(tx.a_dict())
        return output.getvalue()
    
    def limpiar(self):
        self.transacciones = []
        if os.path.exists(self.archivo):
            os.remove(self.archivo)
    
    def total(self) -> int:
        return len(self.transacciones)


class DiagnosticoHistorial:
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
        print("🔍 DIAGNÓSTICO DE BILLETERA/HISTORIAL.PY")
        print("=" * 70)
        
        hist = GestorHistorial("drcTestPropia", persistente=False)
        
        hist.agregar("tx001", "drcTestPropia", "drcB", 1000, tipo="envio", estado="confirmado")
        self._t("Agregar transacción", hist.total() == 1)
        
        hist.agregar("tx002", "drcA", "drcTestPropia", 500, tipo="recepcion", estado="confirmado")
        hist.agregar("tx003", "drcTestPropia", "drcC", 200, tipo="envio", estado="pendiente")
        hist.agregar("tx004", "drcD", "drcTestPropia", 1500, tipo="recepcion", estado="confirmado")
        self._t("Agregar múltiples", hist.total() == 4)
        
        r = hist.buscar(direccion="drcTestPropia")
        self._t("Buscar por dirección", r["total"] == 4)
        
        r = hist.buscar(tipo="envio")
        self._t("Buscar por tipo envio", r["total"] == 2)
        
        r = hist.buscar(estado="confirmado")
        self._t("Buscar por estado", r["total"] == 3)
        
        tx = hist.buscar_por_txid("tx001")
        self._t("Buscar por TXID", tx is not None and tx["cantidad"] == 1000)
        
        bal = hist.obtener_balance_historico()
        self._t("Balance histórico", bal["total_enviado"] == 1200 and bal["total_recibido"] == 2000)
        
        stats = hist.obtener_estadisticas()
        self._t("Estadísticas", stats["total_transacciones"] == 4)
        
        aj = hist.exportar_json("test_historial.json")
        self._t("Exportar JSON", os.path.exists(aj))
        
        ac = hist.exportar_csv("test_historial.csv")
        self._t("Exportar CSV", os.path.exists(ac))
        
        cs = hist.exportar_csv_string()
        self._t("Exportar CSV string", len(cs) > 0 and "txid" in cs)
        
        hist.limpiar()
        self._t("Limpiar historial", hist.total() == 0)
        
        for a in ["test_historial.json", "test_historial.csv", ConfigHistorial.ARCHIVO_HISTORIAL]:
            if os.path.exists(a): os.remove(a)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ BILLETERA/HISTORIAL.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


def main():
    print("\n" + "📋 " * 35)
    print("DIRECCOIN - HISTORIAL DE TRANSACCIONES v1.0.2")
    print("📋 " * 35)
    print(f"Max registros: {ConfigHistorial.MAX_REGISTROS:,}\n")
    
    diag = DiagnosticoHistorial()
    if diag.ejecutar():
        hist = GestorHistorial("drcDemo", persistente=False)
        hist.agregar("tx_demo_001", "drcDemo", "drcTienda", 500, tipo="envio", estado="confirmado", nota="Café")
        hist.agregar("tx_demo_002", "drcAmigo", "drcDemo", 2000, tipo="recepcion", estado="confirmado", nota="Regalo")
        print("📋 DEMO:")
        print(f"   Total: {hist.total()} transacciones")
        print(f"   Balance neto: {hist.obtener_balance_historico()['balance_neto']} Direcs")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()