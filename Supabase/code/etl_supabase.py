"""
ETL Supabase -> Data Warehouse (SQL Server)
- Extrae: cliente, producto, orden, orden_detalle (desde Postgres / Supabase)
- Transforma: normaliza genero, fechas, moneda (CRC->USD), sku para sin-sku, dim tiempo, dim canal
- Carga: inserta/upserta DIM_Cliente, DIM_Producto, DIM_Tiempo, DIM_Canal y FACT_Ventas
"""

import pandas as pd
import psycopg2
import pyodbc
import uuid
import random
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# -------------------------
# CONFIG (REEMPLAZAR) OJO
# -------------------------
PG_CONN = {
    "host": "YOUR_PG_HOST",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "YOUR_PG_PASSWORD"
}

MSSQL_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=YOUR_SQLSERVER_HOST;"      # ej: "tcp:server.database.windows.net,1433"
    "Database=YOUR_DW_DATABASE;"
    "UID=YOUR_SQLUSER;PWD=YOUR_SQLPWD;"
    # o usar Trusted_Connection=yes en entornos Windows
)

# Default conversion rate fallback (CRC -> USD) if no table present
DEFAULT_CRC_TO_USD = 0.0017  # ejemplo; preferible tener tabla TipoCambio en DW

# -------------------------
# CONEXIONES
# -------------------------
def get_pg_connection():
    return psycopg2.connect(
        host=PG_CONN["host"],
        port=PG_CONN["port"],
        dbname=PG_CONN["dbname"],
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
# UTIL: obtener tipo de cambio desde DW (por fecha)
# -------------------------
def get_tipo_cambio_for_date(sql_cursor, fecha_date):
    """
    Intenta leer table TipoCambio(fecha,de,a,tasa) o DIM_Tiempo.tipoCambio.
    Si no existe, retorna DEFAULT_CRC_TO_USD.
    fecha_date: datetime.date o str YYYY-MM-DD
    """
    try:
        # Intenta tabla TipoCambio
        sql_cursor.execute("SELECT TOP 1 tasa FROM TipoCambio WHERE fecha = ?", fecha_date)
        row = sql_cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        pass

    try:
        # Intenta DIM_Tiempo
        sql_cursor.execute("SELECT TOP 1 tipoCambio FROM DIM_Tiempo WHERE fecha = ?", fecha_date)
        row = sql_cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        pass

    # fallback
    return DEFAULT_CRC_TO_USD

# -------------------------
# Upsert helpers (simple, robust)
# -------------------------
def get_or_create_cliente(sql_cur, nombre, email, genero, pais):
    # buscar por email (único)
    row = sql_cur.execute("SELECT idCliente FROM DIM_Cliente WHERE email = ?", (email,)).fetchone()
    if row:
        return int(row[0])
    # insertar y devolver id
    sql_cur.execute(
        "INSERT INTO DIM_Cliente (nombre, email, genero, pais) OUTPUT INSERTED.idCliente VALUES (?, ?, ?, ?)",
        (nombre, email, genero, pais)
    )
    return int(sql_cur.fetchval()) if hasattr(sql_cur, 'fetchval') else int(sql_cur.fetchone()[0])

def get_or_create_producto(sql_cur, sku, nombre, categoria):
    # SKU NOT NULL en DW, si sku vacío, generamos uno determinista
    if (sku is None) or (str(sku).strip() == ""):
        sku = f"NO-SKU-{uuid.uuid4().hex[:8]}"
    row = sql_cur.execute("SELECT idProducto FROM DIM_Producto WHERE sku = ?", (sku,)).fetchone()
    if row:
        return int(row[0])
    sql_cur.execute(
        "INSERT INTO DIM_Producto (sku, nombre, categoria) OUTPUT INSERTED.idProducto VALUES (?, ?, ?)",
        (sku, nombre, categoria)
    )
    return int(sql_cur.fetchval()) if hasattr(sql_cur, 'fetchval') else int(sql_cur.fetchone()[0])

def get_or_create_canal(sql_cur, canal):
    row = sql_cur.execute("SELECT idCanal FROM DIM_Canal WHERE canal = ?", (canal,)).fetchone()
    if row:
        return int(row[0])
    sql_cur.execute("INSERT INTO DIM_Canal (canal) OUTPUT INSERTED.idCanal VALUES (?)", (canal,))
    return int(sql_cur.fetchval()) if hasattr(sql_cur, 'fetchval') else int(sql_cur.fetchone()[0])

def get_or_create_tiempo(sql_cur, fecha):
    # fecha: datetime.date
    row = sql_cur.execute("SELECT idTiempo, tipoCambio FROM DIM_Tiempo WHERE fecha = ?", (fecha,)).fetchone()
    if row:
        return int(row[0]), float(row[1])
    anio = fecha.year
    mes = fecha.month
    dia = fecha.day
    trimestre = (mes - 1) // 3 + 1
    numeroMes = mes
    tipoCambio = get_tipo_cambio_for_date(sql_cur, fecha)
    sql_cur.execute("""
        INSERT INTO DIM_Tiempo (fecha, anio, mes, dia, trimestre, numeroMes, tipoCambio)
        OUTPUT INSERTED.idTiempo
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (fecha, anio, mes, dia, trimestre, numeroMes, tipoCambio))
    newid = sql_cur.fetchval() if hasattr(sql_cur, 'fetchval') else sql_cur.fetchone()[0]
    return int(newid), float(tipoCambio)

# -------------------------
# FUNCIÓN PRINCIPAL ETL
# -------------------------
def run_etl():
    print("Conectando a Postgres (Supabase)...")
    pg_conn = get_pg_connection()
    print("Conectando a SQL Server (DW)...")
    mssql_conn = get_mssql_connection()
    mssql_conn.autocommit = False
    mcur = mssql_conn.cursor()
    # pyodbc cursor does not have fetchval; we'll use fetchone() patterns.

    # --- EXTRACT: leer tablas desde Supabase ---
    print("Extrayendo tablas desde Supabase (cliente, producto, orden, orden_detalle)...")
    clientes = pd.read_sql("SELECT cliente_id, nombre, email, genero, pais, fecha_registro FROM cliente", pg_conn)
    productos = pd.read_sql("SELECT producto_id, sku, nombre, categoria FROM producto", pg_conn)
    ordenes = pd.read_sql("SELECT orden_id, cliente_id, fecha, canal, moneda, total FROM orden", pg_conn)
    detalles = pd.read_sql("SELECT orden_detalle_id, orden_id, producto_id, cantidad, precio_unit FROM orden_detalle", pg_conn)

    print(f"Registros: clientes={len(clientes)}, productos={len(productos)}, ordenes={len(ordenes)}, detalles={len(detalles)}")

    # --- TRANSFORM ---
    print("Transformando datos...")

    # Normalizar genero en clientes
    clientes["genero_norm"] = clientes["genero"].apply(normalizar_genero)
    # asegurar valores minimos
    clientes["email"] = clientes["email"].fillna("").astype(str)

    # Productos: algunos pueden no tener sku -> generar sku provisional (no modifica la fuente)
    productos["sku_filled"] = productos["sku"].fillna("").astype(str)
    mask_no_sku = productos["sku_filled"].str.strip() == ""
    productos.loc[mask_no_sku, "sku_filled"] = productos.loc[mask_no_sku, "producto_id"].apply(lambda v: f"NO-SKU-{str(v)[:8]}")

    # Formatear fechas de ordenes a datetime.date
    ordenes["fecha"] = pd.to_datetime(ordenes["fecha"], errors="coerce")
    # unir ordenes + detalles
    fact = detalles.merge(ordenes, on="orden_id", how="left", suffixes=("_det", "_ord"))
    # unir con productos y clientes
    fact = fact.merge(productos[["producto_id", "sku_filled", "nombre", "categoria"]], on="producto_id", how="left")
    fact = fact.merge(clientes[["cliente_id", "email", "nombre"]], on="cliente_id", how="left")

    # Calcular totalVenta (en moneda de la orden)
    fact["precio_unit"] = pd.to_numeric(fact["precio_unit"], errors="coerce").fillna(0.0)
    fact["cantidad"] = pd.to_numeric(fact["cantidad"], errors="coerce").fillna(0).astype(int)
    fact["totalVenta_local"] = (fact["precio_unit"] * fact["cantidad"]).round(2)

    # Convertir moneda CRC -> USD (usar tipo de cambio por fecha)
    # Para performance, cachear tipos de cambio consultando DW
    tipo_cache = {}
    def convert_to_usd(row):
        moneda = str(row["moneda"]).upper() if pd.notna(row["moneda"]) else "USD"
        fecha = row["fecha"].date() if pd.notna(row["fecha"]) else None
        if moneda == "USD" or fecha is None:
            return float(row["totalVenta_local"]), 1.0
        # moneda CRC
        key = fecha.isoformat()
        if key in tipo_cache:
            tasa = tipo_cache[key]
        else:
            try:
                # query MSSQL via cursor
                mcur.execute("SELECT TOP 1 tasa FROM TipoCambio WHERE fecha = ?", (fecha,))
                r = mcur.fetchone()
                if r and r[0] is not None:
                    tasa = float(r[0])
                else:
                    tasa = DEFAULT_CRC_TO_USD
            except Exception:
                tasa = DEFAULT_CRC_TO_USD
            tipo_cache[key] = tasa
        # totalVenta_local is in CRC, convert to USD by dividing by tasa if tasa is CRC per USD? 
        # (Assuming 'tasa' is CRC per USD, USD = CRC / tasa)
        try:
            usd = float(row["totalVenta_local"]) / float(tasa)
        except Exception:
            usd = float(row["totalVenta_local"]) * DEFAULT_CRC_TO_USD
        return round(usd, 2), tasa

    # Apply conversion row-wise (could be optimized)
    usd_list = []
    tasa_list = []
    for _, r in fact.iterrows():
        usd_val, tasa = convert_to_usd(r)
        usd_list.append(usd_val)
        tasa_list.append(tasa)
    fact["totalVenta_usd"] = usd_list
    fact["tipoCambio_usd"] = tasa_list
    # precio_unit in USD: convert if CRC
    def price_to_usd(row):
        moneda = str(row["moneda"]).upper() if pd.notna(row["moneda"]) else "USD"
        if moneda == "USD":
            return float(row["precio_unit"])
        # CRC -> USD
        tasa = row["tipoCambio_usd"] if pd.notna(row["tipoCambio_usd"]) else DEFAULT_CRC_TO_USD
        try:
            return round(float(row["precio_unit"]) / float(tasa), 2)
        except Exception:
            return round(float(row["precio_unit"]) * DEFAULT_CRC_TO_USD, 2)
    fact["precio_unit_usd"] = fact.apply(price_to_usd, axis=1)

    # -------------------------
    # LOAD: insertar dimensiones y fact
    # -------------------------
    print("Cargando dimensiones y hechos en SQL Server...")

    # Preparar caches para evitar múltiples selects/inserts
    cache_cliente = {}   # email -> idCliente
    cache_producto = {}  # sku -> idProducto
    cache_canal = {}     # canal -> idCanal
    cache_tiempo = {}    # fecha_iso -> (idTiempo, tipoCambio)

    # Procesar DIM_Cliente (por email)
    for _, row in clientes.iterrows():
        email = str(row["email"]).strip()
        if email == "":
            # construir un email artificial si falta (no ideal, pero DW exige unique)
            email = f"no-email-{row['cliente_id'][:8]}@local"
        if email in cache_cliente:
            continue
        # buscar en DW
        mcur.execute("SELECT idCliente FROM DIM_Cliente WHERE email = ?", (email,))
        res = mcur.fetchone()
        if res:
            cache_cliente[email] = int(res[0])
            continue
        genero = normalizar_genero(row.get("genero"))
        nombre = row.get("nombre") or ""
        pais = row.get("pais") or ""
        # insertar
        mcur.execute("INSERT INTO DIM_Cliente (nombre, email, genero, pais) OUTPUT INSERTED.idCliente VALUES (?, ?, ?, ?)",
                     (nombre, email, genero, pais))
        newid = mcur.fetchval() if hasattr(mcur, 'fetchval') else mcur.fetchone()[0]
        # if fetchval not available, try to get SCOPE_IDENTITY
        if newid is None:
            mcur.execute("SELECT SCOPE_IDENTITY()")
            newid = mcur.fetchone()[0]
        cache_cliente[email] = int(newid)
    mssql_conn.commit()
    print(f"DimClientes cargados/confirmados: {len(cache_cliente)}")

    # Procesar DIM_Producto (por sku_filled)
    for _, row in productos.iterrows():
        sku = row["sku_filled"]
        if sku in cache_producto:
            continue
        mcur.execute("SELECT idProducto FROM DIM_Producto WHERE sku = ?", (sku,))
        res = mcur.fetchone()
        if res:
            cache_producto[sku] = int(res[0])
            continue
        nombre = row.get("nombre") or ""
        categoria = row.get("categoria") or ""
        mcur.execute("INSERT INTO DIM_Producto (sku, nombre, categoria) OUTPUT INSERTED.idProducto VALUES (?, ?, ?)",
                     (sku, nombre, categoria))
        newid = mcur.fetchval() if hasattr(mcur, 'fetchval') else mcur.fetchone()[0]
        if newid is None:
            mcur.execute("SELECT SCOPE_IDENTITY()")
            newid = mcur.fetchone()[0]
        cache_producto[sku] = int(newid)
    mssql_conn.commit()
    print(f"DimProductos cargados/confirmados: {len(cache_producto)}")

    # Procesar DIM_Canal (por orden.canal unique)
    canales_unicos = ordenes["canal"].dropna().unique().tolist()
    for canal in canales_unicos:
        if canal in cache_canal:
            continue
        mcur.execute("SELECT idCanal FROM DIM_Canal WHERE canal = ?", (canal,))
        res = mcur.fetchone()
        if res:
            cache_canal[canal] = int(res[0])
            continue
        mcur.execute("INSERT INTO DIM_Canal (canal) OUTPUT INSERTED.idCanal VALUES (?)", (canal,))
        newid = mcur.fetchval() if hasattr(mcur, 'fetchval') else mcur.fetchone()[0]
        if newid is None:
            mcur.execute("SELECT SCOPE_IDENTITY()")
            newid = mcur.fetchone()[0]
        cache_canal[canal] = int(newid)
    mssql_conn.commit()
    print(f"DimCanales cargados/confirmados: {len(cache_canal)}")

    # Preparar inserción en FACT_Ventas (por fila del fact DataFrame)
    insert_sql = """
        INSERT INTO FACT_Ventas
        (idCliente, idProducto, idTiempo, idCanal, cantidad, precioUnitario, descuentoPct, totalVenta, totalCRC)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # Habilitar fast_executemany si está disponible (pyodbc)
    try:
        mcur.fast_executemany = True
    except Exception:
        pass

    rows_to_insert = []
    missing_products = 0
    for _, r in fact.iterrows():
        # idCliente por email
        email = str(r.get("email") or "").strip()
        if email == "":
            email = f"no-email-{r.get('cliente_id')[:8]}@local"
        idCliente = cache_cliente.get(email)
        # idProducto por sku_filled
        sku = r.get("sku_filled")
        idProducto = cache_producto.get(sku)
        if idProducto is None:
            # si no encontrado, intentar buscar por sku en DB (último recurso)
            mcur.execute("SELECT idProducto FROM DIM_Producto WHERE sku = ?", (sku,))
            res = mcur.fetchone()
            if res:
                idProducto = int(res[0])
                cache_producto[sku] = idProducto
            else:
                missing_products += 1
                continue  # saltar fila si no hay producto válido

        # idTiempo
        fecha = r.get("fecha")
        if pd.isna(fecha):
            continue
        fecha_date = fecha.date()
        if fecha_date.isoformat() in cache_tiempo:
            idTiempo, tipoCambio = cache_tiempo[fecha_date.isoformat()]
        else:
            # create or get
            mcur.execute("SELECT idTiempo, tipoCambio FROM DIM_Tiempo WHERE fecha = ?", (fecha_date,))
            rowt = mcur.fetchone()
            if rowt:
                idTiempo = int(rowt[0]); tipoCambio = float(rowt[1])
            else:
                tipoCambio = get_tipo_cambio_for_date(mcur, fecha_date)
                mcur.execute("INSERT INTO DIM_Tiempo (fecha, anio, mes, dia, trimestre, numeroMes, tipoCambio) OUTPUT INSERTED.idTiempo VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (fecha_date, fecha_date.year, fecha_date.month, fecha_date.day, (fecha_date.month-1)//3+1, fecha_date.month, tipoCambio))
                newid = mcur.fetchval() if hasattr(mcur, 'fetchval') else mcur.fetchone()[0]
                if newid is None:
                    mcur.execute("SELECT SCOPE_IDENTITY()")
                    newid = mcur.fetchone()[0]
                idTiempo = int(newid)
            cache_tiempo[fecha_date.isoformat()] = (idTiempo, tipoCambio)

        idCanal = cache_canal.get(r.get("canal"))
        if idCanal is None:
            # fallback
            idCanal = get_or_create_canal(mcur, r.get("canal") or "UNKNOWN")
            cache_canal[r.get("canal")] = idCanal

        cantidad = int(r["cantidad"])
        precio_unit_usd = float(r["precio_unit_usd"])
        descuentoPct = 0.0
        totalVenta = round(float(r["totalVenta_usd"]), 2)
        tipoCambio = cache_tiempo[fecha_date.isoformat()][1]
        totalCRC = round(totalVenta * tipoCambio, 2)

        rows_to_insert.append((idCliente, idProducto, idTiempo, idCanal, cantidad, precio_unit_usd, descuentoPct, totalVenta, totalCRC))

    # Bulk insert
    print(f"Inserting {len(rows_to_insert)} fact rows (skipped {missing_products} rows missing product mapping)...")
    if rows_to_insert:
        mcur.executemany(insert_sql, rows_to_insert)
        mssql_conn.commit()
    print("FACT cargada correctamente.")

    # Cierre conexiones
    pg_conn.close()
    mssql_conn.close()
    print("ETL finalizado OK.")

if __name__ == "__main__":
    run_etl()
