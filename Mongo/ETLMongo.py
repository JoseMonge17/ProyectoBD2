import pymongo
import pyodbc
from datetime import datetime
from dateutil import parser

# Conexión a MongoDB Atlas
mongo_client = pymongo.MongoClient("mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/?appName=MiCluster")
db = mongo_client['Ventas']  # Nombre de la base de datos
clientes_collection = db['Clientes']
productos_collection = db['Productos']
ordenes_collection = db['Ordenes']

# Conexión a SQL Server
server = 'localhost'
database = 'DW_Proyecto_Sales'
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# 1. Función para obtener el idCliente desde la DW
def get_cliente_id(cliente_email):
    query = "SELECT idCliente FROM DIM_Cliente WHERE email = ?"
    cursor.execute(query, (cliente_email,))
    cliente_id_dw = cursor.fetchone()
    if cliente_id_dw:
        return cliente_id_dw[0]
    else:
        print(f"Error: Cliente con email {cliente_email} no encontrado en DIM_Cliente.")
        return None

def get_producto_id(producto):
    # Verificar si el producto tiene equivalencias
    if producto.get('equivalencias'):
        # Si tiene equivalencias, buscar el sku dentro de equivalencias
        sku = producto['equivalencias'].get('sku')
    else:
        # Si no tiene equivalencias, buscar por codigo_mongo o codigo_alterno
        codigo = producto.get('codigo_mongo', producto.get('codigo_alt'))
        if codigo:
            query = "SELECT sku FROM EquivalenciasProductos WHERE codigo_mongo = ? OR codigo_alterno = ?"
            cursor.execute(query, (codigo, codigo))
            resultado = cursor.fetchone()
            sku = resultado[0]
    if sku:
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
        query = "SELECT sku FROM EquivalenciasProductos WHERE codigo_mongo = ? OR codigo_alterno = ?"
        cursor.execute(query, (codigo, codigo))
        sku = cursor.fetchone()
        return sku[0]
    else:
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
        return cursor.lastrowid

# 5. Insertar ventas en la tabla FACT_Ventas
def insert_fact_ventas(cliente_id, producto_id, idTiempo, cantidad, precio_unit, total_venta, total_crc, canal):
    id_canal = get_canal_id(canal)
    
    if id_canal:
        query = """
        INSERT INTO FACT_Ventas (idCliente, idProducto, idTiempo, idCanal, cantidad, precioUnitario, descuentoPct, totalVenta, totalCRC)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (cliente_id, producto_id, idTiempo, id_canal, cantidad, precio_unit, 0, total_venta, total_crc))
        conn.commit()

# 6. Función para procesar los datos de MongoDB y cargar en SQL Server
def process_mongo_data():
    # Extraer y procesar clientes
    '''for cliente in clientes_collection.find():
        cliente_id = cliente["_id"]
        email = cliente["email"]
        genero = cliente.get("genero", "").capitalize()
        
        # Si el genero es M o F, lo convertimos a Masculino/Femenino
        if genero in ['M', 'F']:
            genero = "Masculino" if genero == 'M' else "Femenino"
        
        # Obtenemos la fecha de registro
        fecha_registro = cliente.get("creado", datetime.now())

        query_insert_cliente = """
        INSERT INTO DIM_Cliente (nombre, email, genero, pais, fechaRegistro) 
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query_insert_cliente, (cliente['nombre'], email, genero, cliente['pais'], fecha_registro))
        conn.commit()
        

    # Extraer y procesar productos
    for producto in productos_collection.find():
        # Si el producto tiene equivalencias, buscamos el SKU directamente dentro de las equivalencias
        if producto.get('equivalencias'):
            sku = producto['equivalencias'].get('sku')
        else:
            # Si no tiene equivalencias, buscamos el SKU usando el código_mongo
            sku = get_producto_sku(producto)
            
        if sku:
            id_producto = get_producto_id(producto)  # Aquí usaremos la nueva lógica de get_producto_id
            if id_producto:
                continue  # Si ya existe en la base de datos, no hacemos nada más
            # Si no existe, insertamos el producto usando el SKU de equivalencias
            query_insert_producto = """
            INSERT INTO DIM_Producto (sku, nombre, categoria)
            VALUES (?, ?, ?)
            """
            cursor.execute(query_insert_producto, (sku, producto['nombre'], producto['categoria']))
            conn.commit()
    '''
    conta = 0
    # Extraer y procesar órdenes
    for orden in ordenes_collection.find():
        # Obtener el cliente_id y luego recuperar el email del cliente
        cliente_id = orden['cliente_id']
        cliente = clientes_collection.find_one({"_id": cliente_id})  # Buscar cliente por ObjectId
        if cliente:
            email_cliente = cliente['email']  # Obtener el email del cliente
        else:
            
            continue  # Si no se encuentra el cliente, se salta la orden

        # Usar el email para obtener el cliente_id desde la base de datos
        cliente_id = get_cliente_id(email_cliente)  # Pasamos el email a get_cliente_id
        if not cliente_id:
            continue  # Skip orders for customers not found in DB
        
        if isinstance(orden['fecha'], datetime):
            # Si ya es un datetime, simplemente formateamos
            fecha_obj = orden['fecha']
        else:
            # Si es una cadena de texto, usamos isoparse para convertirlo en datetime
            fecha_str = orden['fecha']
            fecha_obj = parser.isoparse(fecha_str)

        # Formatear la fecha para que esté en el formato YYYY-MM-DD HH:MM:SS
        fecha_sql = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
        
        query_tipo_cambio = "SELECT idTiempo, tipoCambio FROM DIM_Tiempo WHERE fecha = ?"
        cursor.execute(query_tipo_cambio, (fecha_sql,))
        tipo_cambio_data = cursor.fetchone()
        
                
        for item in orden["items"]:
            producto = productos_collection.find_one({"_id": item["producto_id"]})
            producto_id = get_producto_id(producto)
            if not producto_id:
                continue  # Skip orders with products not found in DB

            # Calculamos total_venta y total_crc
            cantidad = item["cantidad"]
            precio_unit = item["precio_unit"]

            total_crc = cantidad * precio_unit
            
            if tipo_cambio_data:
                id_tiempo, tipo_cambio = tipo_cambio_data
                total_venta = total_crc / tipo_cambio  # Convert CRC to USD
            else:
                print(f" No se encontró el idTiempo para la fecha {orden['fecha']}.")  # Error: Tipo de cambio no encontrado
                continue

            insert_fact_ventas(cliente_id, producto_id, id_tiempo, cantidad, precio_unit/tipo_cambio, total_venta, total_crc, orden['canal'])
        conta += 1
        print("Orden terminada", conta)

# 7. Función principal que ejecuta todo el proceso
def main():
    process_mongo_data()
    print("Datos procesados y cargados en SQL Server.")

# Ejecutar el script
if __name__ == "__main__":
    main()
