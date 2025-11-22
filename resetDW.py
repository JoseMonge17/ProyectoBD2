import sqlalchemy as db

# Conexión a tu DW
CONNECTION_STRING_DB = (
    "mssql+pyodbc://localhost/DW_Proyecto_Sales?"
    "trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
)

engine = db.create_engine(CONNECTION_STRING_DB)
connection = engine.connect()

def reset_dw():
    print("Conectado al DW...")

    # El orden importa (primero hechos, luego dimensiones)
    tables = [
        "FACT_Ventas",
        "MetasVentas",
        "EquivalenciasProductos",
        "DIM_Canal",
        "DIM_Tiempo",
        "DIM_Producto",
        "DIM_Cliente"
    ]

    for table in tables:
        print(f"→ Borrando datos de {table}...")
        try:
            # Borrar todo
            connection.execute(db.text(f"DELETE FROM {table};"))

            # Reiniciar IDENTITY
            connection.execute(db.text(f"DBCC CHECKIDENT ('{table}', RESEED, 0);"))
        except Exception as e:
            print(f"❌ Error en {table}: {e}")

    connection.commit()
    print("✔ Todas las tablas han sido limpiadas y los IDENTITY reiniciados.")

if __name__ == "__main__":
    reset_dw()
