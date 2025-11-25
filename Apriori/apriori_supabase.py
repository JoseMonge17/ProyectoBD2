# Ejecución específica para Supabase  
from apriori_engine import AprioriEngine
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    engine = AprioriEngine()
    print("🎯 EJECUTANDO APRIORI PARA SUPABASE")
    engine.ejecutar_pipeline_completo(fuente='supabase')