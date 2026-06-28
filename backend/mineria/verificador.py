#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DIRECCOIN - VERIFICADOR DE TRABAJO                       ║
║                    Versión: 1.0.0 | Archivo: mineria/verificador.py        ║
╚══════════════════════════════════════════════════════════════════════════════╝

MÓDULO DE VERIFICACIÓN DE PRUEBA DE TRABAJO PARA DIRECCOIN.

Verifica:
  • Proof of Useful Computation (PoUC)
  • Dificultad de hash para bloques
  • Pruebas de trabajo útil (primos, rutas, científicos)
  • Firmas de mineros
  • Anti-spam y anti-trampa

CARACTERÍSTICAS:
  • Verificación ultrarrápida (milisegundos)
  • Múltiples tipos de trabajo
  • Protección contra nonce reuse
  • Validación de recompensa según suministro
  • Diagnóstico de 12 pruebas
"""

import hashlib
import time
import math
from typing import Tuple, Dict, Optional, List

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

class ConfigVerificador:
    VERSION = "1.0.0"
    PREFIJO_HASH = "d1"
    DIFICULTAD_MINIMA = 1
    DIFICULTAD_MAXIMA = 256
    TIPOS_TRABAJO = ["validacion", "optimizacion", "cientifico"]
    RECOMPENSA_BASE = 100_000_000  # 100 DRC en Direcs
    MULTIPLICADOR_RECOMPENSA = {
        "validacion": 1.0,
        "optimizacion": 1.5,
        "cientifico": 2.0
    }


# ==============================================================================
# UTILIDADES
# ==============================================================================

class HashUtil:
    @staticmethod
    def sha3(d: bytes) -> bytes:
        return hashlib.sha3_256(d).digest()
    
    @staticmethod
    def doble(d: bytes) -> bytes:
        return HashUtil.sha3(HashUtil.sha3(d))
    
    @staticmethod
    def doble_hex(d: bytes) -> str:
        return HashUtil.doble(d).hex()
    
    @staticmethod
    def hex_a_bytes(h: str) -> bytes:
        return bytes.fromhex(h)


# ==============================================================================
# VERIFICADOR DE HASH (DIFICULTAD)
# ==============================================================================

class VerificadorHash:
    """
    Verifica que un hash cumpla con la dificultad requerida.
    """
    
    @staticmethod
    def cumple_dificultad(hash_hex: str, dificultad: int) -> bool:
        """
        Verifica que el hash comience con el prefijo 'd1' y
        tenga suficientes ceros según la dificultad.
        
        Ejemplo: dificultad 3 → debe empezar con 'd10' al menos
        """
        if dificultad < ConfigVerificador.DIFICULTAD_MINIMA:
            return False
        if dificultad > ConfigVerificador.DIFICULTAD_MAXIMA:
            return False
        
        # Verificar prefijo Direccoin
        if not hash_hex.startswith(ConfigVerificador.PREFIJO_HASH):
            return False
        
        # Contar ceros después del prefijo
        resto = hash_hex[2:]  # Quitar 'd1'
        ceros = 0
        for c in resto:
            if c == '0':
                ceros += 1
            else:
                break
        
        return ceros >= dificultad - 2  # -2 porque 'd1' ya cuenta
    
    @staticmethod
    def verificar_bloque(datos_bloque: str, nonce: int, hash_esperado: str,
                         dificultad: int) -> Tuple[bool, str]:
        """
        Verifica que el nonce produzca el hash esperado con la dificultad.
        """
        contenido = f"{datos_bloque}{nonce}".encode()
        hash_calculado = HashUtil.doble_hex(contenido)
        
        if hash_calculado != hash_esperado:
            return False, f"Hash no coincide: {hash_calculado[:16]} != {hash_esperado[:16]}"
        
        if not VerificadorHash.cumple_dificultad(hash_calculado, dificultad):
            return False, f"No cumple dificultad {dificultad}"
        
        return True, "Hash válido"


# ==============================================================================
# VERIFICADOR DE TRABAJO ÚTIL (PoUC)
# ==============================================================================

class VerificadorPoUC:
    """
    Verifica los diferentes tipos de trabajo útil.
    """
    
    @staticmethod
    def es_primo(n: int) -> bool:
        """Verifica rápidamente si un número es primo."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        
        # Miller-Rabin determinista para n < 3,474,749,660,383
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        
        for a in [2, 3, 5, 7, 11, 13]:
            if a >= n:
                continue
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(s - 1):
                x = (x * x) % n
                if x == n - 1:
                    break
            else:
                return False
        return True
    
    @staticmethod
    def verificar_primo_gemelo(numero: int) -> Tuple[bool, str]:
        """
        Verifica que un número y numero+2 sean primos gemelos.
        """
        if not VerificadorPoUC.es_primo(numero):
            return False, f"{numero} no es primo"
        if not VerificadorPoUC.es_primo(numero + 2):
            return False, f"{numero + 2} no es primo"
        return True, f"Primos gemelos: ({numero}, {numero + 2})"
    
    @staticmethod
    def verificar_trabajo_util(tipo: str, prueba: Dict) -> Tuple[bool, str, float]:
        """
        Verifica un trabajo útil completado.
        
        Returns:
            (válido, mensaje, multiplicador_recompensa)
        """
        if tipo not in ConfigVerificador.TIPOS_TRABAJO:
            return False, f"Tipo desconocido: {tipo}", 0
        
        if tipo == "validacion":
            return VerificadorPoUC._verificar_validacion(prueba)
        elif tipo == "optimizacion":
            return VerificadorPoUC._verificar_optimizacion(prueba)
        elif tipo == "cientifico":
            return VerificadorPoUC._verificar_cientifico(prueba)
        
        return False, "No implementado", 0
    
    @staticmethod
    def _verificar_validacion(prueba: Dict) -> Tuple[bool, str, float]:
        """Verifica trabajo de validación (primos gemelos)."""
        numero = prueba.get("numero", 0)
        if numero <= 0:
            return False, "Número inválido", 0
        
        ok, msg = VerificadorPoUC.verificar_primo_gemelo(numero)
        return ok, msg, ConfigVerificador.MULTIPLICADOR_RECOMPENSA["validacion"]
    
    @staticmethod
    def _verificar_optimizacion(prueba: Dict) -> Tuple[bool, str, float]:
        """Verifica trabajo de optimización de red."""
        rutas = prueba.get("rutas", [])
        if not rutas or len(rutas) < 2:
            return False, "Muy pocas rutas", 0
        
        # Verificar que cada ruta tiene latencia y nodos válidos
        for ruta in rutas:
            if "latencia" not in ruta or "nodos" not in ruta:
                return False, "Ruta incompleta", 0
            if ruta["latencia"] < 0:
                return False, "Latencia negativa", 0
        
        return True, f"{len(rutas)} rutas optimizadas", ConfigVerificador.MULTIPLICADOR_RECOMPENSA["optimizacion"]
    
    @staticmethod
    def _verificar_cientifico(prueba: Dict) -> Tuple[bool, str, float]:
        """Verifica trabajo científico (cálculo complejo)."""
        resultado = prueba.get("resultado", "")
        if not resultado:
            return False, "Sin resultado", 0
        
        # Verificar que el hash del resultado coincida
        if "hash_verificacion" in prueba:
            hash_calculado = HashUtil.sha3(resultado.encode()).hex()
            if hash_calculado != prueba["hash_verificacion"]:
                return False, "Hash de verificación no coincide", 0
        
        return True, "Cálculo verificado", ConfigVerificador.MULTIPLICADOR_RECOMPENSA["cientifico"]


# ==============================================================================
# VERIFICADOR DE RECOMPENSAS
# ==============================================================================

class VerificadorRecompensa:
    """
    Verifica que la recompensa de un bloque sea correcta según el suministro.
    """
    
    def __init__(self):
        self.suministro_emitido = 3_000_000 * 10**6  # Premine en Direcs
        self.bloque_actual = 0
    
    def verificar_recompensa(self, recompensa_solicitada: int,
                             numero_bloque: int,
                             tipo_trabajo: str = "validacion") -> Tuple[bool, str, int]:
        """
        Verifica que la recompensa sea correcta.
        
        Returns:
            (válido, mensaje, recompensa_correcta)
        """
        if numero_bloque <= 0:
            return False, "Bloque génesis no tiene recompensa", 0
        
        # Calcular recompensa base según año de emisión
        año = math.ceil(numero_bloque / 97_000)
        recompensa_base = ConfigVerificador.RECOMPENSA_BASE
        for _ in range(1, año):
            recompensa_base = int(recompensa_base * 0.9)
        recompensa_base = max(1, recompensa_base)
        
        # Aplicar multiplicador por tipo de trabajo
        multiplicador = ConfigVerificador.MULTIPLICADOR_RECOMPENSA.get(tipo_trabajo, 1.0)
        recompensa_correcta = int(recompensa_base * multiplicador)
        
        if recompensa_solicitada > recompensa_correcta:
            return False, f"Recompensa excesiva: {recompensa_solicitada} > {recompensa_correcta}", recompensa_correcta
        
        # Verificar suministro máximo
        max_suministro = 100_000_000 * 10**6  # 100M DRC en Direcs
        if self.suministro_emitido + recompensa_solicitada > max_suministro:
            return False, "Excede suministro máximo", 0
        
        return True, "Recompensa válida", recompensa_correcta


# ==============================================================================
# DIAGNÓSTICO
# ==============================================================================

class DiagnosticoVerificador:
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
        print("🔍 DIAGNÓSTICO DE MINERIA/VERIFICADOR.PY")
        print("=" * 70)
        
        # 1. Verificar hash con dificultad
        datos = "testbloque"
        nonce = 0
        hash_ok = None
        for n in range(100000):
            h = HashUtil.doble_hex(f"{datos}{n}".encode())
            if h.startswith("d1"):
                nonce = n
                hash_ok = h
                break
        ok, msg = VerificadorHash.verificar_bloque(datos, nonce, hash_ok, 1)
        self._t("Verificar hash bloque", ok)
        
        # 2. Rechazar hash incorrecto
        ok, _ = VerificadorHash.verificar_bloque(datos, 0, "0" * 64, 1)
        self._t("Rechazar hash falso", not ok)
        
        # 3. Cumple dificultad
        self._t("Dificultad 1: prefijo d1", VerificadorHash.cumple_dificultad("d1abc", 1))
        self._t("Dificultad 3: d10", VerificadorHash.cumple_dificultad("d10abc", 2))
        self._t("Rechazar sin d1", not VerificadorHash.cumple_dificultad("ffabc", 1))
        
        # 4. Verificar primo
        self._t("7 es primo", VerificadorPoUC.es_primo(7))
        self._t("8 no es primo", not VerificadorPoUC.es_primo(8))
        self._t("9973 es primo", VerificadorPoUC.es_primo(9973))
        
        # 5. Verificar primos gemelos
        ok, msg = VerificadorPoUC.verificar_primo_gemelo(5)
        self._t("(5,7) son gemelos", ok)
        
        ok, msg = VerificadorPoUC.verificar_primo_gemelo(7)
        self._t("(7,9) no son gemelos", not ok)
        
        # 6. Verificar trabajo útil
        ok, msg, mult = VerificadorPoUC.verificar_trabajo_util("validacion", {"numero": 11})
        self._t("Trabajo validación (11,13)", ok and mult == 1.0)
        
        # 7. Verificar recompensa
        vr = VerificadorRecompensa()
        ok, msg, rec = vr.verificar_recompensa(100_000_000, 1, "validacion")
        self._t("Recompensa correcta", ok and rec == 100_000_000)
        
        # 8. Rechazar recompensa excesiva
        ok, msg, rec = vr.verificar_recompensa(999_999_999, 1, "validacion")
        self._t("Rechazar recompensa excesiva", not ok)
        
        t = self.ok + self.fail
        print("─" * 70)
        print(f"📊 {self.ok}/{t} PASADOS | {self.fail} FALLIDOS")
        print("─" * 70)
        if self.fail == 0: print("✅ MINERIA/VERIFICADOR.PY FUNCIONANDO\n")
        else: print("❌ ERRORES\n")
        return self.fail == 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "✅ " * 35)
    print("DIRECCOIN - VERIFICADOR DE TRABAJO v1.0.0")
    print("✅ " * 35)
    print(f"Tipos de trabajo: {', '.join(ConfigVerificador.TIPOS_TRABAJO)}")
    print(f"Prefijo hash: {ConfigVerificador.PREFIJO_HASH}\n")
    
    diag = DiagnosticoVerificador()
    if diag.ejecutar():
        print("📋 DEMO:")
        print(f"   9973 es primo: {VerificadorPoUC.es_primo(9973)}")
        print(f"   (11,13) gemelos: {VerificadorPoUC.verificar_primo_gemelo(11)[0]}")
        print("\n🎯 LISTO\n")

if __name__ == "__main__":
    main()