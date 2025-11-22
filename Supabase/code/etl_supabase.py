# etl_supabase_to_dw.py
import pandas as pd
import psycopg2
import pyodbc
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# -------------------------
# CONFIG (usa las credenciales que ya diste)
# -------------------------
PG_CONN = {
    "host": "aws-1-us-east-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.yxlassfnrleqgcremckw",
    "password": "ZR1bpaNMMy7katsx"
}

MSSQL_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost,1433;"
    "Database=DW_Proyecto_Sales;"
    "Trusted_Connection=yes;"
)

# fallback si no hay tabla de tipo de cambio
# Nota: aquí FALLBACK_CRC_PER_USD representa CRC por 1 USD (ej. 500 CRC/USD).
FALLBACK_CRC_PER_USD = 500.0
DEFAULT_CRC_TO_USD = 1.0 / FALLBACK_CRC_PER_USD  # solo por si se usa en algun otro sitio

# -------------------------
# CONEXIONES
# -------------------------
def get_pg_connection():
    return psycopg2.connect(
        host=PG_CONN["host"],
        port=PG_CONN["port"],
        dbname=PG_CONN["database"],
        user=PG_CONN["user"],
        password=PG_CONN["password"]
    )

def get_mssql_connection():
    return pyodbc.connect(MSSQL_CONN_STR)

# -------------------------
# UTIL: normalizar genero
# -------------------------
def normalizar_genero(g):
    if pd.isna(g):
        return "No especificado"
    s = str(g).strip().lower()
    if s in ("m", "masculino"):
        return "Masculino"
    if s in ("f", "femenino"):
        return "Femenino"
    return "No especificado"

# -------------------------
# UTIL: obtener tipo de cambio desde DW (por fecha) con cache
# devuelve CRC por 1 USD (ej. 500.0) si lo encuentra
# -------------------------
def get_tipo_cambio_for_date(mcur, fecha_date, cache):
    # si no hay fecha, devolvemos None para indicar que no hay tipo por fecha
    if fecha_date is None:
        return None

    key = fecha_date.isoformat()
    if key in cache:
        return cache[key]

    # Try table TipoCambio (asumimos que columna 'tasa' es CRC por USD)
    try:
        mcur.execute("SELECT TOP 1 tasa FROM TipoCambio WHERE fecha = ?", (fecha_date,))
        row = mcur.fetchone()
        if row and row[0] is not None:
            cache[key] = float(row[0])
            return cache[key]
    except Exception:
        pass

    # Try DIM_Tiempo (asumimos 'tipoCambio' es CRC por USD)
    try:
        mcur.execute("SELECT TOP 1 tipoCambio FROM DIM_Tiempo WHERE fecha = ?", (fecha_date,))
        row = mcur.fetchone()
        if row and row[0] is not None:
            cache[key] = float(row[0])
            return cache[key]
    except Exception:
        pass

    # No hay tipo de cambio para esa fecha: dejar como None (se usará fallback)
    cache[key] = None
    return cache[key]

# -------------------------
# Upsert helpers (mantengo igual lógica, solo get_or_create_cliente acepta fecha_registro)
# -------------------------
def get_or_create_cliente(mcur, cache_cliente, nombre, email, genero, pais, fecha_registro):
    email = (email or "").strip()
    if email == "":
        email = f"no-email-{uuid.uuid4().hex[:8]}@local"

    if email in cache_cliente:
        return cache_cliente[email]

    mcur.execute("SELECT idCliente FROM DIM_Cliente WHERE email = ?", (email,))
    res = mcur.fetchone()
    if res:
        cache_cliente[email] = int(res[0])
        return cache_cliente[email]

    fecha_registro_val = fecha_registro
    if pd.isna(fecha_registro_val):
        fecha_registro_val = datetime.now().date()

    mcur.execute(
        "INSERT INTO DIM_Cliente (nombre, email, genero, pais, fechaRegistro) "
        "OUTPUT INSERTED.idCliente VALUES (?, ?, ?, ?, ?)",
        (nombre or "", email, genero or "No especificado", pais or "", fecha_registro_val)
    )

    try:
        newid = mcur.fetchval()
    except:
        mcur.execute("SELECT SCOPE_IDENTITY()")
        newid = mcur.fetchone()[0]

    cache_cliente[email] = int(newid)
    return cache_cliente[email]

def get_or_create_producto(mcur, cache_producto, sku, nombre, categoria):
    sku_val = (sku or "").strip()
    if sku_val == "":
        sku_val = f"NO-SKU-{uuid.uuid4().hex[:8]}"

    if sku_val in cache_producto:
        return cache_producto[sku_val], sku_val

    mcur.execute("SELECT idProducto FROM DIM_Producto WHERE sku = ?", (sku_val,))
    res = mcur.fetchone()
    if res:
        cache_producto[sku_val] = int(res[0])
        return cache_producto[sku_val], sku_val

    mcur.execute(
        "INSERT INTO DIM_Producto (sku, nombre, categoria) OUTPUT INSERTED.idProducto VALUES (?, ?, ?)",
        (sku_val, nombre or "", categoria or "")
    )

    try:
        newid = mcur.fetchval()
    except:
        mcur.execute("SELECT SCOPE_IDENTITY()")
        newid = mcur.fetchone()[0]

    cache_producto[sku_val] = int(newid)
    return cache_producto[sku_val], sku_val

def get_or_create_canal(mcur, cache_canal, canal):
    canal_key = (canal or "UNKNOWN")

    if canal_key in cache_canal:
        return cache_canal[canal_key]

    mcur.execute("SELECT idCanal FROM DIM_Canal WHERE canal = ?", (canal_key,))
    res = mcur.fetchone()
    if res:
        cache_canal[canal_key] = int(res[0])
        return cache_canal[canal_key]

    mcur.execute("INSERT INTO DIM_Canal (canal) OUTPUT INSERTED.idCanal VALUES (?)", (canal_key,))
    try:
        newid = mcur.fetchval()
    except:
        mcur.execute("SELECT SCOPE_IDENTITY()")
        newid = mcur.fetchone()[0]

    cache_canal[canal_key] = int(newid)
    return cache_canal[canal_key]

def get_or_create_tiempo(mcur, cache_tiempo, fecha_date, tipo_cache):
    key = fecha_date.isoformat()
    if key in cache_tiempo:
        return cache_tiempo[key]

    mcur.execute("SELECT idTiempo, tipoCambio FROM DIM_Tiempo WHERE fecha = ?", (fecha_date,))
    row = mcur.fetchone()
    if row:
        cache_tiempo[key] = (int(row[0]), float(row[1]))
        return cache_tiempo[key]

    anio = fecha_date.year
    mes = fecha_date.month
    dia = fecha_date.day
    trimestre = (mes - 1) // 3 + 1
    numeroMes = mes

    tipoCambio = get_tipo_cambio_for_date(mcur, fecha_date, tipo_cache)
    # si no hay tipoCambio encontrado usamos fallback
    if not tipoCambio:
        tipoCambio = FALLBACK_CRC_PER_USD

    mcur.execute(
        "INSERT INTO DIM_Tiempo (fecha, anio, mes, dia, trimestre, numeroMes, tipoCambio) "
        "OUTPUT INSERTED.idTiempo VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fecha_date, anio, mes, dia, trimestre, numeroMes, tipoCambio)
    )

    try:
        newid = mcur.fetchval()
    except:
        mcur.execute("SELECT SCOPE_IDENTITY()")
        newid = mcur.fetchone()[0]

    cache_tiempo[key] = (int(newid), float(tipoCambio))
    return cache_tiempo[key]

# -------------------------
# ETL principal
# -------------------------
def run_etl():
    print("Conectando a Supabase (Postgres)...")
    pg_conn = get_pg_connection()

    print("Conectando a SQL Server (DW)...")
    mssql_conn = get_mssql_connection()
    mssql_conn.autocommit = False
    mcur = mssql_conn.cursor()

    print("Extrayendo datos desde Supabase...")
    clientes = pd.read_sql(
        "SELECT cliente_id, nombre, email, genero, pais, fecha_registro FROM public.cliente",
        pg_conn
    )
    productos = pd.read_sql(
        "SELECT producto_id, sku, nombre, categoria FROM public.producto",
        pg_conn
    )
    ordenes = pd.read_sql(
        "SELECT orden_id, cliente_id, fecha, canal, moneda, total FROM public.orden",
        pg_conn
    )
    detalles = pd.read_sql(
        "SELECT orden_detalle_id, orden_id, producto_id, cantidad, precio_unit FROM public.orden_detalle",
        pg_conn
    )

    print(f"Registros: clientes={len(clientes)}, productos={len(productos)}, ordenes={len(ordenes)}, detalles={len(detalles)}")

    # Transformaciones
    clientes["genero_norm"] = clientes["genero"].apply(normalizar_genero)
    clientes["email"] = clientes["email"].fillna("").astype(str)
    clientes["fecha_registro"] = pd.to_datetime(clientes["fecha_registro"], errors="coerce")

    productos["sku_filled"] = productos["sku"].fillna("").astype(str)
    mask_no_sku = productos["sku_filled"].str.strip() == ""
    productos.loc[mask_no_sku, "sku_filled"] = productos.loc[mask_no_sku, "producto_id"].apply(lambda v: f"NO-SKU-{str(v)[:8]}")

    ordenes["fecha"] = pd.to_datetime(ordenes["fecha"], errors="coerce")

    fact = detalles.merge(ordenes, on="orden_id", how="left", suffixes=("_det", "_ord"))
    fact = fact.merge(productos[["producto_id", "sku_filled", "nombre", "categoria"]], on="producto_id", how="left")
    fact = fact.merge(clientes[["cliente_id", "email", "nombre", "fecha_registro"]], on="cliente_id", how="left")

    fact["precio_unit"] = pd.to_numeric(fact["precio_unit"], errors="coerce").fillna(0.0)
    fact["cantidad"] = pd.to_numeric(fact["cantidad"], errors="coerce").fillna(0).astype(int)
    fact["totalVenta_local"] = (fact["precio_unit"] * fact["cantidad"]).round(2)

    # Ahora calculamos por fila: precio_unit_usd, totalVenta_usd y totalCRC
    # Usamos el tipo de cambio por fecha (si está) o fallback
    tipo_cache = {}
    def compute_currency_row(row):
        moneda = str(row.get("moneda") or "USD").upper()
        fecha = row.get("fecha")
        fecha_date = None
        if not pd.isna(fecha):
            try:
                fecha_date = fecha.date()
            except Exception:
                fecha_date = None

        tipoCambio = get_tipo_cambio_for_date(mcur, fecha_date, tipo_cache) if fecha_date else None
        if not tipoCambio or tipoCambio == 0:
            tipoCambio = FALLBACK_CRC_PER_USD  # CRC per 1 USD

        # Si la orden viene en USD, totalVenta_local está en USD
        if moneda == "USD":
            precio_unit_usd = float(row["precio_unit"])
            totalVenta_usd = float(row["totalVenta_local"])
            totalCRC = round(totalVenta_usd * tipoCambio, 2)
        else:
            # Si la orden viene en CRC, asumimos totalVenta_local está en CRC
            # Convertimos a USD: totalVenta_usd = totalCRC / tipoCambio
            totalCRC = round(float(row["totalVenta_local"]), 2)
            # evitar division por cero (ya controlado por tipoCambio)
            precio_unit_usd = float(row["precio_unit"]) / tipoCambio
            totalVenta_usd = float(row["totalVenta_local"]) / tipoCambio

        return pd.Series({
            "precio_unit_usd": round(precio_unit_usd, 2),
            "totalVenta_usd": round(totalVenta_usd, 2),
            "totalCRC": totalCRC,
            "tipoCambio_used": tipoCambio
        })

    # Aplicar el cálculo en todo el dataframe
    cur_df = fact.apply(compute_currency_row, axis=1)
    fact = pd.concat([fact, cur_df], axis=1)

    # Caches de dimensiones
    cache_cliente = {}
    cache_producto = {}
    cache_canal = {}
    cache_tiempo = {}

    # -------------------------
    # Cargar dimensiones
    # -------------------------
    print("Upsert dimensiones: Clientes, Productos, Canales...")

    for _, row in clientes.iterrows():
        get_or_create_cliente(
            mcur,
            cache_cliente,
            row.get("nombre"),
            row.get("email"),
            row.get("genero_norm"),
            row.get("pais"),
            row.get("fecha_registro")
        )
    mssql_conn.commit()
    print(f"DimClientes confirmados: {len(cache_cliente)}")

    for _, row in productos.iterrows():
        get_or_create_producto(
            mcur,
            cache_producto,
            row.get("sku_filled"),
            row.get("nombre"),
            row.get("categoria")
        )
    mssql_conn.commit()
    print(f"DimProductos confirmados: {len(cache_producto)}")

    for canal in ordenes["canal"].dropna().unique().tolist():
        get_or_create_canal(mcur, cache_canal, canal)
    mssql_conn.commit()
    print(f"DimCanales confirmados: {len(cache_canal)}")

    # -------------------------
    # Preparar filas para FACT_Ventas
    # -------------------------
    print("Preparando filas para FACT_Ventas...")
    insert_sql = """
        INSERT INTO FACT_Ventas
        (idCliente, idProducto, idTiempo, idCanal, cantidad, precioUnitario, descuentoPct, totalVenta, totalCRC)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        mcur.fast_executemany = True
    except:
        pass

    rows_to_insert = []
    missing_products = 0
    skipped_rows = 0

    for _, r in fact.iterrows():
        email = (r.get("email") or "").strip()
        if email == "":
            email = f"no-email-{uuid.uuid4().hex[:8]}@local"

        idCliente = cache_cliente.get(email)
        if idCliente is None:
            mcur.execute("SELECT idCliente FROM DIM_Cliente WHERE email = ?", (email,))
            res = mcur.fetchone()
            if res:
                idCliente = int(res[0])
                cache_cliente[email] = idCliente
            else:
                skipped_rows += 1
                continue

        sku = r.get("sku_filled")
        idProducto = cache_producto.get(sku)
        if idProducto is None:
            mcur.execute("SELECT idProducto FROM DIM_Producto WHERE sku = ?", (sku,))
            res = mcur.fetchone()
            if res:
                idProducto = int(res[0])
                cache_producto[sku] = idProducto
            else:
                missing_products += 1
                continue

        fecha = r.get("fecha")
        if pd.isna(fecha):
            skipped_rows += 1
            continue

        fecha_date = fecha.date()
        # idTiempo lo creamos/obtenemos usando el tipoCambio que ya usamos antes (pero la función lo volverá a calcular si falta)
        idTiempo, tipoCambio_stored = get_or_create_tiempo(mcur, cache_tiempo, fecha_date, tipo_cache)

        canal = r.get("canal") or "UNKNOWN"
        idCanal = cache_canal.get(canal)
        if idCanal is None:
            idCanal = get_or_create_canal(mcur, cache_canal, canal)

        cantidad = int(r["cantidad"])
        precio_unit_usd = float(r["precio_unit_usd"])
        totalVenta = float(r["totalVenta_usd"])
        descuentoPct = 0.0
        totalCRC = float(r.get("totalCRC") or 0.0)

        rows_to_insert.append(
            (idCliente, idProducto, idTiempo, idCanal,
             cantidad, precio_unit_usd, descuentoPct, totalVenta, totalCRC)
        )

    print(f"Filas a insertar en FACT: {len(rows_to_insert)} (missing_products={missing_products}, skipped={skipped_rows})")

    if rows_to_insert:
        mcur.executemany(insert_sql, rows_to_insert)
        mssql_conn.commit()
        print("FACT_Ventas cargada correctamente.")
    else:
        print("No hay filas para insertar en FACT_Ventas.")

    pg_conn.close()
    mssql_conn.close()
    print("ETL finalizado OK.")

if __name__ == "__main__":
    run_etl()
