# loader_sqlalchemy_fixed.py
import pandas as pd
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLAlchemyLoaderFixed:
    def __init__(self, server='localhost', database='Ventas_Transactional'):
        self.connection_string = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        self.engine = None
    
    def connect(self):
        try:
            self.engine = create_engine(self.connection_string)
            logger.info("✅ Conexión establecida con SQLAlchemy")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {str(e)}")
            return False
    
    def cargar_datos_sin_ids(self):
        """Cargar datos omitiendo las columnas ID"""
        
        if not self.connect():
            return False
        
        try:
            total_registros = 0
            
            # 1. CARGAR CLIENTES (sin ClienteId)
            logger.info("📥 Cargando clientes...")
            df_clientes = pd.read_csv('clientes.csv')
            # Quitar columna ClienteId si existe
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
            total_registros += len(df_clientes)
            logger.info(f"✅ {len(df_clientes)} clientes cargados")
            
            # 2. CARGAR PRODUCTOS (sin ProductoId)
            logger.info("📥 Cargando productos...")
            df_productos = pd.read_csv('productos.csv')
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
            total_registros += len(df_productos)
            logger.info(f"✅ {len(df_productos)} productos cargados")
            
            # 3. CARGAR ÓRDENES (sin OrdenId)
            logger.info("📥 Cargando órdenes...")
            df_ordenes = pd.read_csv('ordenes.csv')
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
            total_registros += len(df_ordenes)
            logger.info(f"✅ {len(df_ordenes)} órdenes cargadas")
            
            # 4. CARGAR DETALLES (sin OrdenDetalleId)
            logger.info("📥 Cargando detalles de órdenes...")
            df_detalles = pd.read_csv('ordenes_detalle.csv')
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
            total_registros += len(df_detalles)
            logger.info(f"✅ {len(df_detalles)} detalles cargados")
            
            logger.info(f"🎉 CARGA COMPLETADA: {total_registros} registros totales")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en carga: {str(e)}")
            return False
        finally:
            if self.engine:
                self.engine.dispose()

def main():
    loader = SQLAlchemyLoaderFixed()
    loader.cargar_datos_sin_ids()

if __name__ == "__main__":
    main()