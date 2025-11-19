import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETL_MySQL_to_DW:
    def __init__(self):
        # Connection strings
        self.mysql_conn_str = "mysql+mysqlconnector://root:@127.0.0.1:3307/sales_mysql"
        self.dw_conn_str = "mssql+pyodbc://localhost/DW_Proyecto_Sales?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        
        self.mysql_engine = None
        self.dw_engine = None
        
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

    # ==================== EXTRACCIÓN ====================
    def extract_data(self):
        """Extraer datos de MySQL fuente"""
        try:
            logger.info("📥 Extrayendo datos de MySQL...")
            
            # Extraer tablas fuente de MySQL
            with self.mysql_engine.connect() as conn:
                clientes = pd.read_sql("SELECT * FROM Cliente", conn)
                productos = pd.read_sql("SELECT * FROM Producto", conn)
                ordenes = pd.read_sql("SELECT * FROM Orden", conn)
                ordenes_detalle = pd.read_sql("SELECT * FROM OrdenDetalle", conn)
            
            # Extraer Equivalencias del DW
            with self.dw_engine.connect() as conn:
                equivalencias = pd.read_sql("SELECT * FROM EquivalenciasProductos", conn)
                tipo_cambio = pd.read_sql("SELECT fecha, tipoCambio FROM DIM_Tiempo", conn)
            
            logger.info(f"✅ Extracción MySQL completada: {len(clientes)} clientes, {len(productos)} productos, {len(ordenes)} órdenes")
            return clientes, productos, ordenes, ordenes_detalle, equivalencias, tipo_cambio
            
        except Exception as e:
            logger.error(f"❌ Error en extracción MySQL: {str(e)}")
            return None, None, None, None, None, None

    # ==================== TRANSFORMACIÓN ====================
    def transform_dim_cliente(self, df_clientes):
        """Transformar datos para Dim_Cliente desde MySQL"""
        logger.info("🔄 Transformando Dim_Cliente desde MySQL...")
        
        dim_cliente = df_clientes[[
            'id', 'nombre', 'correo', 'genero', 'pais', 'created_at'
        ]].copy()
        
        # Estandarización de género
        genero_map = {'M': 'Masculino', 'F': 'Femenino', 'X': 'No especificado'}
        dim_cliente['genero'] = dim_cliente['genero'].map(genero_map).fillna('No especificado')
        
        # Convertir fecha
        dim_cliente['created_at'] = pd.to_datetime(dim_cliente['created_at']).dt.date
        
        dim_cliente.columns = ['idCliente', 'nombre', 'email', 'genero', 'pais', 'fechaRegistro']
        return dim_cliente
    
    def transform_dim_producto(self, df_productos, df_equivalencias):
        """Transformar datos para Dim_Producto desde MySQL"""
        logger.info("🔄 Transformando Dim_Producto desde MySQL...")
        
        # Unir con equivalencias para obtener SKU oficial
        dim_producto = pd.merge(
            df_productos,
            df_equivalencias[df_equivalencias['source'] == 'MySQL'][['source_code', 'sku_oficial']],
            left_on='codigo_alt',
            right_on='source_code',
            how='left'
        )
        
        # Si no hay equivalencia, usar código_alt como SKU
        dim_producto['sku_oficial'] = dim_producto['sku_oficial'].fillna(dim_producto['codigo_alt'])
        
        dim_producto = dim_producto[[
            'id', 'sku_oficial', 'nombre', 'categoria'
        ]]
        
        dim_producto.columns = ['idProducto', 'sku', 'nombre', 'categoria']
        return dim_producto

    def transform_fact_ventas(self, df_ordenes, df_ordenes_detalle, df_tipo_cambio):
        """Transformar datos para Fact_Ventas desde MySQL"""
        logger.info("🔄 Transformando Fact_Ventas desde MySQL...")
        
        # Unir órdenes con detalles
        fact_ventas = pd.merge(
            df_ordenes_detalle,
            df_ordenes[['id', 'cliente_id', 'fecha', 'canal', 'moneda', 'total']],
            left_on='orden_id',
            right_on='id',
            how='inner'
        )
        
        # Limpiar y convertir datos
        fact_ventas['fecha'] = pd.to_datetime(fact_ventas['fecha']).dt.date
        
        # Limpiar montos (remover comas y convertir a float)
        fact_ventas['precio_unit'] = fact_ventas['precio_unit'].str.replace(',', '').astype(float)
        fact_ventas['total'] = fact_ventas['total'].str.replace(',', '').astype(float)
        
        # Unir con tipos de cambio
        fact_ventas = pd.merge(
            fact_ventas,
            df_tipo_cambio,
            left_on='fecha',
            right_on='fecha',
            how='inner'
        )
        
        # Convertir montos a USD si están en CRC
        def convertir_a_usd(fila):
            if fila['moneda'] == 'CRC':
                return fila['precio_unit'] / fila['tipoCambio']
            else:  # USD
                return fila['precio_unit']
        
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
            'precio_unit_usd': 'PrecioUnit'
        })
        
        # Agregar columna de descuento (no existe en MySQL, poner 0)
        fact_ventas['DescuentoPct'] = 0.0
        
        return fact_ventas

    def ensure_canales_existen(self, df_ordenes):
        """Asegurar que DIM_Canal tiene todos los canales de MySQL"""
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
                    from sqlalchemy import text 
                    
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

    # ==================== CARGA ====================
    def load_dim_cliente(self, df_dim_cliente):
        """Cargar Dim_Cliente en DW desde MySQL"""
        logger.info("📤 Cargando Dim_Cliente desde MySQL...")
        
        try:
            # Quitar ID original
            df_to_insert = df_dim_cliente.drop('idCliente', axis=1)
            
            with self.dw_engine.connect() as conn:
                # Obtener clientes existentes por email
                existentes = pd.read_sql("SELECT email FROM DIM_Cliente", conn)
                
                # Filtrar nuevos clientes
                nuevos = df_to_insert[~df_to_insert['email'].isin(existentes['email'])]
                
                if not nuevos.empty:
                    nuevos.to_sql(
                        name='DIM_Cliente',
                        con=conn,
                        if_exists='append',
                        index=False
                    )
                    conn.commit() 
                    logger.info(f"✅ {len(nuevos)} nuevos clientes cargados desde MySQL")
                else:
                    logger.info("ℹ️  No hay nuevos clientes desde MySQL para cargar")
                    
            return True
        except Exception as e:
            logger.error(f"❌ Error cargando Dim_Cliente desde MySQL: {str(e)}")
            return False

    def load_dim_producto(self, df_dim_producto):
        """Cargar Dim_Producto en DW desde MySQL"""
        logger.info("📤 Cargando Dim_Producto desde MySQL...")
        
        try:
            # Quitar ID original
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
                else:
                    logger.info("ℹ️  No hay nuevos productos desde MySQL para cargar")
                    
            return True
        except Exception as e:
            logger.error(f"❌ Error cargando Dim_Producto desde MySQL: {str(e)}")
            return False

    def load_fact_ventas(self, df_fact_ventas):
        """Cargar Fact_Ventas en DW desde MySQL"""
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

                # Insertar en Fact_Ventas
                fact_final.to_sql(
                    name='FACT_Ventas',
                    con=conn,
                    if_exists='append',
                    index=False
                )
                conn.commit() 
                
                logger.info(f"✅ {len(fact_final)} registros cargados en Fact_Ventas desde MySQL")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error cargando Fact_Ventas desde MySQL: {str(e)}")
            return False

    # ==================== EJECUCIÓN PRINCIPAL ====================
    def execute_etl(self):
        """Ejecutar proceso ETL completo MySQL → DW"""
        logger.info("🚀 INICIANDO ETL MySQL → DW")
        
        if not self.connect():
            return False
        
        try:
            # INICIAR TRANSACCIÓN en el DW
            with self.dw_engine.begin() as conn:
                logger.info("🔒 Transacción iniciada en DW")
                
                # 1. EXTRACCIÓN
                clientes, productos, ordenes, ordenes_detalle, equivalencias, tipo_cambio = self.extract_data()
                if clientes is None:
                    return False
                
                # 2. TRANSFORMACIÓN
                dim_cliente = self.transform_dim_cliente(clientes)
                dim_producto = self.transform_dim_producto(productos, equivalencias)
                fact_ventas = self.transform_fact_ventas(ordenes, ordenes_detalle, tipo_cambio)
                
                # 3. CARGA
                self.ensure_canales_existen(ordenes)
                self.load_dim_cliente(dim_cliente)
                self.load_dim_producto(dim_producto)
                self.load_fact_ventas(fact_ventas)
                
                logger.info("💾 Transacción COMMIT automático")
            
            logger.info("🎉 ETL MySQL COMPLETADO EXITOSAMENTE")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en ETL MySQL: {str(e)}")
            return False
        finally:
            self.disconnect()

def main():
    etl = ETL_MySQL_to_DW()
    etl.execute_etl()

if __name__ == "__main__":
    main()