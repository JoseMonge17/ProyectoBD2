# loader_mysql_fixed.py
import pandas as pd
import mysql.connector
from mysql.connector import Error
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MySQLDockerLoader:
    def __init__(self, host='127.0.0.1', database='sales_mysql', 
                 user='root', password='', port=3307):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
        # Obtener la ruta del directorio donde está este script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
                auth_plugin='mysql_native_password'
            )
            logger.info("✅ Conexión establecida con MySQL Docker")
            return True
        except Error as e:
            logger.error(f"❌ Error conectando a MySQL Docker: {str(e)}")
            return False
    
    def get_csv_path(self, filename):
        """Obtener la ruta completa del archivo CSV"""
        return os.path.join(self.script_dir, filename)
    
    def verificar_archivos_csv(self):
        """Verificar que todos los archivos CSV existen en la misma carpeta del script"""
        archivos_requeridos = [
            'clientes_mysql.csv',
            'productos_mysql.csv', 
            'ordenes_mysql.csv',
            'ordenes_detalle_mysql.csv'
        ]
        
        logger.info("🔍 Verificando archivos CSV...")
        logger.info(f"📁 Buscando en: {self.script_dir}")
        
        for archivo in archivos_requeridos:
            ruta_completa = self.get_csv_path(archivo)
            if not os.path.exists(ruta_completa):
                logger.error(f"❌ Archivo no encontrado: {ruta_completa}")
                logger.info(f"   Archivos en la carpeta: {os.listdir(self.script_dir)}")
                return False
            else:
                logger.info(f"✅ {archivo} encontrado")
        
        return True
    
    def verificar_base_datos(self):
        """Verificar que la base de datos y tablas existen"""
        try:
            cursor = self.connection.cursor()
            
            # Verificar si la base de datos existe
            cursor.execute("SHOW DATABASES LIKE 'sales_mysql'")
            if not cursor.fetchone():
                logger.error("❌ La base de datos 'sales_mysql' no existe")
                return False
            
            # Verificar tablas
            cursor.execute("USE sales_mysql")
            cursor.execute("SHOW TABLES")
            tablas = cursor.fetchall()
            tablas_esperadas = {'cliente', 'producto', 'orden', 'ordendetalle'}
            tablas_encontradas = {tabla[0].lower() for tabla in tablas}
            
            if not tablas_esperadas.issubset(tablas_encontradas):
                logger.error(f"❌ Faltan tablas. Encontradas: {tablas_encontradas}")
                return False
            
            logger.info("✅ Base de datos y tablas verificadas")
            return True
            
        except Error as e:
            logger.error(f"❌ Error verificando base de datos: {str(e)}")
            return False
    
    def cargar_datos(self):
        # Primero verificar archivos
        if not self.verificar_archivos_csv():
            return False
        
        # Luego conectar a la base de datos
        if not self.connect():
            return False
        
        # Verificar que la base de datos esté lista
        if not self.verificar_base_datos():
            return False
        
        try:
            cursor = self.connection.cursor()
            total_registros = 0
            
            # 1. CARGAR CLIENTES
            logger.info("📥 Cargando clientes...")
            df_clientes = pd.read_csv(self.get_csv_path('clientes_mysql.csv'))
            
            for _, row in df_clientes.iterrows():
                cursor.execute(
                    "INSERT INTO Cliente (nombre, correo, genero, pais, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (row['nombre'], row['correo'], row['genero'], row['pais'], row['created_at'])
                )
            
            total_registros += len(df_clientes)
            logger.info(f"✅ {len(df_clientes)} clientes cargados")
            
            # 2. CARGAR PRODUCTOS
            logger.info("📥 Cargando productos...")
            df_productos = pd.read_csv(self.get_csv_path('productos_mysql.csv'))
            
            for _, row in df_productos.iterrows():
                cursor.execute(
                    "INSERT INTO Producto (codigo_alt, nombre, categoria) VALUES (%s, %s, %s)",
                    (row['codigo_alt'], row['nombre'], row['categoria'])
                )
            
            total_registros += len(df_productos)
            logger.info(f"✅ {len(df_productos)} productos cargados")
            
            # 3. CARGAR ÓRDENES
            logger.info("📥 Cargando órdenes...")
            df_ordenes = pd.read_csv(self.get_csv_path('ordenes_mysql.csv'))
            
            for _, row in df_ordenes.iterrows():
                cursor.execute(
                    "INSERT INTO Orden (cliente_id, fecha, canal, moneda, total) VALUES (%s, %s, %s, %s, %s)",
                    (row['cliente_id'], row['fecha'], row['canal'], row['moneda'], row['total'])
                )
            
            total_registros += len(df_ordenes)
            logger.info(f"✅ {len(df_ordenes)} órdenes cargadas")
            
            # 4. CARGAR DETALLES
            logger.info("📥 Cargando detalles de órdenes...")
            df_detalles = pd.read_csv(self.get_csv_path('ordenes_detalle_mysql.csv'))
            
            for _, row in df_detalles.iterrows():
                cursor.execute(
                    "INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit) VALUES (%s, %s, %s, %s)",
                    (row['orden_id'], row['producto_id'], row['cantidad'], row['precio_unit'])
                )
            
            total_registros += len(df_detalles)
            logger.info(f"✅ {len(df_detalles)} detalles cargados")
            
            self.connection.commit()
            logger.info(f"🎉 CARGA COMPLETADA: {total_registros} registros totales")
            return True
            
        except Error as e:
            logger.error(f"❌ Error en carga: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if self.connection and self.connection.is_connected():
                cursor.close()
                self.connection.close()

def main():
    loader = MySQLDockerLoader(
        host='127.0.0.1', 
        database='sales_mysql', 
        user='root',
        password='', 
        port=3307
    )
    
    loader.cargar_datos()

if __name__ == "__main__":
    main()