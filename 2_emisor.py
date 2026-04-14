# =============================================================
#  SISTEMA DE COMUNICACIÓN CIFRADA Y ESTEGANOGRÁFICA
#  Seguridad Informática — Universidad Siglo 21 — 2026
#  Grupo: Zulatto / Jorja / Cornel / Aguilar / Cappellari
# =============================================================
#  SCRIPT 2 — EMISOR
#  Cifra el mensaje con AES-256-CBC y lo oculta dentro de una
#  imagen mediante la técnica esteganográfica LSB
#  (Least Significant Bit — Bit Menos Significativo).
#
#  Requiere: pip install Pillow cryptography
# =============================================================

import os
import struct
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.hazmat.backends import default_backend


# ── FUNCIONES DE CIFRADO AES ───────────────────────────────────

def cifrar_aes(mensaje_bytes, clave):
    """
    Cifra los datos usando AES-256-CBC.
    
    CBC (Cipher Block Chaining — Encadenamiento de Bloques de Cifrado):
    cada bloque de 128 bits se combina con el bloque cifrado anterior
    antes de cifrarse, lo que impide patrones repetitivos en el texto cifrado.
    
    IV (Initialization Vector — Vector de Inicialización):
    valor aleatorio de 16 bytes que garantiza que el mismo mensaje
    cifrado dos veces produzca resultados distintos.
    
    Retorna: IV (16 bytes) + texto cifrado
    """
    iv = os.urandom(16)

    # PKCS7: relleno que completa el último bloque hasta 128 bits
    relleno = aes_padding.PKCS7(128).padder()
    mensaje_rellenado = relleno.update(mensaje_bytes) + relleno.finalize()

    cifrador = Cipher(
        algorithms.AES(clave),
        modes.CBC(iv),
        backend=default_backend()
    )
    operacion = cifrador.encryptor()
    texto_cifrado = operacion.update(mensaje_rellenado) + operacion.finalize()

    return iv + texto_cifrado  # devolvemos IV + cifrado juntos


# ── FUNCIONES DE ESTEGANOGRAFÍA LSB ───────────────────────────

def bytes_a_bits(datos):
    """
    Convierte una secuencia de bytes en una lista de bits individuales.
    Ejemplo: 0b10110000 → [1, 0, 1, 1, 0, 0, 0, 0]
    """
    bits = []
    for byte in datos:
        for posicion in range(7, -1, -1):
            bits.append((byte >> posicion) & 1)
    return bits


def incrustar_lsb(ruta_imagen_entrada, datos_a_ocultar, ruta_imagen_salida):
    """
    Incrusta datos dentro de una imagen reemplazando el LSB
    (Least Significant Bit — Bit Menos Significativo) de cada canal
    de color de cada píxel.

    Un píxel RGB tiene 3 canales (R: rojo, G: verde, B: azul),
    cada uno representado en 8 bits (0–255).
    Cambiar el último bit de 200 (11001000) a 201 (11001001)
    produce una diferencia de color absolutamente imperceptible al ojo humano.

    Formato de los datos incrustados:
      [4 bytes: largo del mensaje] + [N bytes: datos cifrados]
    """
    imagen = Image.open(ruta_imagen_entrada).convert("RGB")
    pixeles = list(imagen.getdata())

    # Encabezado de 4 bytes que indica cuántos bytes de datos vienen después
    encabezado = struct.pack(">I", len(datos_a_ocultar))
    datos_completos = encabezado + datos_a_ocultar
    bits = bytes_a_bits(datos_completos)

    capacidad_maxima = len(pixeles) * 3  # 3 canales por píxel = 3 bits por píxel
    if len(bits) > capacidad_maxima:
        raise ValueError(
            f"Mensaje demasiado largo para esta imagen.\n"
            f"  Capacidad máxima: {capacidad_maxima // 8} bytes\n"
            f"  Tamaño del mensaje cifrado: {len(datos_a_ocultar)} bytes\n"
            f"  Usá una imagen más grande."
        )

    pixeles_modificados = []
    indice_bit = 0

    for pixel in pixeles:
        canales_nuevos = []
        for valor_canal in pixel:
            if indice_bit < len(bits):
                # Poner el bit del mensaje en la posición menos significativa
                nuevo_valor = (valor_canal & 0b11111110) | bits[indice_bit]
                indice_bit += 1
            else:
                nuevo_valor = valor_canal
            canales_nuevos.append(nuevo_valor)
        pixeles_modificados.append(tuple(canales_nuevos))

    # Guardar en PNG (Portable Network Graphics): sin compresión con pérdida.
    # JPEG alteraría los píxeles y destruiría el mensaje oculto.
    imagen_nueva = Image.new("RGB", imagen.size)
    imagen_nueva.putdata(pixeles_modificados)
    imagen_nueva.save(ruta_imagen_salida, format="PNG")


# ── EJECUCIÓN PRINCIPAL ────────────────────────────────────────

print("\n" + "=" * 62)
print("  FASE 2 — EMISOR: CIFRADO + ESTEGANOGRAFÍA")
print("=" * 62)

# Verificar que existe la clave compartida
if not os.path.exists("clave_compartida.bin"):
    print("\n  [✗] No se encontró 'clave_compartida.bin'.")
    print("  Ejecutá primero el Script 1 (intercambio_dh.py).\n")
    exit(1)

with open("clave_compartida.bin", "rb") as archivo:
    clave_aes = archivo.read()

print("\n  [✓] Clave AES-256 cargada desde clave_compartida.bin")

# Entrada del usuario
print()
mensaje_texto = input("[1] Escribí tu mensaje secreto:\n  > ")
ruta_entrada  = input("\n[2] Ruta de la imagen portadora (ej: foto.png):\n  > ").strip()
ruta_salida   = input("\n[3] Nombre de la imagen de salida (ej: enviada.png):\n  > ").strip()

# Verificar que la imagen existe
if not os.path.exists(ruta_entrada):
    print(f"\n  [✗] No se encontró la imagen '{ruta_entrada}'.\n")
    exit(1)

# Paso 1: cifrar el mensaje
mensaje_bytes  = mensaje_texto.encode("utf-8")
datos_cifrados = cifrar_aes(mensaje_bytes, clave_aes)
print(f"\n  [✓] Mensaje cifrado con AES-256-CBC: {len(datos_cifrados)} bytes")
print(f"      Texto cifrado (muestra): {datos_cifrados[:20].hex()}...")

# Paso 2: ocultar en la imagen
try:
    incrustar_lsb(ruta_entrada, datos_cifrados, ruta_salida)
except ValueError as error:
    print(f"\n  [✗] {error}\n")
    exit(1)

print(f"  [✓] Mensaje oculto en '{ruta_salida}' mediante LSB")

print("\n" + "=" * 62)
print(f"  Enviá '{ruta_salida}' como adjunto en tu correo de Gmail.")
print("  A simple vista es una imagen completamente normal.")
print("  Solo quien tenga la clave AES podrá extraer el mensaje.")
print("=" * 62 + "\n")
