# apriori_config.py
# Configuraciones y conexiones para Apriori - Reutilizando conexiones existentes
import pymongo
import pyodbc
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# CONEXIÓN MONGODB (MISMA que ETLMongo.py)
# =============================================================================
def get_mongo_connection():
    """Conexión a MongoDB Atlas - MISMA configuración que ETLMongo.py"""
    try:
        mongo_client = pymongo.MongoClient(
            "mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/?appName=MiCluster"
        )
        # Verificar conexión
        mongo_client.admin.command('ping')
        logger.info("✅ Conexión MongoDB establecida")
        return mongo_client
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        return None

def get_mongo_database():
    """Obtener base de datos Ventas de MongoDB"""
    client = get_mongo_connection()
    if client:
        return client['Ventas']
    return None

def get_mongo_collections():
    """Obtener colecciones de MongoDB"""
    db = get_mongo_database()
    if db:
        return {
            'clientes': db['Clientes'],
            'productos': db['Productos'], 
            'ordenes': db['Ordenes']
        }
    return None

# =============================================================================
# CONEXIÓN SUPABASE (VERSIÓN MEJORADA)
# =============================================================================
def get_supabase_connection():
    """Conexión a Supabase"""
    try:
        # Intentar importar psycopg2
        try:
            import psycopg2
        except ImportError:
            logger.error("❌ psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")
            return None
        
        # Configuración de conexión directa PostgreSQL
        PG_CONN = {
            "host": "aws-1-us-east-2.pooler.supabase.com",
            "port": 5432,
            "database": "postgres",
            "user": "postgres.yxlassfnrleqgcremckw",
            "password": "ZR1bpaNMMy7katsx"
        }
        
        # Probar conexión directa
        conn = psycopg2.connect(**PG_CONN)
        conn.close()
        
        logger.info("✅ Conexión Supabase establecida")
        return PG_CONN
        
    except Exception as e:
        logger.error(f"❌ Error conectando a Supabase: {e}")
        return None

def get_supabase_dataframe_connection():
    """Conexión para pandas (si psycopg2 está disponible)"""
    try:
        import psycopg2
        PG_CONN = get_supabase_connection()
        if PG_CONN:
            conn_str = f"postgresql://{PG_CONN['user']}:{PG_CONN['password']}@{PG_CONN['host']}:{PG_CONN['port']}/{PG_CONN['database']}"
            return conn_str
    except ImportError:
        logger.warning("⚠️  psycopg2 no disponible - Conexión DataFrame deshabilitada")
    return None

# =============================================================================
# CONEXIÓN SQL SERVER DW (MISMA que ETLMongo.py)
# =============================================================================
def get_sqlserver_connection():
    """Conexión a SQL Server DW - MISMA que ETLMongo.py"""
    try:
        server = 'localhost'
        database = 'DW_Proyecto_Sales'
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        )
        conn = pyodbc.connect(conn_str)
        logger.info("✅ Conexión SQL Server establecida")
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a SQL Server: {e}")
        return None

def get_sqlserver_dataframe_connection():
    """Conexión SQL Server para pandas"""
    try:
        server = 'localhost'
        database = 'DW_Proyecto_Sales'
        conn_str = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        return conn_str
    except Exception as e:
        logger.error(f"❌ Error creando conexión DataFrame SQL Server: {e}")
        return None

# =============================================================================
# CONFIGURACIONES APRIORI
# =============================================================================
# Parámetros del algoritmo Apriori
APRIORI_CONFIG = {
    'min_support': 0.005,    # 0.5% en lugar de 1%
    'min_confidence': 0.3,   # 30% en lugar de 50%
    'max_len': 3,
    'metric': 'confidence'
}

# Configuración de almacenamiento de reglas
STORAGE_CONFIG = {
    'mongodb': {
        'database': 'Recomendaciones',
        'collection': 'reglas_apriori'
    },
    'supabase': {
        'table': 'reglas_apriori'
    }
}

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================
def test_connections():
    """Probar todas las conexiones"""
    logger.info("🧪 Probando conexiones...")
    
    results = {
        'mongodb': False,
        'supabase': False, 
        'sqlserver': False
    }
    
    # Probar MongoDB
    mongo_client = get_mongo_connection()
    if mongo_client:
        results['mongodb'] = True
        mongo_client.close()
        logger.info("   ✅ MongoDB: CONECTADO")
    else:
        logger.info("   ❌ MongoDB: FALLÓ")
    
    # Probar Supabase
    supabase_conn = get_supabase_connection()
    if supabase_conn:
        results['supabase'] = True
        logger.info("   ✅ Supabase: CONECTADO")
    else:
        logger.info("   ❌ Supabase: FALLÓ")
    
    # Probar SQL Server
    sql_conn = get_sqlserver_connection()
    if sql_conn:
        results['sqlserver'] = True
        sql_conn.close()
        logger.info("   ✅ SQL Server: CONECTADO")
    else:
        logger.info("   ❌ SQL Server: FALLÓ")
    
    return results

if __name__ == "__main__":
    # Ejecutar pruebas al correr directamente
    test_connections()