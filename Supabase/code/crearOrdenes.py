import pandas as pd
import uuid
import random
from datetime import datetime, timedelta

# === CONFIGURACION ===
CLIENTES_FILE = "D:\VsCode\ProyectoBD2\Supabase\csv\clientes.csv"
OUTPUT_FILE = "D:\VsCode\ProyectoBD2\Supabase\csv\ordenes.csv"

# === CARGAR CLIENTES ===
clientes = pd.read_csv(CLIENTES_FILE)

# === PARAMETROS ===
NUM_ORDENES = 5000
CANALES = ["WEB", "APP", "PARTNER"]
MONEDAS = ["USD", "CRC"]

# === FUNCION PARA FECHA ALEATORIA ENTRE 2024 Y 31 OCTUBRE 2025 ===
def random_date(start_year=2024, end_year=2025):
    start = datetime(start_year, 1, 1)
    # Fecha máxima: 31 de octubre de 2025
    end = datetime(end_year, 10, 31)
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

    # monto base siempre en USD (mínimo 5 USD)
    base_usd = round(random.uniform(5.01, 1500), 2)

    # si la moneda es CRC → convertir
    if moneda == "CRC":
        total = round(base_usd * 500, 2)
    else:
        total = base_usd

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