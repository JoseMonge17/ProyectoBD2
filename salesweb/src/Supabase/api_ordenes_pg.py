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

# ====================================================
# ENDPOINT: LISTAR CLIENTES
# ====================================================
@app.get("/clientes", response_model=List[dict])
def get_clientes():
    conn = get_pg_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT cliente_id, nombre, email, genero, pais, fecha_registro
            FROM public.cliente
            ORDER BY fecha_registro DESC;
        """)
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ====================================================
# ENDPOINT: LISTAR PRODUCTOS
# ====================================================
@app.get("/productos", response_model=List[dict])
def get_productos():
    conn = get_pg_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT producto_id, sku, nombre, categoria
            FROM public.producto
            ORDER BY nombre ASC;
        """)
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ====================================================
# ENDPOINT: CREAR ORDEN CON DETALLES
# ====================================================
from pydantic import BaseModel
from typing import List

class DetalleItem(BaseModel):
    producto_id: str
    cantidad: int
    precio_unit: float

class OrdenCreate(BaseModel):
    cliente_id: str
    canal: str
    moneda: str
    total: float
    detalles: List[DetalleItem]

@app.post("/ordenes")
def crear_orden(data: OrdenCreate):
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        # 1) Insertar orden
        cur.execute("""
            INSERT INTO public.orden (cliente_id, canal, moneda, total)
            VALUES (%s, %s, %s, %s)
            RETURNING orden_id;
        """, (
            data.cliente_id,
            data.canal,
            data.moneda,
            data.total
        ))

        orden_id = cur.fetchone()["orden_id"]

        # 2) Insertar detalle(s)
        for item in data.detalles:
            cur.execute("""
                INSERT INTO public.orden_detalle (orden_id, producto_id, cantidad, precio_unit)
                VALUES (%s, %s, %s, %s);
            """, (
                orden_id,
                item.producto_id,
                item.cantidad,
                item.precio_unit
            ))

        # Confirmar todo
        conn.commit()

        return {
            "status": "success",
            "orden_id": orden_id,
            "mensaje": "Orden creada correctamente."
        }

    except Exception as e:
        conn.rollback()
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
