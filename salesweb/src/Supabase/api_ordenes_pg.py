# api_ordenes_pg.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
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

# ====================================================
# ENDPOINT: ELIMINAR ORDEN + DETALLES
# ====================================================
@app.delete("/ordenes/{orden_id}")
def eliminar_orden(orden_id: str):
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        # 1) Verificar si existe la orden
        cur.execute("SELECT orden_id FROM public.orden WHERE orden_id = %s", (orden_id,))
        existe = cur.fetchone()

        if not existe:
            raise HTTPException(status_code=404, detail="La orden no existe")

        # 2) Borrar detalles primero
        cur.execute("""
            DELETE FROM public.orden_detalle
            WHERE orden_id = %s;
        """, (orden_id,))

        # 3) Borrar la orden
        cur.execute("""
            DELETE FROM public.orden
            WHERE orden_id = %s;
        """, (orden_id,))

        conn.commit()

        return {
            "status": "success",
            "orden_id": orden_id,
            "mensaje": "Orden y detalles eliminados correctamente."
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

# ====================================================
# ENDPOINT: OBTENER DETALLES DE UNA ORDEN
# ====================================================
@app.get("/ordenes/{orden_id}", response_model=dict)
def get_orden_con_detalles(orden_id: str):
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        # 1) Datos generales de la orden + cliente
        cur.execute("""
            SELECT o.orden_id, o.fecha, o.canal, o.moneda, o.total,
                    c.cliente_id, c.nombre AS cliente_nombre
            FROM public.orden o
            JOIN public.cliente c ON o.cliente_id = c.cliente_id
            WHERE o.orden_id = %s;
        """, (orden_id,))
        orden = cur.fetchone()

        if not orden:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # 2) Detalles de la orden (YA INCLUYE producto_id)
        cur.execute("""
            SELECT d.orden_detalle_id,
                    d.producto_id,
                    p.nombre AS producto_nombre,
                    d.cantidad,
                    d.precio_unit
            FROM public.orden_detalle d
            JOIN public.producto p ON d.producto_id = p.producto_id
            WHERE d.orden_id = %s;
        """, (orden_id,))
        detalles = cur.fetchall()

        return {
            "orden": orden,
            "detalles": detalles
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

# ====================================================
# ENDPOINT: ACTUALIZAR ORDEN + DETALLES
# ====================================================
@app.put("/ordenes/{orden_id}")
def actualizar_orden(orden_id: str, data: OrdenCreate):
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        # 1) Validar que exista la orden
        cur.execute("SELECT orden_id FROM public.orden WHERE orden_id = %s", (orden_id,))
        existe = cur.fetchone()

        if not existe:
            raise HTTPException(status_code=404, detail="La orden no existe")

        # 2) Actualizar datos generales
        cur.execute("""
            UPDATE public.orden
            SET cliente_id = %s,
                canal = %s,
                moneda = %s,
                total = %s
            WHERE orden_id = %s;
        """, (
            data.cliente_id,
            data.canal,
            data.moneda,
            data.total,
            orden_id
        ))

        # 3) Borrar detalles anteriores
        cur.execute("""
            DELETE FROM public.orden_detalle
            WHERE orden_id = %s;
        """, (orden_id,))

        # 4) Insertar nuevos detalles
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

        conn.commit()

        return {
            "status": "success",
            "orden_id": orden_id,
            "mensaje": "Orden actualizada correctamente."
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

# ====================================================
# ENDPOINT: EJECUTAR ETL SUPABASE -> DW
# ====================================================
import subprocess

@app.post("/ejecutar-etl")
def ejecutar_etl():
    """
    Ejecuta el ETL que extrae datos de Supabase y los carga al Data Warehouse.
    """
    try:
        # Ejecutar el script Python como proceso externo
        result = subprocess.run(
            ["python", "Supabase\code\etl_supabase.py"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "mensaje": "El ETL falló",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        return {
            "status": "success",
            "mensaje": "ETL ejecutado correctamente",
            "stdout": result.stdout
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================
# ENDPOINT: OBTENER RECOMENDACIONES APRIORI
# ====================================================
@app.get("/recomendaciones/{producto_id}")
def get_recomendaciones(producto_id: str):
    """
    Obtiene recomendaciones de productos basadas en reglas Apriori
    """
    conn = get_pg_connection()
    cur = conn.cursor()

    try:
        # 1) Buscar reglas donde el producto esté en antecedentes y fuente sea supabase
        cur.execute("""
            SELECT antecedents, consequents, support, confidence, lift
            FROM public.reglas_apriori 
            WHERE %s = ANY(antecedents) 
            AND fuente = 'supabase'
            ORDER BY confidence DESC
            LIMIT 10;
        """, (producto_id,))

        reglas = cur.fetchall()

        if not reglas:
            return {
                "producto_id": producto_id,
                "recomendaciones": []
            }

        # 2) Extraer todos los IDs de productos recomendados
        productos_recomendados_ids = []
        productos_vistos = set()
        
        for regla in reglas:
            producto_recomendado_id = regla['consequents'][0] if regla['consequents'] else None
            if producto_recomendado_id and producto_recomendado_id not in productos_vistos:
                productos_vistos.add(producto_recomendado_id)
                productos_recomendados_ids.append(producto_recomendado_id)

        # 3) Obtener nombres de los productos recomendados - CORREGIDO CON CAST
        if productos_recomendados_ids:
            # Convertir lista de strings a array de UUIDs para PostgreSQL
            cur.execute("""
                SELECT producto_id, nombre 
                FROM public.producto 
                WHERE producto_id = ANY(%s::uuid[]);
            """, (productos_recomendados_ids,))
            
            productos_recomendados = cur.fetchall()
            productos_map = {str(prod['producto_id']): prod['nombre'] for prod in productos_recomendados}
        else:
            productos_map = {}

        # 4) Obtener nombre del producto original - CORREGIDO
        cur.execute("SELECT nombre FROM public.producto WHERE producto_id = %s::uuid", (producto_id,))
        producto_original = cur.fetchone()

        # 5) Construir respuesta
        recomendaciones = []
        for regla in reglas:
            producto_recomendado_id = regla['consequents'][0] if regla['consequents'] else None
            if producto_recomendado_id:
                recomendaciones.append({
                    "producto_id": producto_recomendado_id,
                    "nombre": productos_map.get(producto_recomendado_id, "Producto no encontrado"),
                    "confidence": round(regla['confidence'] * 100),
                    "lift": round(regla['lift'] * 100) / 100,
                    "support": round(regla['support'] * 1000) / 10
                })

        return {
            "producto_id": producto_id,
            "producto_nombre": producto_original['nombre'] if producto_original else "Producto no encontrado",
            "recomendaciones": recomendaciones
        }

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
