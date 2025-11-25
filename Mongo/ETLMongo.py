import pymongo
import pyodbc
import pandas as pd
import json
from datetime import datetime, timedelta
from dateutil import parser

# Conexión a MongoDB Atlas
mongo_client = pymongo.MongoClient(
    "mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/?appName=MiCluster"
)
db = mongo_client['Ventas']  # Nombre de la base de datos
clientes_collection = db['Clientes']
productos_collection = db['Productos']
ordenes_collection = db['Ordenes']

# Conexión a SQL Server
server = 'localhost'
database = 'DW_Proyecto_Sales'
conn_str = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};DATABASE={database};Trusted_Connection=yes;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
LOG_PATH = r"E:/BD2/Proyecto/ProyectoBD2/Mongo/log.json"

# Función para leer la fecha de la última carga desde log.json
def get_fecha_carga():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("fechaCarga", "")  # Devuelve vacío si no tiene valor
    except FileNotFoundError:
        return ""  # Si el archivo no existe, retornamos vacío
 
 # Función para actualizar la fecha de la última carga en log.json   
def update_log_data():
    # Obtener la fecha y hora actual
    fecha_carga = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Formato datetime ISO 8601
    
    log_data = {
        "fechaCarga": fecha_carga,  # Guardamos la fecha de la última orden procesada
    }
    
    with open(LOG_PATH, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4)

# ================== HELPERS SQL ==================

# 1. Función para obtener el idCliente desde la DW (para ventas)
def get_cliente_id(cliente_email):
    query = "SELECT idCliente FROM DIM_Cliente WHERE email = ?"
    cursor.execute(query, (cliente_email,))
    cliente_id_dw = cursor.fetchone()
    if cliente_id_dw:
        return cliente_id_dw[0]
    else:
        print(f"Error: Cliente con email {cliente_email} no encontrado en DIM_Cliente.")
        return None

def check_cliente_existe(cliente_email):
    query = "SELECT COUNT(*) FROM DIM_Cliente WHERE email = ?"
    cursor.execute(query, (cliente_email,))
    return cursor.fetchone()[0] > 0

def get_producto_id(producto):
    # producto es un dict (fila convertida)
    sku = None

    # Verificar si el producto tiene equivalencias
    if producto.get('equivalencias') and isinstance(producto.get('equivalencias'), dict):
        # Si tiene equivalencias, buscar el sku dentro de equivalencias
        sku = producto['equivalencias'].get('sku')
    else:
        # Si no tiene equivalencias, buscar por codigo_mongo o codigo_alterno en EquivalenciasProductos
        codigo = producto.get('codigo_mongo', producto.get('codigo_alt'))
        if codigo:
            query = """
                SELECT sku 
                FROM EquivalenciasProductos 
                WHERE codigo_mongo = ? OR codigo_alterno = ?
            """
            cursor.execute(query, (codigo, codigo))
            resultado = cursor.fetchone()
            if resultado:
                sku = resultado[0]

    if not sku:
        return None

    query = "SELECT idProducto FROM DIM_Producto WHERE sku = ?"
    cursor.execute(query, (sku,))
    id_producto = cursor.fetchone()
    if id_producto:
        return id_producto[0]
    return None

def get_producto_sku(producto):
    # Si no tiene equivalencias, buscar por codigo_mongo o codigo_alterno
    codigo = producto.get('codigo_mongo', producto.get('codigo_alt'))
    if codigo:
        query = """
            SELECT sku 
            FROM EquivalenciasProductos 
            WHERE codigo_mongo = ? OR codigo_alterno = ?
        """
        cursor.execute(query, (codigo, codigo))
        sku = cursor.fetchone()
        if sku:
            return sku[0]
    return None
    
# 3. Función para obtener el idCanal desde la DW
def get_canal_id(canal):
    query = "SELECT idCanal FROM DIM_Canal WHERE canal = ?"
    cursor.execute(query, (canal,))
    id_canal = cursor.fetchone()
    if id_canal:
        return id_canal[0]
    else:
        # Si no existe, lo insertamos
        query_insert = "INSERT INTO DIM_Canal (canal) VALUES (?)"
        cursor.execute(query_insert, (canal,))
        conn.commit()
        # Recuperamos el idCanal recién insertado
        cursor.execute("SELECT idCanal FROM DIM_Canal WHERE canal = ?", (canal,))
        nuevo = cursor.fetchone()
        return nuevo[0] if nuevo else None

# 5. Insertar ventas en la tabla FACT_Ventas
def insert_fact_ventas(cliente_id, producto_id, idTiempo, cantidad, precio_unit, total_venta, total_crc, canal):
    id_canal = get_canal_id(canal)
    
    if id_canal:
        query = """
        INSERT INTO FACT_Ventas 
        (idCliente, idProducto, idTiempo, idCanal, cantidad, precioUnitario, descuentoPct, totalVenta, totalCRC)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (
            cliente_id, producto_id, idTiempo, id_canal,
            cantidad, precio_unit, 0, total_venta, total_crc
        ))
        conn.commit()

# ================== PROCESO PRINCIPAL ==================

def process_mongo_data():
    # ---------- CARGA MASIVA DESDE MONGO CON PANDAS ----------
    # Obtener la fecha de la última carga desde log.json
    fecha_carga = get_fecha_carga()
    
    clientes_df = pd.DataFrame(list(clientes_collection.find()))
    productos_df = pd.DataFrame(list(productos_collection.find()))
    
    # Si fecha_carga está vacía, traeremos todas las órdenes
    if not fecha_carga:
        ordenes_df = pd.DataFrame(list(ordenes_collection.find()))
    else:
        # 1) Parsear la fecha del log como LOCAL (CR)
        fecha_carga_local = datetime.strptime(fecha_carga, "%Y-%m-%d %H:%M:%S")

        # 2) Convertirla a UTC (Costa Rica es UTC-6, así que sumamos 6 horas)
        fecha_carga_utc = fecha_carga_local + timedelta(hours=6)

    # 3) Usar esa fecha UTC en el query de Mongo
    query = {"fecha": {"$gt": fecha_carga_utc}}
    ordenes_df = pd.DataFrame(list(ordenes_collection.find(query)))

    print(f"Clientes cargados desde Mongo: {len(clientes_df)}")
    print(f"Productos cargados desde Mongo: {len(productos_df)}")
    print(f"Órdenes cargadas desde Mongo: {len(ordenes_df)}")

    # ---------- 1) INSERTAR CLIENTES EN DIM_Cliente ----------
    clientes_insertados = 0
    for _, row in clientes_df.iterrows():
        cliente = row.to_dict()
        email = cliente.get("email")

        if not email:
            print(f"Cliente {cliente.get("nombre")}sin correo")
            continue

        if check_cliente_existe(email):
            continue  # ya existe en la DW

        genero = (cliente.get("genero") or "").capitalize()
        if genero in ['M', 'Masculino']:
            genero = "Masculino"
        elif genero in ['F', 'Femenino']:
            genero = "Femenino"
        else:
            genero = "Otro"

        fecha_registro = cliente.get("creado", datetime.now())
        if isinstance(fecha_registro, str):
            try:
                # Intentar parseo ISO
                fecha_registro = parser.isoparse(fecha_registro)
            except Exception:
                try:
                    fecha_registro = datetime.strptime(fecha_registro, "%Y-%m-%d")
                except Exception:
                    fecha_registro = datetime.now()

        query_insert_cliente = """
        INSERT INTO DIM_Cliente (nombre, email, genero, pais, fechaRegistro) 
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query_insert_cliente, (
            cliente.get('nombre'),
            email,
            genero,
            cliente.get('pais', 'Costa Rica'),
            fecha_registro
        ))
        conn.commit()
        clientes_insertados += 1

    print(f"Clientes insertados en DIM_Cliente: {clientes_insertados}")

    # ---------- 2) INSERTAR PRODUCTOS EN DIM_Producto ----------
    productos_insertados = 0
    for _, row in productos_df.iterrows():
        producto = row.to_dict()

        # Si el producto tiene equivalencias, usamos el SKU directo de equivalencias
        if producto.get('equivalencias') and isinstance(producto.get('equivalencias'), dict):
            sku = producto['equivalencias'].get('sku')
        else:
            # Si no tiene equivalencias, buscamos el SKU usando el código_mongo / codigo_alt
            sku = get_producto_sku(producto)

        if not sku:
            continue

        # Verificar si ya existe en DIM_Producto
        query = "SELECT idProducto FROM DIM_Producto WHERE sku = ?"
        cursor.execute(query, (sku,))
        ya_existe = cursor.fetchone()
        if ya_existe:
            continue

        query_insert_producto = """
        INSERT INTO DIM_Producto (sku, nombre, categoria)
        VALUES (?, ?, ?)
        """
        cursor.execute(query_insert_producto, (
            sku,
            producto.get('nombre'),
            producto.get('categoria')
        ))
        conn.commit()
        productos_insertados += 1

    print(f"Productos insertados en DIM_Producto: {productos_insertados}")

    # ---------- 3) PROCESAR ÓRDENES E INSERTAR VENTAS (UN SOLO FOR DE ÓRDENES) ----------
    conta_ordenes = 0
    conta_ventas = 0

    for _, orden_row in ordenes_df.iterrows():
        orden = orden_row.to_dict()

        # 1) Cliente desde DataFrame de clientes
        cliente_mongo_id = orden.get('cliente_id')
        cliente_rows = clientes_df[clientes_df['_id'] == cliente_mongo_id]
        if cliente_rows.empty:
            continue

        email_cliente = cliente_rows.iloc[0]['email']

        # 2) idCliente en la DW
        cliente_id_dw = get_cliente_id(email_cliente)
        if not cliente_id_dw:
            continue

        # 3) Fecha -> idTiempo y tipoCambio (una sola vez por orden)
        fecha_val = orden.get('fecha')
        if isinstance(fecha_val, datetime):
            fecha_obj = fecha_val
        else:
            # ej: "2024-07-17T06:00:00.000+00:00"
            fecha_obj = parser.isoparse(fecha_val)

        fecha_sql = fecha_obj.date()  # YYYY-MM-DD, como está en DIM_Tiempo

        query_tipo_cambio = "SELECT idTiempo, tipoCambio FROM DIM_Tiempo WHERE fecha = ?"
        cursor.execute(query_tipo_cambio, (fecha_sql,))
        tipo_cambio_data = cursor.fetchone()

        if not tipo_cambio_data:
            print(f"No se encontró idTiempo/tipoCambio para la fecha {fecha_sql}. Se omite la orden.")
            continue

        id_tiempo, tipo_cambio = tipo_cambio_data
        tipo_cambio = float(tipo_cambio)

        # 4) Recorrer items y hacer inserts directo (mismo estilo que tenías antes)
        items = orden.get("items") or []
        for item in items:
            producto_mongo_id = item["producto_id"]
            prod_rows = productos_df[productos_df['_id'] == producto_mongo_id]
            if prod_rows.empty:
                continue

            producto = prod_rows.iloc[0].to_dict()
            producto_id_dw = get_producto_id(producto)
            if not producto_id_dw:
                continue

            cantidad = float(item["cantidad"])
            precio_unit_crc = float(item["precio_unit"])

            total_crc = cantidad * precio_unit_crc
            total_venta = total_crc / tipo_cambio          # total en USD
            precio_unit_usd = precio_unit_crc / tipo_cambio

            insert_fact_ventas(
                cliente_id_dw,
                producto_id_dw,
                id_tiempo,
                cantidad,
                precio_unit_usd,
                total_venta,
                total_crc,
                orden.get('canal')
            )
            conta_ventas += 1

        conta_ordenes += 1

    print(f"Órdenes procesadas: {conta_ordenes}")
    print(f"Ventas insertadas en FACT_Ventas: {conta_ventas}")


# 7. Función principal que ejecuta todo el proceso
def main():
    process_mongo_data()
    update_log_data()
    print("Datos procesados y cargados en SQL Server.")

# Ejecutar el script
if __name__ == "__main__":
    main()
