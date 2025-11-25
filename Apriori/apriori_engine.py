# apriori_engine.py
# Motor principal del algoritmo Apriori para el proyecto
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
import logging
from apriori_config import (
    get_mongo_connection,
    get_supabase_connection, 
    APRIORI_CONFIG,
    STORAGE_CONFIG
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AprioriEngine:
    def __init__(self):
        self.mongo_client = None
        self.supabase_conn = None
        self.sql_engine = None
        self.initialize_connections()
    
    def initialize_connections(self):
        """Inicializar todas las conexiones"""
        logger.info("🔌 Inicializando conexiones...")
        
        # MongoDB
        self.mongo_client = get_mongo_connection()
        
        # Supabase  
        self.supabase_conn = get_supabase_connection()

        logger.info("✅ Conexiones inicializadas")
    
    # =========================================================================
    # EXTRACCIÓN DE DATOS
    # =========================================================================
    
    def extraer_datos_mongo(self):
        """Extraer datos transaccionales de MongoDB"""
        logger.info("📥 Extrayendo datos de MongoDB...")
        
        try:
            db = self.mongo_client['Ventas']
            
            # Pipeline para extraer transacciones (orden -> productos)
            pipeline = [
                {'$unwind': '$items'},  # Descomponer array de items
                {'$project': {
                    'transaction_id': '$_id',  # OrdenId como transaction_id
                    'item': '$items.producto_id'  # ProductoId como item
                }}
            ]
            
            cursor = db.Ordenes.aggregate(pipeline)
            df = pd.DataFrame(list(cursor))
            
            # Limpiar y formatear
            df = df[['transaction_id', 'item']].dropna()
            df['item'] = df['item'].astype(str)
            
            logger.info(f"✅ MongoDB: {len(df)} transacciones extraídas")
            logger.info(f"   - Transacciones únicas: {df['transaction_id'].nunique()}")
            logger.info(f"   - Productos únicos: {df['item'].nunique()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos MongoDB: {e}")
            return pd.DataFrame()
    
    def extraer_datos_supabase(self):
        """Extraer datos transaccionales de Supabase"""
        logger.info("📥 Extrayendo datos de Supabase...")
        
        try:
            # Usar conexión directa si psycopg2 está disponible
            import psycopg2
            conn = psycopg2.connect(**self.supabase_conn)
            
            query = """
            SELECT 
                orden_id as transaction_id,
                producto_id as item
            FROM orden_detalle
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            # Limpiar y formatear
            df['item'] = df['item'].astype(str)
            
            logger.info(f"✅ Supabase: {len(df)} transacciones extraídas")
            logger.info(f"   - Transacciones únicas: {df['transaction_id'].nunique()}")
            logger.info(f"   - Productos únicos: {df['item'].nunique()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos Supabase: {e}")
            return pd.DataFrame()
    
    
    # =========================================================================
    # TRANSFORMACIÓN DE DATOS
    # =========================================================================
    
    def transformar_a_one_hot(self, df):
        """Transformar datos a formato one-hot para Apriori"""
        logger.info("🔄 Transformando a formato one-hot...")
        
        if df.empty:
            logger.warning("⚠️  DataFrame vacío, no se puede transformar")
            return pd.DataFrame()
        
        try:
            # Crear tabla transacción x item
            basket = (
                df.groupby(['transaction_id', 'item'])['item']
                .count()
                .unstack()
                .reset_index()
                .fillna(0)
                .set_index('transaction_id')
            )
            
            # Convertir a boolean (1/0)
            basket = basket.astype(bool)
            
            logger.info(f"✅ Formato one-hot creado:")
            logger.info(f"   - Transacciones: {basket.shape[0]}")
            logger.info(f"   - Productos: {basket.shape[1]}")
            logger.info(f"   - Densidad: {(basket.sum().sum() / (basket.shape[0] * basket.shape[1]) * 100):.2f}%")
            
            return basket
            
        except Exception as e:
            logger.error(f"❌ Error transformando a one-hot: {e}")
            return pd.DataFrame()
    
    # =========================================================================
    # ALGORITMO APRIORI
    # =========================================================================
    
    def ejecutar_apriori(self, basket):
        """Ejecutar algoritmo Apriori y generar reglas"""
        logger.info("🔍 Ejecutando algoritmo Apriori...")
        
        if basket.empty or basket.shape[0] < 10:
            logger.warning("⚠️  Datos insuficientes para Apriori")
            return pd.DataFrame()
        
        try:
            # Fase 1: Itemsets frecuentes
            logger.info(f"📊 Buscando itemsets frecuentes (soporte ≥ {APRIORI_CONFIG['min_support']})...")
            
            frequent_itemsets = apriori(
                basket,
                min_support=APRIORI_CONFIG['min_support'],
                use_colnames=True,
                max_len=APRIORI_CONFIG['max_len']
            )
            
            logger.info(f"✅ Itemsets frecuentes encontrados: {len(frequent_itemsets)}")
            
            if frequent_itemsets.empty:
                logger.warning("⚠️  No se encontraron itemsets frecuentes")
                return pd.DataFrame()
            
            # Mostrar itemsets más frecuentes
            top_itemsets = frequent_itemsets.nlargest(5, 'support')
            logger.info("🏆 Top 5 itemsets más frecuentes:")
            for idx, itemset in top_itemsets.iterrows():
                items = list(itemset['itemsets'])
                logger.info(f"   {items} (soporte: {itemset['support']:.3f})")
            
            # Fase 2: Reglas de asociación
            logger.info(f"📊 Generando reglas (confianza ≥ {APRIORI_CONFIG['min_confidence']})...")
            
            rules = association_rules(
                frequent_itemsets,
                metric=APRIORI_CONFIG['metric'],
                min_threshold=APRIORI_CONFIG['min_confidence']
            )
            
            logger.info(f"✅ Reglas generadas: {len(rules)}")
            
            if not rules.empty:
                # Ordenar por confianza y lift
                rules = rules.sort_values(['confidence', 'lift'], ascending=[False, False])
                
                # Mostrar mejores reglas
                top_rules = rules.head(5)
                logger.info("🏆 Top 5 reglas (por confianza):")
                for idx, rule in top_rules.iterrows():
                    ant = list(rule['antecedents'])
                    cons = list(rule['consequents'])
                    logger.info(f"   {ant} → {cons} (conf: {rule['confidence']:.3f}, lift: {rule['lift']:.3f})")
            
            return rules
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando Apriori: {e}")
            return pd.DataFrame()
    
    # =========================================================================
    # ALMACENAMIENTO DE RESULTADOS
    # =========================================================================
    
    def guardar_reglas_mongo(self, rules):
        """Guardar reglas en MongoDB"""
        logger.info("💾 Guardando reglas en MongoDB...")
        
        if rules.empty:
            logger.warning("⚠️  No hay reglas para guardar")
            return False
        
        try:
            db = self.mongo_client[STORAGE_CONFIG['mongodb']['database']]
            collection = db[STORAGE_CONFIG['mongodb']['collection']]
            
            # Preparar datos para MongoDB
            rules_data = rules[[
                'antecedents', 'consequents', 'support', 
                'confidence', 'lift', 'conviction'
            ]].copy()
            
            # Convertir frozenset a list para JSON
            rules_data['antecedents'] = rules_data['antecedents'].apply(list)
            rules_data['consequents'] = rules_data['consequents'].apply(list)
            rules_data['antecedents_str'] = rules_data['antecedents'].apply(lambda x: ', '.join(x))
            rules_data['consequents_str'] = rules_data['consequents'].apply(lambda x: ', '.join(x))
            
            # Convertir a diccionario
            records = rules_data.to_dict('records')
            
            # Limpiar colección anterior e insertar nuevas
            collection.delete_many({})
            result = collection.insert_many(records)
            
            logger.info(f"✅ {len(result.inserted_ids)} reglas guardadas en MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando reglas en MongoDB: {e}")
            return False
    
    def guardar_reglas_supabase(self, rules):
        """Guardar reglas en Supabase"""
        logger.info("💾 Guardando reglas en Supabase...")
        
        if rules.empty:
            logger.warning("⚠️  No hay reglas para guardar")
            return False
        
        try:
            import psycopg2
            conn = psycopg2.connect(**self.supabase_conn)
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS reglas_apriori (
                id SERIAL PRIMARY KEY,
                antecedents TEXT[],
                consequents TEXT[],
                antecedents_str TEXT,
                consequents_str TEXT,
                support FLOAT,
                confidence FLOAT,
                lift FLOAT,
                conviction FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
            cursor.execute(create_table_query)
            
            # Limpiar tabla anterior
            cursor.execute("DELETE FROM reglas_apriori")
            
            # Insertar nuevas reglas
            insert_query = """
            INSERT INTO reglas_apriori 
            (antecedents, consequents, antecedents_str, consequents_str, support, confidence, lift, conviction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for _, rule in rules.iterrows():
                antecedents = list(rule['antecedents'])
                consequents = list(rule['consequents'])
                antecedents_str = ', '.join(antecedents)
                consequents_str = ', '.join(consequents)
                
                cursor.execute(insert_query, (
                    antecedents, consequents, antecedents_str, consequents_str,
                    float(rule['support']), float(rule['confidence']), 
                    float(rule['lift']), float(rule['conviction'])
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ {len(rules)} reglas guardadas en Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando reglas en Supabase: {e}")
            return False
    
    # =========================================================================
    # PIPELINE COMPLETO
    # =========================================================================
    
    def ejecutar_pipeline_completo(self, fuente='dw'):
        """Ejecutar pipeline completo de Apriori"""
        logger.info("🚀 INICIANDO PIPELINE APRIORI COMPLETO")
        
        try:
            # 1. EXTRACCIÓN - Elegir fuente de datos
            if fuente == 'mongo':
                df = self.extraer_datos_mongo()
            else:  # dw por defecto
                df = self.extraer_datos_supabase()
            
            if df.empty:
                logger.error("❌ No se pudieron extraer datos")
                return False
            
            # 2. TRANSFORMACIÓN
            basket = self.transformar_a_one_hot(df)
            if basket.empty:
                logger.error("❌ No se pudo transformar datos")
                return False
            
            # 3. ALGORITMO APRIORI
            rules = self.ejecutar_apriori(basket)
            if rules.empty:
                logger.error("❌ No se generaron reglas")
                return False
            
            # 4. ALMACENAMIENTO
            mongo_success = self.guardar_reglas_mongo(rules)
            supabase_success = self.guardar_reglas_supabase(rules)
            
            if mongo_success or supabase_success:
                logger.info("🎉 PIPELINE APRIORI COMPLETADO EXITOSAMENTE")
                return True
            else:
                logger.error("❌ No se pudieron guardar las reglas")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error en pipeline Apriori: {e}")
            return False
    
    def obtener_estadisticas(self):
        """Obtener estadísticas de las reglas almacenadas"""
        try:
            stats = {}
            
            # MongoDB stats
            db = self.mongo_client[STORAGE_CONFIG['mongodb']['database']]
            collection = db[STORAGE_CONFIG['mongodb']['collection']]
            stats['mongodb'] = collection.count_documents({})
            
            # Supabase stats
            import psycopg2
            conn = psycopg2.connect(**self.supabase_conn)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM reglas_apriori")
            stats['supabase'] = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def main():
    """Función principal para ejecutar desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar algoritmo Apriori')
    parser.add_argument('--fuente', choices=['dw', 'mongo', 'supabase'], 
                       default='dw', help='Fuente de datos (default: dw)')
    parser.add_argument('--min-support', type=float, 
                       default=APRIORI_CONFIG['min_support'], help='Soporte mínimo')
    parser.add_argument('--min-confidence', type=float,
                       default=APRIORI_CONFIG['min_confidence'], help='Confianza mínima')
    
    args = parser.parse_args()
    
    # Actualizar configuración con argumentos
    APRIORI_CONFIG['min_support'] = args.min_support
    APRIORI_CONFIG['min_confidence'] = args.min_confidence
    
    # Ejecutar pipeline
    engine = AprioriEngine()
    success = engine.ejecutar_pipeline_completo(fuente=args.fuente)
    
    if success:
        stats = engine.obtener_estadisticas()
        logger.info(f"📊 Estadísticas finales: MongoDB={stats.get('mongodb', 0)}, Supabase={stats.get('supabase', 0)}")
    else:
        logger.error("❌ Pipeline falló")

if __name__ == "__main__":
    main()