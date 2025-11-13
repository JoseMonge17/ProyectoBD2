import pandas as pd
import random
import uuid

# Archivos fuente
ORDENES_FILE = "Supabase/ordenes.csv"
PRODUCTOS_FILE = "Supabase/productos.csv"

# Archivo de salida
DETALLES_FILE = "Supabase/orden_detalles.csv"

# Cargar datos
ordenes = pd.read_csv(ORDENES_FILE)
productos = pd.read_csv(PRODUCTOS_FILE)

# Crear lista para los detalles
detalles = []

# Generar detalles
for _, orden in ordenes.iterrows():
    # Cada orden tendra de 1 a 5 productos
    num_items = random.randint(1, 5)
    productos_seleccionados = productos.sample(num_items)
    
    for _, prod in productos_seleccionados.iterrows():
        cantidad = random.randint(1, 5)
        precio_unitario = round(float(prod["precio"]), 2)
        subtotal = round(cantidad * precio_unitario, 2)

        detalles.append({
            "detalle_id": str(uuid.uuid4()),
            "orden_id": orden["orden_id"],
            "producto_id": prod["producto_id"],
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": subtotal
        })

# Crear DataFrame y guardar
df_detalles = pd.DataFrame(detalles)

# Exportar CSV sin índice
df_detalles.to_csv(DETALLES_FILE, index=False)

print(f"✅ Archivo '{DETALLES_FILE}' generado con {len(df_detalles)} filas.")
