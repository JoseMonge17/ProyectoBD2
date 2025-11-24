import csv
import uuid
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "..", "csv")

PRODUCTOS_FILE = os.path.join(CSV_DIR, "productos.csv")
ORDENES_FILE = os.path.join(CSV_DIR, "ordenes.csv")
OUTPUT_FILE = os.path.join(CSV_DIR, "orden_detalles.csv")

# Validaciones de archivos
if not os.path.exists(PRODUCTOS_FILE):
    raise FileNotFoundError(f"No existe: {PRODUCTOS_FILE}")

if not os.path.exists(ORDENES_FILE):
    raise FileNotFoundError(f"No existe: {ORDENES_FILE}")

# Leer productos desde Supabase
productos = []
with open(PRODUCTOS_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        productos.append(row["producto_id"])

if not productos:
    raise ValueError("No se pudieron cargar productos desde productos.csv")

# Leer órdenes con su moneda
ordenes = []
with open(ORDENES_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ordenes.append({
            "orden_id": row["orden_id"],
            "moneda": row["moneda"]
        })

if not ordenes:
    raise ValueError("No se pudieron cargar órdenes desde ordenes.csv")

# Crear detalles
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["orden_detalle_id", "orden_id", "producto_id", "cantidad", "precio_unit"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for orden in ordenes:
        orden_id = orden["orden_id"]
        moneda = orden["moneda"]

        n_items = random.randint(1, 5)

        for _ in range(n_items):
            # precio base en USD (mayor a 5 USD)
            precio_usd = round(random.uniform(5.01, 150.0), 2)

            # si moneda es CRC, convertir
            if moneda == "CRC":
                precio_unit = round(precio_usd * 500, 2)
            else:
                precio_unit = precio_usd

            writer.writerow({
                "orden_detalle_id": str(uuid.uuid4()),
                "orden_id": orden_id,
                "producto_id": random.choice(productos),
                "cantidad": random.randint(1, 4),
                "precio_unit": precio_unit
            })

print("✔ Archivo orden_detalles.csv generado correctamente!")
print(f"Ubicación: {OUTPUT_FILE}")
