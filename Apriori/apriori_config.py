# Configuraciones y conexiones (reutilizar de tus ETLs existentes)
import pymongo
from supabase import create_client

def get_mongo_connection():
    # MISMA configuración que ETLMongo.py
    return pymongo.MongoClient("mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/")

def get_supabase_connection():
    # MISMA configuración que etl_supabase.py  
    return create_client("tu_url_supabase", "tu_key_supabase")