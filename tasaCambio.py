import pandas as pd
import pycurl
from io import BytesIO
import json
import sqlalchemy as db
import datetime

# Datos de conexión con SQLAlchemy (local)
CONNECTION_STRING_DB = "mssql+pyodbc://localhost/DW_Proyecto_Sales?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
engine = db.create_engine(CONNECTION_STRING_DB)
connection = engine.connect()
metadata = db.MetaData()

# URL base del BCCR
BASE_URL = "https://apim.bccr.fi.cr/SDDE/api/Bccr.Ge.SDDE.Publico.Indicadores.API/"

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJCQ0NSLVNEREUiLCJzdWIiOiJqLm1vbmdlLjZAZXN0dWRpYW50ZWMuY3IiLCJhdWQiOiJTRERFLVNpdGlvRXh0ZXJubyIsImV4cCI6MjUzNDAyMzAwODAwLCJuYmYiOjE3NjI3OTc4MzYsImlhdCI6MTc2Mjc5NzgzNiwianRpIjoiMWMyN2QzNDYtY2Q2MS00OGMzLWFhZTEtN2YxOWVkOTkwZDhjIiwiZW1haWwiOiJqLm1vbmdlLjZAZXN0dWRpYW50ZWMuY3IifQ.Axe0mv5yGGaFzFXVVSxAtaopWEzQr9EsVV3TxEY3Fc8"

# Función para crear la URL y los encabezados para la consulta
def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

# Función para obtener los datos del tipo de cambio del BCCR usando pycurl
def fetch_bccr(fecha_ini, fecha_fin):
    # Convertir las fechas a formato 'yyyy/mm/dd'
    fecha_ini_str = fecha_ini.strftime("%Y/%m/%d")
    fecha_fin_str = fecha_fin.strftime("%Y/%m/%d")
    
    # Construir la URL para la consulta
    url = f'{BASE_URL}cuadro/1/series?fechaInicio={fecha_ini_str}&fechaFin={fecha_fin_str}&idioma=ES'

    # Crear un buffer para capturar la respuesta
    buffer = BytesIO()

    # Crear el objeto cURL
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + TOKEN])
    c.setopt(c.WRITEFUNCTION, buffer.write)

    # Ejecutar la solicitud
    c.perform()

    # Obtener el código de respuesta
    response_code = c.getinfo(c.RESPONSE_CODE)

    # Verificar si la solicitud fue exitosa
    if response_code == 200:
        print("Datos obtenidos correctamente")
        # Leer la respuesta JSON desde el buffer
        response_data = buffer.getvalue().decode('utf-8')
        data = json.loads(response_data)  # Convertir JSON en diccionario de Python
        
        # Cerrar el objeto cURL
        c.close()
        if data["estado"]:
                # Filtrar solo los datos del tipo de cambio de venta (codigoIndicador: 318)
                venta_data = []
                for item in data["datos"]:
                    for indicador in item["indicadores"]:
                        if indicador["codigoIndicador"] == "318":  # Tipo cambio venta
                            for serie in indicador["series"]:
                                fecha = serie["fecha"]
                                valor = serie["valorDatoPorPeriodo"]
                                venta_data.append((fecha, valor))
                return venta_data
        else:
            print("No se encontraron datos.")
            return []
    else:
        print(f"Error {response_code}: {buffer.getvalue().decode('utf-8')}")
        c.close()
        return []


# Función para verificar si el dato ya existe en la base de datos
def check_if_exists(fecha, tipo_cambio):
    query = """
        SELECT COUNT(*) 
        FROM DIM_Tiempo 
        WHERE fecha = :fecha AND tipoCambio = :tipoCambio
    """
    result = connection.execute(db.text(query), {'fecha': fecha, 'tipoCambio': tipo_cambio})
    return result.scalar() > 0  # Devuelve True si el registro existe, False si no

# Función para actualizar el tipo de cambio en la base de datos
def update_tipo_cambio(fecha, tipo_cambio):
    update_query = """
        UPDATE DIM_Tiempo
        SET tipoCambio = :tipoCambio
        WHERE fecha = :fecha
    """
    connection.execute(db.text(update_query), {'fecha': fecha, 'tipoCambio': tipo_cambio})

# Función para insertar los tipos de cambio de venta en la tabla DIM_Tiempo usando Pandas
def insert_or_update_tipo_cambio(tipo_cambio):
    inserted_count = 0  # Contador de inserciones
    updated_count = 0   # Contador de actualizaciones
    # Convertir los datos a un DataFrame de pandas
    df = pd.DataFrame(tipo_cambio, columns=["fecha", "tipoCambio"])

    # Convertir la fecha a formato datetime
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

    # Agregar las columnas adicionales que necesitamos
    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['dia'] = df['fecha'].dt.day
    df['trimestre'] = df['fecha'].dt.quarter
    df['numeroMes'] = df['fecha'].dt.month

    # Verificar si los registros ya existen y realizar insert o update
    for index, row in df.iterrows():
        if check_if_exists(row['fecha'], row['tipoCambio']):
            # Si existe, actualizamos el tipo de cambio
            update_tipo_cambio(row['fecha'], row['tipoCambio'])
            
            updated_count += 1  # Incrementar el contador de actualizaciones
        else:
            # Si no existe, insertamos el nuevo tipo de cambio
            try:
                insert_query = """
                    INSERT INTO DIM_Tiempo (fecha, anio, mes, dia, trimestre, numeroMes, tipoCambio)
                    VALUES (:fecha, YEAR(:fecha), MONTH(:fecha), DAY(:fecha), DATEPART(QUARTER, :fecha), MONTH(:fecha), :tipoCambio)
                """
                connection.execute(db.text(insert_query), {
                    'fecha': row['fecha'], 
                    'tipoCambio': row['tipoCambio']
                })
                inserted_count += 1  # Incrementar el contador de inserciones
            except Exception as e:
                print(f"Error al insertar datos en la base de datos: {e}")
    connection.commit()
    return inserted_count, updated_count

# Función principal
if __name__ == "__main__":
    today = datetime.date.today()
    start = today - datetime.timedelta(days=365*3)
    tipo_cambio = fetch_bccr(start, today)
    if tipo_cambio:
        inserted_count, updated_count  = insert_or_update_tipo_cambio(tipo_cambio)
        print(f"Se insertaron {inserted_count} registros y se actualizaron {updated_count} registros en la base de datos.")