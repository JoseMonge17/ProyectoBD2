# loader_sqlalchemy_fixed.py
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLAlchemyLoaderFixed:
    def __init__(self, server='localhost', database='Ventas_Transactional'):
        self.connection_string = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        self.engine = None
        # Rutas absolutas a los archivos CSV
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_files = {
            'clientes': os.path.join(self.script_dir, 'clientes.csv'),
            'productos': os.path.join(self.script_dir, 'productos.csv'),
            'ordenes': os.path.join(self.script_dir, 'ordenes.csv'),
            'ordenes_detalle': os.path.join(self.script_dir, 'ordenes_detalle.csv')
        }
    
    def connect(self):
        try:
            self.engine = create_engine(self.connection_string)
            logger.info(" Conexión establecida con SQLAlchemy")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {str(e)}")
            return False
    
    def verificar_archivos(self):
        """Verificar que todos los archivos CSV existan"""
        logger.info(" Verificando archivos CSV...")
        for nombre, archivo in self.csv_files.items():
            if not os.path.exists(archivo):
                logger.error(f"❌ Archivo no encontrado: {archivo}")
                return False
            logger.info(f" {nombre}: {archivo}")
        return True
    
    def verificar_tabla_vacia(self, tabla):
        """Verificar si una tabla está vacía"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM sales_ms.{tabla}"))
                count = result.scalar()
                return count == 0
        except Exception as e:
            logger.error(f"❌ Error verificando tabla {tabla}: {str(e)}")
            return True  # Si hay error, asumimos que está vacía
    
    def cargar_datos_con_validacion(self):
        """Cargar datos con validaciones previas"""
        
        if not self.connect():
            return False
        
        if not self.verificar_archivos():
            return False
        
        try:
            total_registros = 0
            estadisticas = {}
            
            # 1. CARGAR CLIENTES
            logger.info(" Verificando clientes...")
            if self.verificar_tabla_vacia('Cliente'):
                logger.info(" Cargando clientes...")
                df_clientes = pd.read_csv(self.csv_files['clientes'])
                if 'ClienteId' in df_clientes.columns:
                    df_clientes = df_clientes.drop('ClienteId', axis=1)
                
                df_clientes.to_sql(
                    name='Cliente',
                    con=self.engine,
                    schema='sales_ms',
                    if_exists='append',
                    index=False,
                    chunksize=1000
                )
                estadisticas['clientes'] = len(df_clientes)
                total_registros += len(df_clientes)
                logger.info(f" {len(df_clientes)} clientes cargados")
            else:
                logger.info(" Clientes ya existen, omitiendo...")
                estadisticas['clientes'] = 0
            
            # 2. CARGAR PRODUCTOS
            logger.info(" Verificando productos...")
            if self.verificar_tabla_vacia('Producto'):
                logger.info(" Cargando productos...")
                df_productos = pd.read_csv(self.csv_files['productos'])
                if 'ProductoId' in df_productos.columns:
                    df_productos = df_productos.drop('ProductoId', axis=1)
                
                df_productos.to_sql(
                    name='Producto',
                    con=self.engine,
                    schema='sales_ms',
                    if_exists='append',
                    index=False,
                    chunksize=1000
                )
                estadisticas['productos'] = len(df_productos)
                total_registros += len(df_productos)
                logger.info(f" {len(df_productos)} productos cargados")
            else:
                logger.info(" Productos ya existen, omitiendo...")
                estadisticas['productos'] = 0
            
            # 3. CARGAR ÓRDENES
            logger.info(" Verificando órdenes...")
            if self.verificar_tabla_vacia('Orden'):
                logger.info(" Cargando órdenes...")
                df_ordenes = pd.read_csv(self.csv_files['ordenes'])
                if 'OrdenId' in df_ordenes.columns:
                    df_ordenes = df_ordenes.drop('OrdenId', axis=1)
                
                df_ordenes.to_sql(
                    name='Orden',
                    con=self.engine,
                    schema='sales_ms',
                    if_exists='append',
                    index=False,
                    chunksize=1000
                )
                estadisticas['ordenes'] = len(df_ordenes)
                total_registros += len(df_ordenes)
                logger.info(f" {len(df_ordenes)} órdenes cargadas")
            else:
                logger.info(" Órdenes ya existen, omitiendo...")
                estadisticas['ordenes'] = 0
            
            # 4. CARGAR DETALLES
            logger.info(" Verificando detalles...")
            if self.verificar_tabla_vacia('OrdenDetalle'):
                logger.info(" Cargando detalles de órdenes...")
                df_detalles = pd.read_csv(self.csv_files['ordenes_detalle'])
                if 'OrdenDetalleId' in df_detalles.columns:
                    df_detalles = df_detalles.drop('OrdenDetalleId', axis=1)
                
                df_detalles.to_sql(
                    name='OrdenDetalle',
                    con=self.engine,
                    schema='sales_ms',
                    if_exists='append',
                    index=False,
                    chunksize=1000
                )
                estadisticas['detalles'] = len(df_detalles)
                total_registros += len(df_detalles)
                logger.info(f" {len(df_detalles)} detalles cargados")
            else:
                logger.info(" Detalles ya existen, omitiendo...")
                estadisticas['detalles'] = 0
            
            logger.info(f"CARGA COMPLETADA: {total_registros} registros totales")
            
            # Imprimir estadísticas para que el frontend las capture
            print(f"ESTADISTICAS: {estadisticas}")
            return True, estadisticas
            
        except Exception as e:
            logger.error(f"❌ Error en carga: {str(e)}")
            return False, {}
        finally:
            if self.engine:
                self.engine.dispose()

def main():
    loader = SQLAlchemyLoaderFixed()
    success, estadisticas = loader.cargar_datos_con_validacion()
    
    # Salida estructurada para el frontend
    if success:
        print(f"RESULTADO: EXITO")
        print(f"CLIENTES: {estadisticas.get('clientes', 0)}")
        print(f"PRODUCTOS: {estadisticas.get('productos', 0)}") 
        print(f"ORDENES: {estadisticas.get('ordenes', 0)}")
        print(f"DETALLES: {estadisticas.get('detalles', 0)}")
    else:
        print(f"RESULTADO: ERROR")

if __name__ == "__main__":
    main()