import pandas as pd
import pyodbc
from neo4j import GraphDatabase
import json
from datetime import datetime
from decimal import Decimal

# Conexión global a Neo4j
URI = "bolt://localhost:7687"
AUTH_USER = "neo4j"
AUTH_PASS = "Jjmb260505*"
DATABASE_NAME = "ventas"
LOG_PATH = r"E:/BD2/Proyecto/ProyectoBD2/Neo4j/log.json"

def get_driver():
    """Retorna el driver de Neo4j."""
    return GraphDatabase.driver(URI, auth=(AUTH_USER, AUTH_PASS))

# Conexión global a SQL Server (Autenticación de Windows)
server = 'localhost'
database = 'DW_Proyecto_Sales'
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Obtener el driver de Neo4j
neo4j_driver = get_driver()

# Función para leer el último ID insertado y la fecha de carga desde el archivo log.json
def get_log_data():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("last_id", 0), data.get("fechaCarga", "")  # Devuelve 0 si no existe last_id
    except FileNotFoundError:
        return 0, ""  # Si el archivo no existe, asumimos que no hay ventas procesadas

# Función para actualizar el archivo log.json con el último ID insertado y la fecha de carga
def update_log_data(last_id):
    # Obtener la fecha actual
    fecha_carga = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        "last_id": last_id,
        "fechaCarga": fecha_carga
    }
    
    with open(LOG_PATH, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4)
        
# 1. Extraer datos de clientes desde Neo4j
def extract_clientes_data():
    clientes_query = """
    MATCH (c:Cliente)
    RETURN c.nombre AS nombre, c.email AS email, c.genero AS genero, c.pais AS pais, c.fechaRegistro AS fechaRegistro
    """
    with neo4j_driver.session(database=DATABASE_NAME) as session:
        clientes_data = session.run(clientes_query)
        clientes = [record.data() for record in clientes_data]
    print(f"Se extrajeron {len(clientes)} registros de clientes desde Neo4j.")
    return pd.DataFrame(clientes)

# 2. Extraer datos de productos desde Neo4j
def extract_productos_data():
    productos_query = """
    MATCH (p:Producto)-[:PERTENECE_A]->(c:Categoria)
    RETURN p.sku AS sku, p.nombre AS nombre, c.categoria AS categoria, p.codigo_alt AS codigo_alterno, p.codigo_mongo AS codigo_mongo
    """
    with neo4j_driver.session(database=DATABASE_NAME) as session:
        productos_data = session.run(productos_query)
        productos = [record.data() for record in productos_data]
    print(f"Se extrajeron {len(productos)} registros de productos desde Neo4j.")
    return pd.DataFrame(productos)


# 3. Extraer datos de órdenes desde Neo4j (con filtro por id mayor que el último insertado)
def extract_ordenes_data(last_id):
    ordenes_query = f"""
    MATCH (c:Cliente)-[:REALIZO]->(o:Orden)-[contiente:CONTIENTE]->(p:Producto)
    WHERE o.idOrden > {last_id}
    RETURN o.idOrden AS orden_id, o.fecha AS fecha, o.total AS total, o.moneda AS moneda, c.email AS cliente_email, 
           p.sku AS producto_sku, p.codigo_alt AS codigo_alterno, p.codigo_mongo AS codigo_mongo, 
           contiente.cantidad AS cantidad, contiente.precio AS precio_unitario, o.canal as canal
    """
    with neo4j_driver.session(database=DATABASE_NAME) as session:
        ordenes_data = session.run(ordenes_query)
        ordenes = [record.data() for record in ordenes_data]
    print(f"Se extrajeron {len(ordenes)} registros de ventas desde Neo4j.")
    return pd.DataFrame(ordenes)

# 5. Validar si un cliente ya existe en la base de datos SQL Server
def check_cliente(cliente_email):
    query = "SELECT COUNT(*) FROM DIM_Cliente WHERE email = ?"
    cursor.execute(query, (cliente_email,))
    count = cursor.fetchone()[0]
    return count > 0

# 6. Insertar cliente si no existe
def insert_cliente(cliente):
    if not check_cliente(cliente['email']):
        # Convertir género M/F a Masculino/Femenino
        genero = cliente['genero']
        if genero == 'M' or genero == 'Masculino':
            genero = 'Masculino'
        elif genero == 'F' or genero == 'Femenino':
            genero = 'Femenino'
        else:
            genero = 'Otro'  # Si es otro valor, lo dejamos como 'Otro'

        # Convertir fechaRegistro a datetime si no lo está
        fecha_registro = cliente['fechaRegistro']
        if isinstance(fecha_registro, str):  # Si la fecha es string, convertirla
            fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d')  # Ajusta el formato si es necesario
            
        # Convertir el datetime a cadena de texto con formato compatible para SQL Server
        fecha_registro_str = fecha_registro.strftime('%Y-%m-%d %H:%M:%S')  # Convertir a 'YYYY-MM-DD HH:MM:SS'
        
        # Insertar en la base de datos
        query = """
        INSERT INTO DIM_Cliente (nombre, email, genero, pais, fechaRegistro)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (cliente['nombre'], cliente['email'], genero, cliente['pais'], fecha_registro_str))
        conn.commit()


# 7. Obtener o insertar un producto (con manejo de SKU, código_alterno y código_mongo)
def get_or_insert_producto(producto):
    sku = producto['sku'] if producto['sku'] else None
    codigo_alterno = producto['codigo_alterno'] if producto['codigo_alterno'] else None
    codigo_mongo = producto['codigo_mongo'] if producto['codigo_mongo'] else None

    # Si no tiene sku, buscar en la tabla de equivalencias por codigo_alterno o codigo_mongo
    if not sku:
        if codigo_alterno:
            query = "SELECT sku FROM EquivalenciasProductos WHERE codigo_alterno = ?"
            cursor.execute(query, (codigo_alterno,))
            sku = cursor.fetchone()
            if sku:
                sku = sku[0]  # Extraemos el valor de sku encontrado
        if not sku and codigo_mongo:
            query = "SELECT sku FROM EquivalenciasProductos WHERE codigo_mongo = ?"
            cursor.execute(query, (codigo_mongo,))
            sku = cursor.fetchone()
            if sku:
                sku = sku[0]  # Extraemos el valor de sku encontrado

    # Si aún no tenemos un sku, no podemos insertar el producto
    if not sku:
        print(f"Producto con código alterno {codigo_alterno} y código mongo {codigo_mongo} no tiene SKU, se omite la inserción.")
        return None  # Producto no insertado

    # Verificar si el producto ya existe por sku
    query = "SELECT idProducto FROM DIM_Producto WHERE sku = ?"
    cursor.execute(query, (sku,))
    id_producto = cursor.fetchone()

    if id_producto:
        return id_producto[0]  # Si ya existe, devolver su idProducto
    else:
        # Si el producto no existe, insertar en la tabla DIM_Producto
        if not producto['categoria']:
            print(f"Producto {sku} no tiene categoría asignada, se omite la inserción.")
            return None  # Omitir inserción si no tiene categoría

        query = """
        INSERT INTO DIM_Producto (sku, nombre, categoria)
        VALUES (?, ?, ?)
        """
        cursor.execute(query, (sku, producto['nombre'], producto['categoria']))
        conn.commit()

        # Obtener el último ID insertado usando SCOPE_IDENTITY()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        id_producto = cursor.fetchone()[0]
        
        return id_producto  # Devuelve el id del producto insertado

def get_id_producto(producto):
    # Si el producto tiene SKU, buscarlo directamente en DIM_Producto
    if producto['sku']:
        query = "SELECT idProducto FROM DIM_Producto WHERE sku = ?"
        cursor.execute(query, (producto['sku'],))
        id_producto = cursor.fetchone()
        if id_producto:
            return id_producto[0]

    # Si no tiene SKU, buscar por código alterno
    if producto['codigo_alterno']:
        query = "SELECT sku FROM EquivalenciasProductos WHERE codigo_alterno = ?"
        cursor.execute(query, (producto['codigo_alterno'],))
        sku = cursor.fetchone()
        if sku:
            # Si encontramos el SKU, buscarlo en DIM_Producto
            query = "SELECT idProducto FROM DIM_Producto WHERE sku = ?"
            cursor.execute(query, (sku[0],))
            id_producto = cursor.fetchone()
            if id_producto:
                return id_producto[0]

    # Si no tiene SKU ni código alterno, usar el código Mongo
    if producto['codigo_mongo']:
        query = "SELECT sku FROM EquivalenciasProductos WHERE codigo_mongo = ?"
        cursor.execute(query, (producto['codigo_mongo'],))
        sku = cursor.fetchone()
        if sku:
            # Si encontramos el SKU, buscarlo en DIM_Producto
            query = "SELECT idProducto FROM DIM_Producto WHERE sku = ?"
            cursor.execute(query, (sku[0],))
            id_producto = cursor.fetchone()
            if id_producto:
                return id_producto[0]

    # Si no se encuentra el producto, devolver None
    print(f"Producto con SKU {producto['sku']}, código alterno {producto['codigo_alterno']} y código mongo {producto['codigo_mongo']} no encontrado en el DW.")
    return None  # Producto no encontrado

def get_or_insert_canal(canal):
    # Verificar si el canal ya existe en DIM_Canal
    query = "SELECT idCanal FROM DIM_Canal WHERE canal = ?"
    cursor.execute(query, (canal,))
    id_canal = cursor.fetchone()

    if id_canal:
        # Si existe, devolver el idCanal
        return id_canal[0]
    else:
        # Si no existe, insertar el nuevo canal
        query_insert = "INSERT INTO DIM_Canal (canal) VALUES (?)"
        cursor.execute(query_insert, (canal,))
        conn.commit()

        query1 = "SELECT idCanal FROM DIM_Canal WHERE canal = ?"
        cursor.execute(query1, (canal,))
        id_canal1 = cursor.fetchone()
        return id_canal1[0]
    
# 8. Insertar ventas en la tabla FACT_Ventas con actualización del último ID insertado
def insert_fact_ventas(orden, cliente_id, producto_id):
    # Obtener el tipo de cambio desde DIM_Tiempo usando la fecha de la orden
    query_tipo_cambio = "SELECT idTiempo, tipoCambio FROM DIM_Tiempo WHERE fecha = ?"
    cursor.execute(query_tipo_cambio, (orden['fecha'],))
    tipo_cambio_data = cursor.fetchone()

    if not tipo_cambio_data:
        print(f"Error: No se encontró el tipo de cambio para la fecha {orden['fecha']}.")
        return  # Omitir la inserción si no se encuentra el tipo de cambio

    id_tiempo, tipo_cambio = tipo_cambio_data

    # Obtener o insertar el canal
    id_canal = get_or_insert_canal(orden['canal'])
    
    cantidad = orden['cantidad']
    precio_unitario = orden['precio_unitario']
    cantidad = Decimal(str(cantidad))
    precio_unitario = Decimal(str(precio_unitario))
    
    if orden['moneda'] == 'CRC':
        # Si la moneda es CRC, calculamos total_CRC con cantidad * precio_unitario
        total_crc = cantidad * precio_unitario
        # Luego, calculamos total_venta en USD, dividiendo entre tipoCambio
        total_venta = total_crc / tipo_cambio
        precio_unitario = precio_unitario / tipo_cambio
    elif orden['moneda'] == 'USD':
        # Si la moneda es USD, calculamos total_venta directamente con cantidad * precio_unitario
        total_venta = cantidad * precio_unitario
        # Calculamos total_CRC multiplicando por el tipo de cambio
        total_crc = total_venta * tipo_cambio
    else:
        # Si la moneda no es ni CRC ni USD, no se puede calcular
        print(f"Error: Moneda no válida para la orden {orden['cliente_email']} - {orden['producto_sku']}.")
        return  # Omitir la inserción si la moneda es inválida

    # Insertar la venta en la tabla FACT_Ventas
    query = """
    INSERT INTO FACT_Ventas (idCliente, idProducto, idTiempo, idCanal, cantidad, precioUnitario, descuentoPct, totalVenta, totalCRC)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (cliente_id, producto_id, id_tiempo, id_canal, cantidad, precio_unitario, 0, total_venta, total_crc))
    conn.commit()

    # Actualizar el último ID insertado en el archivo log.json
    update_log_data(orden['orden_id'])  # Asumimos que el orden_id es único



# 9. Procesar clientes e insertarlos
def process_clientes(clientes_df):
    insert_count = 0
    for _, cliente in clientes_df.iterrows():
        insert_cliente(cliente)
        insert_count += 1
    print(f"Se insertaron {insert_count} registros en la tabla DIM_Cliente.")

# 10. Procesar productos e insertarlos
def process_productos(productos_df):
    insert_count = 0
    for _, producto in productos_df.iterrows():
        get_or_insert_producto(producto)
        insert_count += 1
    print(f"Se insertaron {insert_count} registros en la tabla DIM_Producto.")

# 11. Procesar y cargar ventas
def process_ventas(ordenes_df):
    insert_count = 0
    for _, orden in ordenes_df.iterrows():
        # Buscar cliente_id en el Data Warehouse por cliente_email
        query = "SELECT idCliente FROM DIM_Cliente WHERE email = ?"
        cursor.execute(query, (orden['cliente_email'],))
        cliente_id = cursor.fetchone()

        if not cliente_id:
            print(f"Cliente con email {orden['cliente_email']} no encontrado en el DW.")
            continue  # Omite esta orden si no se encuentra el cliente

        cliente_id = cliente_id[0]

        # Obtener el producto_id utilizando la nueva función get_id_producto
        producto = {
            'sku': orden['producto_sku'],
            'codigo_alterno': orden['codigo_alterno'],
            'codigo_mongo': orden['codigo_mongo']
        }

        producto_id = get_id_producto(producto)

        if producto_id is None:
            print(f"Producto {orden['producto_sku']} no insertado o no encontrado.")
            continue  # Omite esta orden si no se encuentra o inserta el producto

        # Insertar ventas en la tabla FACT_Ventas
        insert_fact_ventas(orden, cliente_id, producto_id)
        insert_count += 1

    print(f"Se insertaron {insert_count} registros en la tabla FACT_Ventas.")

# Función principal que ejecuta todo el proceso
def main():
    # Obtener el último id y la fecha de carga desde el archivo log.json
    last_id, fecha_carga = get_log_data()
    # Extraer datos desde Neo4j
    clientes_df = extract_clientes_data()
    productos_df = extract_productos_data()
    ordenes_df = extract_ordenes_data(last_id)

    # Procesar e insertar los datos en SQL Server
    process_clientes(clientes_df)
    process_productos(productos_df)
    process_ventas(ordenes_df)

    # Cerrar la conexión
    conn.close()

# Ejecutar el script
if __name__ == "__main__":
    main()
