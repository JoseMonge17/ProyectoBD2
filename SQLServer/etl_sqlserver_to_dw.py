# etl_sqlserver_to_dw_corrected.py
import pandas as pd
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETL_SQLServer_to_DW:
    def __init__(self):
        # Connection strings
        self.source_conn_str = "mssql+pyodbc://localhost/Ventas_Transactional?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        self.dw_conn_str = "mssql+pyodbc://localhost/DW_Proyecto_Sales?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        
        self.source_engine = None
        self.dw_engine = None
        
    def connect(self):
        """Conectar a ambas bases de datos"""
        try:
            self.source_engine = create_engine(self.source_conn_str)
            self.dw_engine = create_engine(self.dw_conn_str)
            logger.info("✅ Conexiones establecidas")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {str(e)}")
            return False

    def disconnect(self):
        """Cerrar conexiones"""
        if self.source_engine:
            self.source_engine.dispose()
        if self.dw_engine:
            self.dw_engine.dispose()
        logger.info("🔌 Conexiones cerradas")

    # ==================== EXTRACCIÓN ====================
    def extract_data(self):
        """Extraer datos de SQL Server fuente y Equivalencias del DW"""
        try:
            logger.info("📥 Extrayendo datos fuente...")
            
            # Extraer tablas fuente de SQL Server transaccional
            with self.source_engine.connect() as conn:
                clientes = pd.read_sql("SELECT * FROM sales_ms.Cliente", conn)
                productos = pd.read_sql("SELECT * FROM sales_ms.Producto", conn)
                ordenes = pd.read_sql("SELECT * FROM sales_ms.Orden", conn)
                ordenes_detalle = pd.read_sql("SELECT * FROM sales_ms.OrdenDetalle", conn)
            
            # Extraer Equivalencias del DW
            with self.dw_engine.connect() as conn:
                equivalencias = pd.read_sql("SELECT * FROM EquivalenciasProductos", conn)
            
            logger.info(f"✅ Extracción completada: {len(clientes)} clientes, {len(productos)} productos, {len(ordenes)} órdenes, {len(equivalencias)} equivalencias")
            return clientes, productos, ordenes, ordenes_detalle, equivalencias
            
        except Exception as e:
            logger.error(f"❌ Error en extracción: {str(e)}")
            return None, None, None, None, None

    # ==================== TRANSFORMACIÓN ====================
    def transform_dim_cliente(self, df_clientes):
        """Transformar datos para Dim_Cliente"""
        logger.info("🔄 Transformando Dim_Cliente...")
        
        # Ya está estandarizado, solo seleccionar columnas necesarias
        dim_cliente = df_clientes[[
            'ClienteId', 'Nombre', 'Email', 'Genero', 'Pais', 'FechaRegistro'
        ]].copy()
        
        dim_cliente.columns = ['idCliente', 'nombre', 'email', 'genero', 'pais', 'fechaRegistro']
        return dim_cliente
    
    def transform_dim_producto(self, df_productos, df_equivalencias):
        """Transformar datos para Dim_Producto - SOLO cambio de nombres"""
        logger.info("🔄 Transformando Dim_Producto...")
        
        # Solo renombrar columnas y mantener estructura
        dim_producto = df_productos[[
            'ProductoId', 'SKU', 'Nombre', 'Categoria'
        ]].copy()
        
        dim_producto.columns = ['idProducto', 'sku', 'nombre', 'categoria']
        return dim_producto

    def ensure_canales_existen(self, df_ordenes):
        """Asegurar que DIM_Canal tiene todos los canales de las órdenes"""
        logger.info("🔧 Asegurando canales en DIM_Canal...")
        
        # Extraer canales únicos de las órdenes
        canales_unicos = df_ordenes['Canal'].unique()
        logger.info(f"Canales encontrados en órdenes: {list(canales_unicos)}")
        
        try:
            with self.dw_engine.connect() as conn:
                # Verificar si DIM_Canal está vacía
                count_result = pd.read_sql("SELECT COUNT(*) as count FROM DIM_Canal", conn)
                esta_vacia = count_result.iloc[0]['count'] == 0
                
                if esta_vacia:
                    logger.info("📥 DIM_Canal está vacía, insertando canales...")
                    # Insertar todos los canales únicos USANDO text()
                    from sqlalchemy import text  
                    
                    for canal in canales_unicos:
                        # CORREGIDO: Usar text() para SQL nativo
                        conn.execute(text("INSERT INTO DIM_Canal (canal) VALUES (:canal)"), 
                                    {'canal': canal})
                    conn.commit()
                    logger.info(f"✅ {len(canales_unicos)} canales insertados en DIM_Canal")
                else:
                    logger.info("✅ DIM_Canal ya tiene datos, verificando canales nuevos...")
                    # Obtener canales existentes
                    existentes = pd.read_sql("SELECT canal FROM DIM_Canal", conn)
                    existentes_set = set(existentes['canal'])
                    
                    # Insertar solo canales nuevos
                    nuevos = set(canales_unicos) - existentes_set
                    if nuevos:
                        from sqlalchemy import text 
                        
                        for canal in nuevos:
                            # CORREGIDO: Usar text() para SQL nativo
                            conn.execute(text("INSERT INTO DIM_Canal (canal) VALUES (:canal)"), 
                                        {'canal': canal})
                        conn.commit()
                        logger.info(f"✅ {len(nuevos)} canales nuevos insertados: {list(nuevos)}")
                    else:
                        logger.info("ℹ️  No hay canales nuevos para insertar")
                        
        except Exception as e:
            logger.error(f"❌ Error asegurando canales: {str(e)}")
            return False

    def transform_fact_ventas(self, df_ordenes, df_ordenes_detalle):
        """Transformar datos para Fact_Ventas - USANDO DIM_Tiempo existente"""
        logger.info("🔄 Transformando Fact_Ventas...")
       
        # Unir órdenes con detalles
        fact_ventas = pd.merge(
            df_ordenes_detalle,
            df_ordenes[['OrdenId', 'ClienteId', 'Fecha', 'Canal']],
            on='OrdenId',
            how='inner'
        )
    
        # Convertir fecha y obtener tipo de cambio de DIM_Tiempo
        fact_ventas['Fecha'] = pd.to_datetime(fact_ventas['Fecha']).dt.date

        # Obtener tipos de cambio desde DIM_Tiempo
        with self.dw_engine.connect() as conn:
            tiempos_df = pd.read_sql("SELECT fecha, tipoCambio FROM DIM_Tiempo", conn)

        # Unir con tipos de cambio
        fact_ventas = pd.merge(
            fact_ventas,
            tiempos_df,
            left_on='Fecha',
            right_on='fecha',
            how='inner'
        )

        # Calcular campos derivados CON TIPO DE CAMBIO REAL
        fact_ventas['totalVenta'] = (
            fact_ventas['Cantidad'] * 
            fact_ventas['PrecioUnit'] * 
            (1 - fact_ventas['DescuentoPct'].fillna(0))
        ).round(2)
        
        fact_ventas['totalCRC'] = (fact_ventas['totalVenta'] * fact_ventas['tipoCambio']).round(2)
      
        return fact_ventas

    # ==================== CARGA ====================
    def load_dim_cliente(self, df_dim_cliente):
        """Cargar Dim_Cliente en DW - SIN idCliente"""
        logger.info("📤 Cargando Dim_Cliente...")
        
        try:
            # QUITAR la columna idCliente antes de insertar
            df_to_insert = df_dim_cliente.drop('idCliente', axis=1)
            
            with self.dw_engine.connect() as conn:
                # Obtener clientes existentes por email (no por ID)
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
                    logger.info(f"✅ {len(nuevos)} nuevos clientes cargados")
                else:
                    logger.info("ℹ️  No hay nuevos clientes para cargar")
                    
            return True
        except Exception as e:
            logger.error(f"❌ Error cargando Dim_Cliente: {str(e)}")
            return False

    def load_dim_producto(self, df_dim_producto):
        """Cargar Dim_Producto en DW - SIN idProducto"""
        logger.info("📤 Cargando Dim_Producto...")
        
        try:
            # QUITAR la columna idProducto antes de insertar
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
                    logger.info(f"✅ {len(nuevos)} nuevos productos cargados")
                else:
                    logger.info("ℹ️  No hay nuevos productos para cargar")
                    
            return True
        except Exception as e:
            logger.error(f"❌ Error cargando Dim_Producto: {str(e)}")
            return False

    def load_fact_ventas(self, df_fact_ventas):
        """Cargar Fact_Ventas en DW - CON TIPO DE CAMBIO REAL"""
        logger.info("📤 Cargando Fact_Ventas...")
        
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
                
                logger.info(f"✅ {len(fact_final)} registros cargados en Fact_Ventas")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error cargando Fact_Ventas: {str(e)}")
            return False

    # ==================== EJECUCIÓN PRINCIPAL ====================
    def execute_etl(self):
        """Ejecutar proceso ETL completo CON TRANSACCIÓN"""
        logger.info("🚀 INICIANDO ETL SQL Server → DW")
        
        if not self.connect():
            return False
        
        try:
            # INICIAR TRANSACCIÓN en el DW
            with self.dw_engine.begin() as conn:
                logger.info("🔒 Transacción iniciada en DW")
                
                # 1. EXTRACCIÓN
                clientes, productos, ordenes, ordenes_detalle, equivalencias = self.extract_data()
                if clientes is None:
                    return False
                
                # 2. TRANSFORMACIÓN
                dim_cliente = self.transform_dim_cliente(clientes)
                dim_producto = self.transform_dim_producto(productos, equivalencias)
                fact_ventas = self.transform_fact_ventas(ordenes, ordenes_detalle)
                
                # 3. CARGA (pasar la conexión de transacción)
                self.ensure_canales_existen(ordenes)
                self.load_dim_cliente(dim_cliente)
                self.load_dim_producto(dim_producto)
                self.load_fact_ventas(fact_ventas)
                
                # COMMIT automático al salir del bloque 'with'
                logger.info("💾 Transacción COMMIT automático")
            
            logger.info("🎉 ETL COMPLETADO EXITOSAMENTE")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en ETL: {str(e)}")
            # ROLLBACK automático
            return False
        finally:
            self.disconnect()

def main():
    etl = ETL_SQLServer_to_DW()
    etl.execute_etl()

if __name__ == "__main__":
    main()