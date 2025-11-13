import pandas as pd
import uuid
import random
from datetime import datetime, timedelta

# === CONFIGURACION ===
CLIENTES_FILE = "Supabase/clientes.csv"
OUTPUT_FILE = "Supabase/ordenes.csv"

# === CARGAR CLIENTES ===
clientes = pd.read_csv(CLIENTES_FILE)

# === PARAMETROS ===
NUM_ORDENES = 5000
CANALES = ["WEB", "APP", "PARTNER"]
MONEDAS = ["USD", "CRC"]

# === FUNCION PARA FECHA ALEATORIA ENTRE 2024 Y 2025 ===
def random_date(start_year=2024, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return (start + timedelta(days=random_days, seconds=random_seconds)).isoformat()

# === GENERAR ORDENES ===
ordenes = []
for _ in range(NUM_ORDENES):
    cliente = clientes.sample(1).iloc[0]
    canal = random.choice(CANALES)
    moneda = random.choice(MONEDAS)

    # monto aleatorio según moneda
    if moneda == "USD":
        total = round(random.uniform(10, 1500), 2)
    else:  # CRC
        total = round(random.uniform(5000, 900000), 2)

    ordenes.append({
        "orden_id": str(uuid.uuid4()),
        "cliente_id": cliente["cliente_id"],
        "fecha": random_date(),
        "canal": canal,
        "moneda": moneda,
        "total": total
    })

# === CREAR DATAFRAME Y REORDENAR COLUMNAS ===
df = pd.DataFrame(ordenes)[["orden_id", "cliente_id", "fecha", "canal", "moneda", "total"]]
df.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Archivo generado: {OUTPUT_FILE}")
print(f"Total de órdenes: {len(df)}")
