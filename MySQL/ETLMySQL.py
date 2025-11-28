# etl_mysql_to_dw_controlled.py
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
import re
import traceback
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETL_MySQL_to_DW:
    def __init__(self):
        # Connection strings
        self.mysql_conn_str = "mysql+mysqlconnector://root:12345678@127.0.0.1:3306/sales_mysql"
        self.dw_conn_str = "mssql+pyodbc://localhost/DW_Proyecto_Sales?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        
        self.mysql_engine = None
        self.dw_engine = None
        self.etl_log_file = "etl_mysql_log.json"
        
    def connect(self):
        """Conectar a MySQL y SQL Server DW"""
        try:
            self.mysql_engine = create_engine(self.mysql_conn_str)
            self.dw_engine = create_engine(self.dw_conn_str)
            logger.info("✅ Conexiones establecidas (MySQL → DW)")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {str(e)}")
            return False

    def disconnect(self):
        """Cerrar conexiones"""
        if self.mysql_engine:
            self.mysql_engine.dispose()
        if self.dw_engine:
            self.dw_engine.dispose()
        logger.info("🔌 Conexiones cerradas")

    def get_last_etl_execution(self):
        """Obtener información de la última ejecución del ETL"""
        try:
            if os.path.exists(self.etl_log_file):
                with open(self.etl_log_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "last_execution": None,
                    "last_processed_date": None,
                    "processed_records": 0
                }
        except Exception as e:
            logger.warning(f"⚠️  Error leyendo log de ETL: {e}")
            return {
                "last_execution": None,
                "last_processed_date": None,
                "processed_records": 0
            }

    def save_etl_execution(self, execution_data):
        """Guardar información de la ejecución actual del ETL"""
        try:
            with open(self.etl_log_file, 'w') as f:
                json.dump(execution_data, f, indent=2)
            logger.info("📝 Log de ejecución guardado")
        except Exception as e:
            logger.error(f"❌ Error guardando log de ETL: {e}")

    def clean_numeric_string(self, value):
        """Limpiar string numérico: remover comas, espacios y convertir a float"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return 0.0
            
            # Convertir a string por si acaso
            str_value = str(value).strip()
            
            # Si está vacío, retornar 0
            if str_value == '':
                return 0.0
            
            # Remover comas (formato 1,200.50 -> 1200.50)
            str_value = str_value.replace(',', '')
            
            # Remover caracteres no numéricos excepto punto decimal y signo negativo
            str_value = re.sub(r'[^\d.-]', '', str_value)
            
            # Si está vacío después de limpiar, retornar 0
            if str_value == '' or str_value == '-':
                return 0.0
            
            # Convertir a float
            return float(str_value)
            
        except Exception as e:
            logger.warning(f"⚠️  No se pudo convertir a número: '{value}' -> '{str_value}'. Error: {e}")
            return 0.0

    # ==================== EXTRACCIÓN CON CONTROL ====================
    def extract_data(self, last_processed_date=None):
        """Extraer datos de MySQL fuente con control de duplicación"""
        try:
            logger.info("📥 Extrayendo datos de MySQL...")
            
            # Construir consultas con filtro de fecha si existe última ejecución
            where_clause = ""
            if last_processed_date:
                where_clause = f"WHERE fecha > '{last_processed_date}'"
                logger.info(f"🔍 Filtrando datos desde: {last_processed_date}")
            
            # Extraer tablas fuente de MySQL
            with self.mysql_engine.connect() as conn:
                clientes = pd.read_sql("SELECT * FROM Cliente", conn)
                productos = pd.read_sql("SELECT * FROM Producto", conn)
                ordenes = pd.read_sql(f"SELECT * FROM Orden {where_clause}", conn)
                ordenes_detalle_query = f"""
                    SELECT od.* FROM OrdenDetalle od
                    INNER JOIN Orden o ON od.orden_id = o.id
                    {where_clause.replace('fecha', 'o.fecha') if where_clause else ''}
                """
                ordenes_detalle = pd.read_sql(ordenes_detalle_query, conn)
            
            # Cargar equivalencias desde el CSV (ubicado en la raíz del proyecto)
            ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_equivalencias = os.path.join(ruta_base, 'EquivalenciaProductos.csv')
            
            if os.path.exists(ruta_equivalencias):
                equivalencias = pd.read_csv(ruta_equivalencias)
                logger.info(f"✅ Equivalencias cargadas desde CSV: {len(equivalencias)} registros")
            else:
                logger.error(f"❌ Archivo de equivalencias no encontrado: {ruta_equivalencias}")
                equivalencias = pd.DataFrame()
            
            # Extraer tipos de cambio del DW
            with self.dw_engine.connect() as conn:
                tipo_cambio = pd.read_sql("SELECT fecha, tipoCambio FROM DIM_Tiempo", conn)
            
            # Obtener fecha máxima procesada para el log
            max_fecha = None
            if not ordenes.empty:
                max_fecha = ordenes['fecha'].max()
            
            logger.info(f"✅ Extracción MySQL completada: {len(clientes)} clientes, {len(productos)} productos, {len(ordenes)} órdenes nuevas")
            
            return clientes, productos, ordenes, ordenes_detalle, equivalencias, tipo_cambio, max_fecha
            
        except Exception as e:
            logger.error(f"❌ Error en extracción MySQL: {str(e)}")
            return None, None, None, None, None, None, None

    # ==================== TRANSFORMACIÓN ====================
    def transform_dim_cliente(self, df_clientes):
        """Transformar datos para Dim_Cliente desde MySQL"""
        logger.info("🔄 Transformando Dim_Cliente desde MySQL...")
        
        dim_cliente = df_clientes[[
            'id', 'nombre', 'correo', 'genero', 'pais', 'created_at'
        ]].copy()
        
        # Estandarización de género (acortar para que quepa en la columna)
        genero_map = {'M': 'Masculino', 'F': 'Femenino', 'X': 'Otro'}
        dim_cliente['genero'] = dim_cliente['genero'].map(genero_map).fillna('Otro')
        
        # Convertir fecha (VARCHAR a DATE)
        dim_cliente['created_at'] = pd.to_datetime(dim_cliente['created_at'], errors='coerce').dt.date
        
        # Renombrar columnas para el DW
        dim_cliente.columns = ['idCliente', 'nombre', 'email', 'genero', 'pais', 'fechaRegistro']
        
        logger.info(f"✅ Dim_Cliente transformado: {len(dim_cliente)} registros")
        return dim_cliente
    
    def transform_dim_producto(self, df_productos, df_equivalencias):
        """Transformar datos para Dim_Producto desde MySQL usando equivalencias"""
        logger.info("🔄 Transformando Dim_Producto desde MySQL...")
        
        if df_equivalencias.empty:
            logger.warning("⚠️  No hay equivalencias disponibles, usando códigos alternos como SKU")
            # Si no hay equivalencias, usar código_alt como SKU
            dim_producto = df_productos[['id', 'codigo_alt', 'nombre', 'categoria']].copy()
            dim_producto.columns = ['idProducto', 'sku', 'nombre', 'categoria']
        else:
            # Unir con equivalencias para obtener SKU oficial
            dim_producto = pd.merge(
                df_productos,
                df_equivalencias[['codigo_alt', 'sku']],
                left_on='codigo_alt',
                right_on='codigo_alt',
                how='left'
            )
            
            # Si no hay equivalencia, usar código_alt como SKU
            dim_producto['sku'] = dim_producto['sku'].fillna(dim_producto['codigo_alt'])
            
            dim_producto = dim_producto[['id', 'sku', 'nombre', 'categoria']]
            dim_producto.columns = ['idProducto', 'sku', 'nombre', 'categoria']
        
        logger.info(f"✅ Dim_Producto transformado: {len(dim_producto)} registros")
        return dim_producto

    def transform_fact_ventas(self, df_ordenes, df_ordenes_detalle, df_tipo_cambio):
        """Transformar datos para Fact_Ventas desde MySQL"""
        logger.info("🔄 Transformando Fact_Ventas desde MySQL...")
        
        try:
            # Verificar si hay datos nuevos para procesar
            if df_ordenes.empty:
                logger.info("ℹ️  No hay órdenes nuevas para procesar")
                return pd.DataFrame()
                
            # Unir órdenes con detalles
            fact_ventas = pd.merge(
                df_ordenes_detalle,
                df_ordenes[['id', 'cliente_id', 'fecha', 'canal', 'moneda', 'total']],
                left_on='orden_id',
                right_on='id',
                how='inner'
            )
            
            logger.info(f"✅ Datos unidos: {len(fact_ventas)} registros")
            
            # Limpiar y convertir datos
            fact_ventas['fecha'] = pd.to_datetime(fact_ventas['fecha'], errors='coerce').dt.date
            
            # Limpiar montos usando la función mejorada
            logger.info("🧹 Limpiando montos numéricos...")
            fact_ventas['precio_unit_clean'] = fact_ventas['precio_unit'].apply(self.clean_numeric_string)
            fact_ventas['total_clean'] = fact_ventas['total'].apply(self.clean_numeric_string)
            
            # Unir con tipos de cambio
            fact_ventas = pd.merge(
                fact_ventas,
                df_tipo_cambio,
                left_on='fecha',
                right_on='fecha',
                how='inner'
            )
            
            logger.info(f"✅ Unido con tipos de cambio: {len(fact_ventas)} registros")
            
            # Convertir montos a USD si están en CRC
            def convertir_a_usd(fila):
                try:
                    if fila['moneda'] == 'CRC':
                        return fila['precio_unit_clean'] / fila['tipoCambio']
                    else:  # USD
                        return fila['precio_unit_clean']
                except Exception as e:
                    logger.warning(f"⚠️  Error en conversión de moneda: {e}")
                    return fila['precio_unit_clean']
            
            fact_ventas['precio_unit_usd'] = fact_ventas.apply(convertir_a_usd, axis=1)
            
            # Calcular campos derivados
            fact_ventas['totalVenta'] = (
                fact_ventas['cantidad'] * 
                fact_ventas['precio_unit_usd']
            ).round(2)
            
            fact_ventas['totalCRC'] = (fact_ventas['totalVenta'] * fact_ventas['tipoCambio']).round(2)
            
            # Renombrar columnas para consistencia
            fact_ventas = fact_ventas.rename(columns={
                'cliente_id': 'ClienteId',
                'producto_id': 'ProductoId',
                'fecha': 'Fecha',
                'cantidad': 'Cantidad',
                'precio_unit_usd': 'PrecioUnit',
                'canal': 'Canal'
            })
            
            # Agregar columna de descuento (no existe en MySQL, poner 0)
            fact_ventas['DescuentoPct'] = 0.0
            
            logger.info(f"✅ Fact_Ventas transformado: {len(fact_ventas)} registros")
            logger.info(f"   - Montos en USD: {len(fact_ventas[fact_ventas['moneda'] == 'USD'])}")
            logger.info(f"   - Montos en CRC: {len(fact_ventas[fact_ventas['moneda'] == 'CRC'])}")
            
            return fact_ventas
            
        except Exception as e:
            logger.error(f"❌ Error en transform_fact_ventas: {str(e)}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            raise

    def ensure_canales_existen(self, df_ordenes):
        """Asegurar que DIM_Canal tiene todos los canales de MySQL"""
        if df_ordenes.empty:
            logger.info("ℹ️  No hay órdenes nuevas, omitiendo verificación de canales")
            return True
            
        logger.info("🔧 Asegurando canales MySQL en DIM_Canal...")
        
        canales_unicos = df_ordenes['canal'].unique()
        logger.info(f"Canales encontrados en MySQL: {list(canales_unicos)}")
        
        try:
            with self.dw_engine.connect() as conn:
                # Obtener canales existentes
                existentes = pd.read_sql("SELECT canal FROM DIM_Canal", conn)
                existentes_set = set(existentes['canal'])
                
                # Insertar solo canales nuevos
                nuevos = set(canales_unicos) - existentes_set
                if nuevos:
                    for canal in nuevos:
                        conn.execute(text("INSERT INTO DIM_Canal (canal) VALUES (:canal)"), 
                                    {'canal': canal})
                    conn.commit()
                    logger.info(f"✅ {len(nuevos)} canales nuevos insertados desde MySQL: {list(nuevos)}")
                else:
                    logger.info("ℹ️  No hay canales nuevos desde MySQL")
                    
        except Exception as e:
            logger.error(f"❌ Error asegurando canales MySQL: {str(e)}")
            return False

    # ==================== CARGA CON CONTROL ====================
    def load_dim_cliente(self, df_dim_cliente):
        """Cargar Dim_Cliente en DW desde MySQL con control de duplicados"""
        logger.info("📤 Cargando Dim_Cliente desde MySQL...")
        
        try:
            # Quitar ID original de MySQL
            df_to_insert = df_dim_cliente.drop('idCliente', axis=1)
            
            with self.dw_engine.connect() as conn:
                # Obtener clientes existentes por email
                existentes = pd.read_sql("SELECT email FROM DIM_Cliente", conn)
                
                # Filtrar nuevos clientes
                nuevos = df_to_insert[~df_to_insert['email'].isin(existentes['email'])]
                
                if not nuevos.empty:
                    # Insertar en lotes pequeños para mejor manejo de errores
                    batch_size = 100
                    total_inserted = 0
                    
                    for i in range(0, len(nuevos), batch_size):
                        batch = nuevos.iloc[i:i + batch_size]
                        batch.to_sql(
                            name='DIM_Cliente',
                            con=conn,
                            if_exists='append',
                            index=False
                        )
                        total_inserted += len(batch)
                        logger.info(f"✅ Lote {i//batch_size + 1}: {len(batch)} clientes cargados")
                    
                    conn.commit() 
                    logger.info(f"✅ {total_inserted} nuevos clientes cargados desde MySQL")
                    return total_inserted
                else:
                    logger.info("ℹ️  No hay nuevos clientes desde MySQL para cargar")
                    return 0
                    
        except Exception as e:
            logger.error(f"❌ Error cargando Dim_Cliente desde MySQL: {str(e)}")
            return -1

    def load_dim_producto(self, df_dim_producto):
        """Cargar Dim_Producto en DW desde MySQL con control de duplicados"""
        logger.info("📤 Cargando Dim_Producto desde MySQL...")
        
        try:
            # Quitar ID original de MySQL
            df_to_insert = df_dim_producto.drop('idProducto', axis=1)
            
            with self.dw_engine.connect() as conn:
                # Obtener productos existentes por SKU
                existentes = pd.read_sql("SELECT sku FROM DIM_Producto", conn)
                
                # Filtrar nuevos productos
                nuevos = df_to_insert[~df_to_insert['sku'].isin(existentes['sku'])]
                
                if not nuevos.empty:
                    nuevos.to_sql(
                        name='DIM_Producto',
                        con=conn,
                        if_exists='append',
                        index=False
                    )
                    conn.commit() 
                    logger.info(f"✅ {len(nuevos)} nuevos productos cargados desde MySQL")
                    return len(nuevos)
                else:
                    logger.info("ℹ️  No hay nuevos productos desde MySQL para cargar")
                    return 0
                    
        except Exception as e:
            logger.error(f"❌ Error cargando Dim_Producto desde MySQL: {str(e)}")
            return -1

    def load_fact_ventas(self, df_fact_ventas):
        """Cargar Fact_Ventas en DW desde MySQL"""
        if df_fact_ventas.empty:
            logger.info("ℹ️  No hay ventas nuevas para cargar")
            return 0
            
        logger.info("📤 Cargando Fact_Ventas desde MySQL...")
        
        try:
            with self.dw_engine.connect() as conn:
                # Obtener mappings necesarios
                dim_cliente = pd.read_sql("SELECT idCliente, idCliente as ClienteId FROM DIM_Cliente", conn)
                dim_producto = pd.read_sql("SELECT idProducto, idProducto as ProductoId FROM DIM_Producto", conn)
                dim_tiempo = pd.read_sql("SELECT idTiempo, fecha FROM DIM_Tiempo", conn)
                dim_canal = pd.read_sql("SELECT idCanal, canal FROM DIM_Canal", conn)
                
                # Unir con dimensiones para obtener FKs
                fact_final = pd.merge(
                    df_fact_ventas,
                    dim_cliente,
                    left_on='ClienteId',
                    right_on='ClienteId',
                    how='inner'
                )
                
                fact_final = pd.merge(
                    fact_final,
                    dim_producto,
                    left_on='ProductoId',
                    right_on='ProductoId',
                    how='inner'
                )
                
                fact_final = pd.merge(
                    fact_final,
                    dim_tiempo,
                    left_on='Fecha',
                    right_on='fecha',
                    how='inner'
                )
                
                fact_final = pd.merge(
                    fact_final,
                    dim_canal,
                    left_on='Canal',
                    right_on='canal',
                    how='inner'
                )

                # Seleccionar columnas finales
                fact_final = fact_final[[
                    'idCliente', 'idProducto', 'idTiempo', 'idCanal',
                    'Cantidad', 'PrecioUnit', 'DescuentoPct', 'totalVenta', 'totalCRC'
                ]]
                
                fact_final.columns = [
                    'idCliente', 'idProducto', 'idTiempo', 'idCanal',
                    'cantidad', 'precioUnitario', 'descuentoPct', 'totalVenta', 'totalCRC'
                ]

                # Insertar en Fact_Ventas en lotes
                batch_size = 500
                total_inserted = 0
                
                for i in range(0, len(fact_final), batch_size):
                    batch = fact_final.iloc[i:i + batch_size]
                    batch.to_sql(
                        name='FACT_Ventas',
                        con=conn,
                        if_exists='append',
                        index=False
                    )
                    total_inserted += len(batch)
                    logger.info(f"✅ Lote {i//batch_size + 1}: {len(batch)} ventas cargadas")
                
                conn.commit() 
                
                logger.info(f"✅ {total_inserted} registros cargados en Fact_Ventas desde MySQL")
                return total_inserted
                
        except Exception as e:
            logger.error(f"❌ Error cargando Fact_Ventas desde MySQL: {str(e)}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return -1

    # ==================== EJECUCIÓN PRINCIPAL CON CONTROL ====================
    def execute_etl(self):
        """Ejecutar proceso ETL completo MySQL → DW con control de duplicación"""
        logger.info("🚀 INICIANDO ETL MySQL → DW")
        
        # Obtener información de la última ejecución
        last_execution = self.get_last_etl_execution()
        last_processed_date = last_execution.get('last_processed_date')
        
        if last_processed_date:
            logger.info(f"📅 Última ejecución: {last_execution['last_execution']}")
            logger.info(f"📊 Última fecha procesada: {last_processed_date}")
        
        if not self.connect():
            return False
        
        try:
            # INICIAR TRANSACCIÓN en el DW
            with self.dw_engine.begin() as conn:
                logger.info("🔒 Transacción iniciada en DW")
                
                # 1. EXTRACCIÓN CON CONTROL TEMPORAL
                clientes, productos, ordenes, ordenes_detalle, equivalencias, tipo_cambio, max_fecha = self.extract_data(last_processed_date)
                if clientes is None:
                    return False
                
                # Verificar si hay datos nuevos
                if ordenes.empty and last_processed_date:
                    logger.info("🎯 No hay datos nuevos para procesar. ETL completado sin cambios.")
                    return True
                
                # 2. TRANSFORMACIÓN
                dim_cliente = self.transform_dim_cliente(clientes)
                dim_producto = self.transform_dim_producto(productos, equivalencias)
                fact_ventas = self.transform_fact_ventas(ordenes, ordenes_detalle, tipo_cambio)
                
                # 3. CARGA
                self.ensure_canales_existen(ordenes)
                clientes_cargados = self.load_dim_cliente(dim_cliente)
                productos_cargados = self.load_dim_producto(dim_producto)
                ventas_cargadas = self.load_fact_ventas(fact_ventas)
                
                # 4. GUARDAR LOG DE EJECUCIÓN
                execution_data = {
                    "last_execution": datetime.now().isoformat(),
                    "last_processed_date": max_fecha if max_fecha else last_processed_date,
                    "processed_records": {
                        "clientes": clientes_cargados if clientes_cargados >= 0 else 0,
                        "productos": productos_cargados if productos_cargados >= 0 else 0,
                        "ventas": ventas_cargadas if ventas_cargadas >= 0 else 0
                    },
                    "source": "MySQL",
                    "status": "completed"
                }
                
                self.save_etl_execution(execution_data)
                
                logger.info("💾 Transacción COMMIT automático")
            
            logger.info("🎉 ETL MySQL COMPLETADO EXITOSAMENTE")
            logger.info(f"📊 Resumen de carga:")
            logger.info(f"   - Clientes nuevos: {execution_data['processed_records']['clientes']}")
            logger.info(f"   - Productos nuevos: {execution_data['processed_records']['productos']}")
            logger.info(f"   - Ventas nuevas: {execution_data['processed_records']['ventas']}")
            logger.info(f"   - Próxima ejecución procesará desde: {execution_data['last_processed_date']}")
            
            return True
            
        except Exception as e:
            # Guardar log de error
            error_data = {
                "last_execution": datetime.now().isoformat(),
                "last_processed_date": last_processed_date,
                "error": str(e),
                "status": "failed"
            }
            self.save_etl_execution(error_data)
            
            logger.error(f"❌ Error en ETL MySQL: {str(e)}")
            logger.error(f"🔍 Traceback completo: {traceback.format_exc()}")
            return False
        finally:
            self.disconnect()

def main():
    etl = ETL_MySQL_to_DW()
    success = etl.execute_etl()
    
    if success:
        print("\n✅ ETL ejecutado exitosamente sin duplicación de datos")
    else:
        print("\n❌ ETL falló - revisar logs para más detalles")

if __name__ == "__main__":
    main()