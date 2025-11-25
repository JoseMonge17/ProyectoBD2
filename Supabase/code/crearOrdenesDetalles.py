import csv
import uuid
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "..", "csv")

PRODUCTOS_FILE = os.path.join(CSV_DIR, "productos.csv")
ORDENES_FILE = os.path.join(CSV_DIR, "ordenes.csv")
OUTPUT_FILE = os.path.join(CSV_DIR, "orden_detalles.csv")

# Validaciones
if not os.path.exists(PRODUCTOS_FILE):
    raise FileNotFoundError(f"No existe: {PRODUCTOS_FILE}")

if not os.path.exists(ORDENES_FILE):
    raise FileNotFoundError(f"No existe: {ORDENES_FILE}")

# Leer productos
productos = []
with open(PRODUCTOS_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        productos.append(row["producto_id"])

if not productos:
    raise ValueError("No se pudieron cargar productos desde productos.csv")


# Leer órdenes
ordenes = []
with open(ORDENES_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ordenes.append({
            "orden_id": row["orden_id"],
            "moneda": row["moneda"],
            "total": float(row["total"])  # Ajustar si el nombre cambia
        })

if not ordenes:
    raise ValueError("No se pudieron cargar órdenes desde ordenes.csv")


def generar_precios_limitados(total_usd, min_precio=5.0, max_items=4):
    """Genera una lista de precios que sumen cerca del total pero con máximo 4 items."""
    
    if total_usd < min_precio * 1.2:
        # Total muy pequeño → 1 solo item exacto
        return [round(total_usd, 2)]
    
    precios = []
    restante = total_usd

    # Intentar generar de 2 a max_items productos
    n_items = random.randint(1, max_items)

    # Asegurar que cada uno pueda valer al menos 5
    if total_usd < n_items * min_precio:
        n_items = max(1, int(total_usd // min_precio))

    if n_items == 1:
        return [round(total_usd, 2)]

    # Generar n_items - 1 precios aleatorios
    for i in range(n_items - 1):
        max_precio = max(min_precio, restante - (min_precio * (n_items - i - 1)))
        precio = round(random.uniform(min_precio, max_precio), 2)
        precios.append(precio)
        restante = round(restante - precio, 2)

    # Último item es lo que queda
    precios.append(round(restante, 2))

    return precios


# Crear archivo de salida
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["orden_detalle_id", "orden_id", "producto_id", "cantidad", "precio_unit"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for orden in ordenes:
        orden_id = orden["orden_id"]
        moneda = orden["moneda"]
        total = orden["total"]

        # Convertir total
        if moneda == "CRC":
            total_usd = total / 500.0
        else:
            total_usd = total

        # Precios con máximo 4 detalles
        precios_usd = generar_precios_limitados(total_usd)

        # Escribir detalles
        for precio_usd in precios_usd:
            precio_unit = round(precio_usd * 500, 2) if moneda == "CRC" else precio_usd

            writer.writerow({
                "orden_detalle_id": str(uuid.uuid4()),
                "orden_id": orden_id,
                "producto_id": random.choice(productos),
                "cantidad": 1,
                "precio_unit": precio_unit
            })

print("✔ Archivo orden_detalles.csv generado correctamente!")
print(f"Ubicación: {OUTPUT_FILE}")
