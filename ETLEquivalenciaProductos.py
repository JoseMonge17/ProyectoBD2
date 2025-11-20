import pandas as pd
import pyodbc

# Conexión global a SQL Server (Autenticación de Windows)
server = 'localhost'
database = 'DW_Proyecto_Sales'
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# 1. Leer el archivo CSV
def load_csv_to_dataframe(file_path):
    return pd.read_csv(file_path)

# 2. Validar y transformar los datos
def transform_data(df):
    # Filtrar columnas necesarias: sku, codigo_alt, codigo_mongo
    df = df[['sku', 'codigo_alt', 'codigo_mongo']].copy()  # Asegurarse de trabajar sobre una copia

    # Eliminar filas donde no hay SKU ni código alterno ni código mongo
    df.dropna(subset=['sku', 'codigo_alt', 'codigo_mongo'], how='all', inplace=True)  # Modificar directamente

    # Eliminar duplicados
    df.drop_duplicates(subset=['sku', 'codigo_alt', 'codigo_mongo'], inplace=True)  # Modificar directamente

    return df

# 3. Insertar datos en la tabla EquivalenciasProductos
def insert_equivalencias_productos(df):
    insert_count = 0
    for _, row in df.iterrows():
        # Inserción de cada fila en la tabla EquivalenciasProductos
        query = """
        INSERT INTO EquivalenciasProductos (sku, codigo_alterno, codigo_mongo)
        VALUES (?, ?, ?)
        """
        cursor.execute(query, (row['sku'], row['codigo_alt'], row['codigo_mongo']))
        conn.commit()
        insert_count += 1
    
    # Verificar cuántas inserciones se hicieron
    print(f"Se insertaron {insert_count} registros en la tabla EquivalenciasProductos.")

# Función principal para ejecutar el proceso ETL
def main():
    # Ruta del archivo CSV
    file_path = 'D:\VsCode\ProyectoBD2\EquivalenciaProductos.csv'
    #file_path = 'C:/Users/djmon/OneDrive/Documentos/GitHub/ProyectoBD2/EquivalenciaProductos.csv'

    # Leer y transformar datos
    df = load_csv_to_dataframe(file_path)
    df = transform_data(df)

    # Insertar datos en SQL Server
    insert_equivalencias_productos(df)

    # Cerrar la conexión
    conn.close()

# Ejecutar el script
if __name__ == "__main__":
    main()
