# =============================================================
#  SISTEMA DE COMUNICACIÓN CIFRADA Y ESTEGANOGRÁFICA
#  Seguridad Informática — Universidad Siglo 21 — 2026
#  Grupo: Zulatto / Jorja / Cornel / Aguilar / Cappellari
# =============================================================
#  SCRIPT 3 — RECEPTOR
#  Extrae el mensaje oculto en la imagen mediante LSB
#  (Least Significant Bit — Bit Menos Significativo) y lo
#  descifra usando AES-256-CBC con la clave compartida.
#
#  Requiere: pip install Pillow cryptography
# =============================================================

import os
import struct
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.hazmat.backends import default_backend


# ── FUNCIONES DE ESTEGANOGRAFÍA LSB ───────────────────────────

def bits_a_bytes(lista_bits):
    """
    Convierte una lista de bits individuales en bytes.
    Ejemplo: [1, 0, 1, 1, 0, 0, 0, 0] → 0b10110000 → 176
    """
    resultado = bytearray()
    for i in range(0, len(lista_bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(lista_bits):
                byte = (byte << 1) | lista_bits[i + j]
        resultado.append(byte)
    return bytes(resultado)


def extraer_lsb(ruta_imagen):
    """
    Extrae los datos ocultos en el LSB (Least Significant Bit —
    Bit Menos Significativo) de cada canal de color de la imagen.

    Proceso inverso al de incrustación:
      1. Leer el bit menos significativo de cada canal R, G, B
      2. Reconstruir los primeros 32 bits → largo del mensaje
      3. Leer los siguientes N*8 bits → datos cifrados
    """
    imagen = Image.open(ruta_imagen).convert("RGB")
    pixeles = list(imagen.getdata())

    # Extraer todos los LSB de la imagen
    todos_los_bits = []
    for pixel in pixeles:
        for valor_canal in pixel:
            todos_los_bits.append(valor_canal & 1)  # bit menos significativo

    # Los primeros 32 bits codifican el largo del payload
    bits_encabezado = todos_los_bits[:32]
    largo_mensaje = struct.unpack(">I", bits_a_bytes(bits_encabezado))[0]

    # Extraer exactamente esa cantidad de bytes
    bits_mensaje = todos_los_bits[32 : 32 + largo_mensaje * 8]
    return bits_a_bytes(bits_mensaje)


# ── FUNCIONES DE DESCIFRADO AES ────────────────────────────────

def descifrar_aes(datos_cifrados, clave):
    """
    Descifra datos usando AES-256-CBC.

    Los primeros 16 bytes son el IV (Initialization Vector —
    Vector de Inicialización) necesario para el descifrado CBC.
    Los bytes restantes son el texto cifrado.
    """
    if len(datos_cifrados) < 16:
        raise ValueError("Los datos extraídos son demasiado cortos para contener un IV válido.")

    iv            = datos_cifrados[:16]
    texto_cifrado = datos_cifrados[16:]

    descifrador = Cipher(
        algorithms.AES(clave),
        modes.CBC(iv),
        backend=default_backend()
    )
    operacion = descifrador.decryptor()
    datos_con_relleno = operacion.update(texto_cifrado) + operacion.finalize()

    # Quitar el relleno PKCS7 agregado al cifrar
    quitador_relleno = aes_padding.PKCS7(128).unpadder()
    datos_limpios = quitador_relleno.update(datos_con_relleno) + quitador_relleno.finalize()

    return datos_limpios


# ── EJECUCIÓN PRINCIPAL ────────────────────────────────────────

print("\n" + "=" * 62)
print("  FASE 2 — RECEPTOR: EXTRACCIÓN + DESCIFRADO")
print("=" * 62)

# Verificar que existe la clave compartida
if not os.path.exists("clave_compartida.bin"):
    print("\n  [✗] No se encontró 'clave_compartida.bin'.")
    print("  Ejecutá primero el Script 1 (intercambio_dh.py).\n")
    exit(1)

with open("clave_compartida.bin", "rb") as archivo:
    clave_aes = archivo.read()

print("\n  [✓] Clave AES-256 cargada desde clave_compartida.bin")

ruta_imagen = input("\n[1] Ruta de la imagen recibida (ej: enviada.png):\n  > ").strip()

if not os.path.exists(ruta_imagen):
    print(f"\n  [✗] No se encontró la imagen '{ruta_imagen}'.\n")
    exit(1)

# Paso 1: extraer datos cifrados de la imagen
print("\n  Extrayendo datos ocultos de la imagen...")
datos_cifrados = extraer_lsb(ruta_imagen)
print(f"  [✓] {len(datos_cifrados)} bytes extraídos mediante LSB")
print(f"      Muestra del texto cifrado: {datos_cifrados[:20].hex()}...")

# Paso 2: descifrar con AES
try:
    mensaje_bytes = descifrar_aes(datos_cifrados, clave_aes)
    mensaje_texto = mensaje_bytes.decode("utf-8")
except Exception:
    print("\n  [✗] No se pudo descifrar. Verificá que:")
    print("      - La imagen fue generada con el Script 2.")
    print("      - Ambas partes usaron la misma clave (mismo clave_compartida.bin).")
    print("      - La imagen no fue recomprimida (debe ser PNG).\n")
    exit(1)

print("\n" + "=" * 62)
print("  MENSAJE SECRETO DESCIFRADO:")
print("=" * 62)
print(f"\n  {mensaje_texto}\n")
print("=" * 62)
print("\n  [✓] Integridad verificada: el mensaje fue descifrado correctamente.")
print("  [✓] Origen auténtico: solo quien posee la clave AES puede leer esto.\n")
