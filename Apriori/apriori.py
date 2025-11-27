import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import pymongo
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parámetros 
MIN_SUPPORT = 0.0005
MIN_CONFIDENCE = 0.01

# Conexiones
MONGO_CONN = "mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/?appName=MiCluster"
SUPABASE_CONN = {
    "host": "aws-1-us-east-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres", 
    "user": "postgres.yxlassfnrleqgcremckw",
    "password": "ZR1bpaNMMy7katsx"
}

def obtener_nombres_productos_mongo():
    """Obtener mapeo de ID a nombre desde MongoDB"""
    client = pymongo.MongoClient(MONGO_CONN)
    db = client['Ventas']
    
    productos = db['Productos'].find({}, {'_id': 1, 'nombre': 1})
    mapeo = {str(p['_id']): p.get('nombre', 'Sin nombre') for p in productos}
    
    client.close()
    return mapeo

def obtener_nombres_productos_supabase():
    """Obtener mapeo de ID a nombre desde Supabase - SIN pandas para evitar warning"""
    conn = psycopg2.connect(**SUPABASE_CONN)
    cursor = conn.cursor()
    
    cursor.execute("SELECT producto_id::text, nombre FROM producto")
    resultados = cursor.fetchall()
    
    mapeo = {str(row[0]): row[1] for row in resultados}
    
    cursor.close()
    conn.close()
    return mapeo

def extraer_datos_supabase():
    """Extraer datos de Supabase - SIN pandas para evitar warning"""
    print("=== Cargando datos de Supabase ===")
    
    conn = psycopg2.connect(**SUPABASE_CONN)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        orden_id::text as transaction_id,
        producto_id::text as item
    FROM orden_detalle
    """)
    
    resultados = cursor.fetchall()
    
    # Crear DataFrame manualmente
    df = pd.DataFrame(resultados, columns=['transaction_id', 'item'])
    
    if not df.empty:
        print(f"Transacciones: {df['transaction_id'].nunique()}")
        print(f"Productos únicos: {df['item'].nunique()}")
        
        # Mostrar algunos datos con nombres
        mapeo = obtener_nombres_productos_supabase()
        df_sample = df.head(10).copy()
        df_sample['nombre_producto'] = df_sample['item'].map(mapeo)
        print("Primeras transacciones:")
        print(df_sample[['transaction_id', 'item', 'nombre_producto']])
    
    cursor.close()
    conn.close()
    return df

def extraer_datos_mongo():
    """Extraer datos de MongoDB"""
    print("=== Cargando datos de MongoDB ===")
    
    client = pymongo.MongoClient(MONGO_CONN)
    db = client['Ventas']
    
    pipeline = [
        {'$unwind': '$items'},
        {'$project': {
            'transaction_id': '$_id',
            'item': '$items.producto_id'
        }}
    ]
    
    cursor = db.Ordenes.aggregate(pipeline)
    df = pd.DataFrame(list(cursor))
    
    if not df.empty:
        df = df[['transaction_id', 'item']]
        df['item'] = df['item'].astype(str)
        print(f"Transacciones: {df['transaction_id'].nunique()}")
        print(f"Productos únicos: {df['item'].nunique()}")
        
        # Mostrar algunos datos con nombres
        mapeo = obtener_nombres_productos_mongo()
        df_sample = df.head(10).copy()
        df_sample['nombre_producto'] = df_sample['item'].map(mapeo)
        print("Primeras transacciones:")
        print(df_sample[['transaction_id', 'item', 'nombre_producto']])
    
    client.close()
    return df

def transformar_a_one_hot(df):
    """Transformar a formato one-hot"""
    print("=== Transformación a formato one-hot ===")
    
    basket = (
        df
        .groupby(['transaction_id', 'item'])['item']
        .count()
        .unstack()
        .fillna(0)
    )
    
    basket = basket.astype(bool)
    print(f"Formato: {basket.shape[0]} transacciones x {basket.shape[1]} productos")
    
    densidad = (basket.sum().sum() / (basket.shape[0] * basket.shape[1])) * 100
    print(f"Densidad: {densidad:.4f}%")
    
    return basket

def guardar_reglas_mongo(rules, fuente):
    """Guardar reglas SOLO en MongoDB para la fuente correspondiente"""
    print(f"=== Guardando reglas de {fuente} en MongoDB ===")
    
    client = pymongo.MongoClient(MONGO_CONN)
    db = client['Recomendaciones']
    collection = db['reglas_apriori']
    
    rules_data = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    rules_data['antecedents'] = rules_data['antecedents'].apply(list)
    rules_data['consequents'] = rules_data['consequents'].apply(list)
    rules_data['fuente'] = fuente
    
    # Solo borrar las reglas de esta fuente específica
    collection.delete_many({'fuente': fuente})
    result = collection.insert_many(rules_data.to_dict('records'))
    print(f"Reglas guardadas en MongoDB: {len(result.inserted_ids)}")
    client.close()

def guardar_reglas_supabase(rules, fuente):
    """Guardar reglas SOLO en Supabase para la fuente correspondiente"""
    print(f"=== Guardando reglas de {fuente} en Supabase ===")
    
    conn = psycopg2.connect(**SUPABASE_CONN)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reglas_apriori (
        id SERIAL PRIMARY KEY,
        antecedents TEXT[],
        consequents TEXT[],
        support FLOAT,
        confidence FLOAT,
        lift FLOAT,
        fuente TEXT
    )
    """)
    
    # Solo borrar las reglas de esta fuente específica
    cursor.execute("DELETE FROM reglas_apriori WHERE fuente = %s", (fuente,))
    
    for _, rule in rules.iterrows():
        cursor.execute(
            "INSERT INTO reglas_apriori (antecedents, consequents, support, confidence, lift, fuente) VALUES (%s, %s, %s, %s, %s, %s)",
            (list(rule['antecedents']), list(rule['consequents']), 
             float(rule['support']), float(rule['confidence']), float(rule['lift']), fuente)
        )
    
    conn.commit()
    print(f"Reglas guardadas en Supabase: {len(rules)}")
    cursor.close()
    conn.close()

def ejecutar_apriori(fuente):
    """Ejecutar Apriori para una fuente específica"""
    
    if fuente == 'mongo':
        df = extraer_datos_mongo()
        mapeo_productos = obtener_nombres_productos_mongo()
    else:
        df = extraer_datos_supabase()
        mapeo_productos = obtener_nombres_productos_supabase()
    
    if df.empty:
        print("No hay datos para procesar")
        return
    
    basket = transformar_a_one_hot(df)
    
    print("=== Fase 1: Conjuntos frecuentes ===")
    frequent_itemsets = apriori(
        basket,
        min_support=MIN_SUPPORT,
        use_colnames=True,
        max_len=3
    )
    
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(len)
    print(f"Encontrados {len(frequent_itemsets)} itemsets frecuentes")
    
    itemsets_multiples = frequent_itemsets[frequent_itemsets['length'] >= 2]
    if not itemsets_multiples.empty:
        print("Itemsets con múltiples productos:")
        for _, itemset in itemsets_multiples.head(10).iterrows():
            productos = [mapeo_productos.get(item, item) for item in itemset['itemsets']]
            print(f"  {productos} (soporte: {itemset['support']:.4f})")
    
    print("=== Fase 2: Reglas de asociación ===")
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=MIN_CONFIDENCE
    )
    
    if not rules.empty:
        print(f"Encontradas {len(rules)} reglas:")
        
        # Mostrar con nombres
        def traducir_itemset(itemset):
            return [mapeo_productos.get(item, item) for item in itemset]
        
        rules['antecedents_nombres'] = rules['antecedents'].apply(traducir_itemset)
        rules['consequents_nombres'] = rules['consequents'].apply(traducir_itemset)
        
        rules_to_show = rules[['antecedents_nombres', 'consequents_nombres', 'support', 'confidence', 'lift']]
        print(rules_to_show.head(20))
        
        # Guardar reglas según la fuente
        if fuente == 'mongo':
            guardar_reglas_mongo(rules, fuente)
        else:  # supabase
            guardar_reglas_supabase(rules, fuente)
        
    else:
        print("No se encontraron reglas. Intenta bajar más MIN_SUPPORT y MIN_CONFIDENCE")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python apriori_corregido.py [mongo|supabase]")
        sys.exit(1)
    
    fuente = sys.argv[1]
    if fuente not in ['mongo', 'supabase']:
        print("Fuente debe ser 'mongo' o 'supabase'")
        sys.exit(1)
    
    ejecutar_apriori(fuente)