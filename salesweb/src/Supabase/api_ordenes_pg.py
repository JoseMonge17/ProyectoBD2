# api_ordenes_pg.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor

# -------------------------
# CONFIGURACIÓN PostgreSQL
# -------------------------
PG_CONN = {
    "host": "aws-1-us-east-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.yxlassfnrleqgcremckw",
    "password": "ZR1bpaNMMy7katsx"
}

# -------------------------
# Inicializar FastAPI
# -------------------------
app = FastAPI(title="API de Órdenes - public")

# -------------------------
# Habilitar CORS
# -------------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Función para conexión
# -------------------------
def get_pg_connection():
    return psycopg2.connect(**PG_CONN, cursor_factory=RealDictCursor)

# -------------------------
# Endpoint: Obtener todas las órdenes
# -------------------------
@app.get("/ordenes", response_model=List[dict])
def get_all_ordenes():
    """
    Retorna todas las órdenes con cliente desde la base public.
    (Detalles de productos aún no)
    """
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        # Traemos órdenes + info del cliente
        cur.execute("""
            SELECT o.orden_id, o.fecha, o.canal, o.moneda, o.total,
                   c.cliente_id, c.nombre AS cliente_nombre, c.email
            FROM public.orden o
            JOIN public.cliente c ON o.cliente_id = c.cliente_id
            ORDER BY o.fecha DESC
        """)
        ordenes = cur.fetchall()

        # Retornamos directamente la lista de órdenes (sin detalles por ahora)
        return ordenes

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

# -------------------------
# Punto de entrada
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_ordenes_pg:app", host="127.0.0.1", port=8000, reload=True)
