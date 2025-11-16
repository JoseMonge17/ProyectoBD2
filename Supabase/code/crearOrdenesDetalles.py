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
    raise ValueError("No se pudieron cargar productos desde productos_supabase.csv")

# Leer órdenes
ordenes = []
with open(ORDENES_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ordenes.append(row["orden_id"])

if not ordenes:
    raise ValueError("No se pudieron cargar órdenes desde ordenes.csv")


# Crear detalles
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["orden_detalle_id", "orden_id", "producto_id", "cantidad", "precio_unit"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for orden_id in ordenes:
        n_items = random.randint(1, 5)

        for _ in range(n_items):
            writer.writerow({
                "orden_detalle_id": str(uuid.uuid4()),
                "orden_id": orden_id,
                "producto_id": random.choice(productos),
                "cantidad": random.randint(1, 4),
                "precio_unit": round(random.uniform(5.0, 150.0), 2)
            })

print("✔ Archivo orden_detalles.csv generado correctamente!")
print(f"Ubicación: {OUTPUT_FILE}")