# =============================================================
#  SISTEMA DE COMUNICACIÓN CIFRADA Y ESTEGANOGRÁFICA
#  Seguridad Informática — Universidad Siglo 21 — 2026
#  Grupo: Zulatto / Jorja / Cornel / Aguilar / Cappellari
# =============================================================
#  SCRIPT 1 — Intercambio de claves (Protocolo Diffie-Hellman)
#
#  Uso: ambos participantes ejecutan este script de forma
#  independiente. Intercambian sus claves públicas por correo
#  (aunque alguien las intercepte, no puede deducir el secreto).
#  Al finalizar, ambos habrán calculado la misma clave AES
#  sin haberla comunicado explícitamente.
# =============================================================

import random
import hashlib

# ── PARÁMETROS PÚBLICOS ────────────────────────────────────────
# P: número primo de 2048 bits del RFC (Request for Comments)
# 3526 del IETF (Internet Engineering Task Force).
# Auditado internacionalmente. Ambas partes lo conocen.
# G: generador (base) del grupo matemático.

P = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF695581718399549E80F7B2E3D5D4DA8B3B8B87FC9"
    "15728E5A8AACAA68FFFFFFFFFFFFFFFF", 16
)
G = 2


def generar_clave_privada():
    """
    Genera un número entero aleatorio grande como clave privada.
    Este número NUNCA se comparte con nadie.
    """
    return random.randrange(2, P - 1)


def calcular_clave_publica(clave_privada):
    """
    Calcula la clave pública: A = G^a mod P
    Este valor SÍ se comparte abiertamente por correo electrónico.
    """
    return pow(G, clave_privada, P)


def calcular_secreto_compartido(clave_publica_otro, clave_privada):
    """
    Calcula el secreto compartido: K = B^a mod P
    Ambas partes obtienen el mismo K = G^(a*b) mod P
    sin haberlo comunicado directamente.
    """
    return pow(clave_publica_otro, clave_privada, P)


def derivar_clave_aes(secreto_compartido):
    """
    Deriva una clave AES (Advanced Encryption Standard) de 256 bits
    aplicando SHA-256 (Secure Hash Algorithm de 256 bits) al secreto.
    Esto convierte el número enorme de DH en exactamente 32 bytes
    utilizables por AES.
    """
    secreto_bytes = secreto_compartido.to_bytes(
        (secreto_compartido.bit_length() + 7) // 8, byteorder='big'
    )
    return hashlib.sha256(secreto_bytes).digest()


# ── EJECUCIÓN PRINCIPAL ────────────────────────────────────────

print("\n" + "=" * 62)
print("  FASE 1 — INTERCAMBIO DE CLAVES DIFFIE-HELLMAN")
print("=" * 62)

# Paso 1: generar clave privada (solo para este equipo)
clave_privada = generar_clave_privada()
clave_publica = calcular_clave_publica(clave_privada)

print("\n[PASO 1] Tu CLAVE PÚBLICA generada (compartila por mail):\n")
print(clave_publica)
print("\n→ Enviá este número a tu contacto por correo electrónico.")
print("  No importa si alguien lo intercepta: es inútil sin tu clave privada.\n")

# Paso 2: ingresar la clave pública del otro participante
print("[PASO 2] Ingresá la clave pública que te envió tu contacto:")
clave_publica_otro = int(input("  > ").strip())

# Paso 3: calcular el secreto compartido y derivar clave AES
secreto = calcular_secreto_compartido(clave_publica_otro, clave_privada)
clave_aes = derivar_clave_aes(secreto)

# Guardar la clave AES para usarla en los scripts 2 y 3
with open("clave_compartida.bin", "wb") as archivo:
    archivo.write(clave_aes)

print("\n" + "=" * 62)
print("  [✓] Secreto compartido calculado correctamente.")
print("  [✓] Clave AES-256 derivada y guardada en: clave_compartida.bin")
print("=" * 62)
print("\n  Ambas partes ahora tienen la misma clave sin haberla")
print("  enviado nunca. La Fase 1 está completa.")
print("\n  Podés comenzar a usar los scripts 2 (emisor) y 3 (receptor).\n")
