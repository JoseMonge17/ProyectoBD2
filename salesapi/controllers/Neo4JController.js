// server/controllers/ventasController.js

const neo4j = require('neo4j-driver');

const fs = require('fs');
const { spawn } = require('child_process');
const path = require('path');

// 👇 Ajusta esta ruta al lugar REAL donde está tu log.json
const LOG_PATH = 'E:/BD2/Proyecto/ProyectoBD2/Neo4j/log.json'; 
const PYTHON_SCRIPT_PATH = 'E:/BD2/Proyecto/ProyectoBD2/Neo4j/ETLNeo4j.py';
// o la ruta que corresponda en tu máquina
const PYTHON_COMMAND = 'python';

// Convierte "2025-11-23 18:28:55" a Date
function parseFechaCarga(fechaStr) {
  if (!fechaStr) return null;
  try {
    const [datePart, timePart] = fechaStr.split(' '); // "2025-11-23" y "18:28:55"
    const [year, month, day] = datePart.split('-').map(Number);
    const [hour, minute, second] = timePart.split(':').map(Number);
    return new Date(year, month - 1, day, hour, minute, second);
  } catch {
    return null;
  }
}

// Configuración del driver con IPv4 explícito y sin encriptación
const driver = neo4j.driver(
  'neo4j://127.0.0.1:7687', // Cambiado de 'bolt://' a 'neo4j://'
  neo4j.auth.basic('neo4j', 'Jjmb260505*'),
  { 
    encrypted: false, // Desactiva encriptación (Neo4j 4.0+)
    maxConnectionPoolSize: 50,
    connectionTimeout: 30000,
    disableLosslessIntegers: true
  }
);

// Función para obtener las ventas desde Neo4j
const getVentas = async (req, res) => {
  console.log("Extrayendo ventas");
  const session = driver.session({ database: 'ventas' });

  try {
    // 🔹 Leer log.json desde el disco
    let fechaLimiteDate = null;
    try {
      const rawLog = fs.readFileSync(LOG_PATH, 'utf8');
      const logJson = JSON.parse(rawLog); // { last_id, fechaCarga }
      
      if(logJson.fechaCarga == "")
        logJson.fechaCarga = "2000-11-23 18:28:55"
      fechaLimiteDate = parseFechaCarga(logJson.fechaCarga);
      console.log('Fecha límite desde log.json:', logJson.fechaCarga, fechaLimiteDate);
    } catch (e) {
      console.warn('No se pudo leer log.json, no se aplicará lógica de edición:', e.message);
    }

    const result = await session.run(
      'MATCH (c:Cliente)-[:REALIZO]->(o:Orden) ' +
      'RETURN o.idOrden AS id, o.fecha AS fecha, o.total AS total, o.moneda AS moneda, o.canal AS canal, c.nombre AS cliente ' +
      'ORDER BY o.idOrden ASC '
    );

    const ventas = result.records.map(record => {
      const fechaVentaStr = record.get('fecha');
      let puedeEditar = false;

      if (fechaLimiteDate) {
        const fechaVentaDate = new Date(fechaVentaStr);
        if (!isNaN(fechaVentaDate.getTime())) {
          puedeEditar = fechaVentaDate > fechaLimiteDate;
        }
      }

      return {
        id: record.get('id'),
        fecha: fechaVentaStr,
        total: record.get('total'),
        moneda: record.get('moneda'),
        canal: record.get('canal'),
        cliente: record.get('cliente'),
        puedeEditar // 👈 aquí va la marca para el front
      };
    });

    res.json(ventas);
  } catch (error) {
    console.error('Error al obtener las ventas de Neo4j:', error);
    res.status(500).json({
      message: 'Error al obtener las ventas',
      error: error.message
    });
  } finally {
    await session.close();
  }
};

// Funcion para obtener los datos de una venta en concreto
const getVentaById = async (req, res) => {
  const { id } = req.params; // viene de /api/neo4j/:id
  const session = driver.session({ database: 'ventas' });

  try {
    const result = await session.run(
      `
      MATCH (o:Orden {idOrden: $idOrden})
      MATCH (c:Cliente)-[relCliente:REALIZO]->(o)
      MATCH (o)-[r:CONTIENTE]->(p:Producto)
      RETURN 
        {
          idOrden: o.idOrden,
          fecha: o.fecha,
          total: o.total,
          moneda: o.moneda,
          canal: o.canal
        } AS orden,
        {
          idCliente: c.idCliente,
          nombre: c.nombre,
          telefono: c.telefono,
          correo: c.correo
        } AS cliente,
        {
          tipo: type(relCliente),
          propiedades: properties(relCliente)
        } AS relacion_cliente_orden,
        collect({
          producto: properties(p),
          relacion: {
            tipo: type(r),
            propiedades: properties(r)
          }
        }) AS productos
      `,
      { idOrden: Number(id) } // si lo guardas numérico
    );

    if (result.records.length === 0) {
      return res.status(404).json({ message: 'Venta no encontrada' });
    }

    const record = result.records[0];

    res.json({
      orden: record.get('orden'),
      cliente: record.get('cliente'),
      relacion_cliente_orden: record.get('relacion_cliente_orden'),
      productos: record.get('productos'),
    });
  } catch (error) {
    console.error('Error al obtener la venta en Neo4j:', error);
    res.status(500).json({
      message: 'Error al obtener la venta',
      error: error.message,
    });
  } finally {
    await session.close();
  }
};

// Función para crear una nueva venta
const createVentas = async (req, res) => {
  const session = driver.session({ database: 'ventas' });

  console.log(req.body);
  const { cliente, moneda, canal, productos } = req.body; // ya no usamos fecha del body

  try {
    // 1. Obtener el ID más alto de las órdenes existentes
    const result = await session.run(
      'MATCH (o:Orden) RETURN coalesce(MAX(o.idOrden), 0) AS maxId'
    );

    let maxId = result.records[0].get('maxId');

    // Si viene como Integer de neo4j, lo convertimos
    if (neo4j.isInt(maxId)) {
      maxId = maxId.toNumber();
    }

    const nuevoId = (maxId || 0) + 1;

    // 2. Crear fecha en este momento
    const fechaActual = new Date().toISOString();

    // 3. Calcular total de la orden
    const totalOrden = productos.reduce((acc, producto) => acc + producto.total, 0);

    // 4. Crear nodo de la orden con el nuevo ID
    const ordenResult = await session.run(
      `
      CREATE (o:Orden {
        idOrden: $nuevoId,
        fecha: $fecha,
        total: $total,
        moneda: $moneda,
        canal: $canal
      })
      RETURN o
      `,
      {
        nuevoId: nuevoId,
        fecha: fechaActual,
        total: totalOrden,
        moneda: moneda,
        canal: canal
      }
    );

    const orden = ordenResult.records[0].get('o');

    // 5. Crear la relación con el cliente (sin recrear la Orden)
    await session.run(
      `
      MATCH (c:Cliente {idCliente: $clienteId}),
            (o:Orden  {idOrden: $ordenId})
      MERGE (c)-[:REALIZO]->(o)
      `,
      {
        clienteId: cliente,
        ordenId: orden.properties.idOrden
      }
    );

    // 6. Crear relaciones con los productos (igual: MATCH, no MERGE del nodo Orden)
    for (let producto of productos) {
      await session.run(
        `
        MATCH (p:Producto {idProducto: $productoId}),
              (o:Orden   {idOrden: $ordenId})
        MERGE (o)-[:CONTIENTE {
          cantidad: $cantidad,
          precio: $precio
        }]->(p)
        `,
        {
          productoId: producto.id,
          ordenId: orden.properties.idOrden,
          cantidad: producto.cantidad,
          precio: producto.precio,
          total: producto.total
        }
      );
    }

    res.status(201).json({
      message: 'Venta creada con éxito',
      idOrden: orden.properties.idOrden,
      fecha: fechaActual
    });

  } catch (error) {
    console.error('Error al crear la venta en Neo4j:', error);
    res.status(500).json({ message: 'Error al crear la venta', error: error.message });
  } finally {
    await session.close();
  }
};

//Funcion de actualizar venta
const updateVenta = async (req, res) => {
  const { id } = req.params; // ID de la orden a actualizar
  const { cliente, moneda, canal, productos } = req.body;
  const session = driver.session({ database: 'ventas' });

  try {
    const idOrden = Number(id);
    
    // 1. Verificar que la orden existe
    const existeResult = await session.run(
      'MATCH (o:Orden {idOrden: $idOrden}) RETURN o',
      { idOrden }
    );

    if (existeResult.records.length === 0) {
      return res.status(404).json({ message: `Venta con id ${id} no encontrada` });
    }

    // 2. Calcular nuevo total
    const totalOrden = productos.reduce((acc, producto) => acc + producto.total, 0);

    // 3. Actualizar propiedades de la Orden (excepto fecha e idOrden)
    await session.run(
      `
      MATCH (o:Orden {idOrden: $idOrden})
      SET o.total = $total,
          o.moneda = $moneda,
          o.canal = $canal
      RETURN o
      `,
      {
        idOrden: idOrden,
        total: totalOrden,
        moneda: moneda,
        canal: canal
      }
    );

    // 4. Actualizar relación con el cliente
    // Primero eliminar la relación anterior
    await session.run(
      `
      MATCH (c:Cliente)-[r:REALIZO]->(o:Orden {idOrden: $idOrden})
      DELETE r
      `,
      { idOrden }
    );

    // Crear nueva relación con el cliente actualizado
    await session.run(
      `
      MATCH (c:Cliente {idCliente: $clienteId}),
            (o:Orden {idOrden: $idOrden})
      MERGE (c)-[:REALIZO]->(o)
      `,
      {
        clienteId: cliente,
        idOrden: idOrden
      }
    );

    // 5. Actualizar productos: eliminar todas las relaciones CONTIENTE anteriores
    await session.run(
      `
      MATCH (o:Orden {idOrden: $idOrden})-[r:CONTIENTE]->(p:Producto)
      DELETE r
      `,
      { idOrden }
    );

    // 6. Crear nuevas relaciones CONTIENTE con los productos actualizados
    for (let producto of productos) {
      await session.run(
        `
        MATCH (p:Producto {idProducto: $productoId}),
              (o:Orden {idOrden: $idOrden})
        MERGE (o)-[:CONTIENTE {
          cantidad: $cantidad,
          precio: $precio
        }]->(p)
        `,
        {
          productoId: producto.id,
          idOrden: idOrden,
          cantidad: producto.cantidad,
          precio: producto.precio
        }
      );
    }

    res.json({
      message: 'Venta actualizada con éxito',
      idOrden: idOrden,
      total: totalOrden
    });

  } catch (error) {
    console.error('Error al actualizar la venta en Neo4j:', error);
    res.status(500).json({
      message: 'Error al actualizar la venta',
      error: error.message
    });
  } finally {
    await session.close();
  }
};

// Funcion de eliminar venta
const deleteVenta = async (req, res) => {
  const { id } = req.params; // viene de /api/neo4j/:id
  const session = driver.session({ database: 'ventas' });

  try {
    // Si idOrden es numérico en Neo4j, conviene convertirlo a Number
    const idOrden = Number(id);

    const result = await session.run(
      `
      MATCH (o:Orden {idOrden: $idOrden})
      DETACH DELETE o
      `,
      { idOrden }
    );

    // Opcional: revisar si realmente eliminó algo
    const summary = result.summary;
    const nodesDeleted = summary.counters.updates().nodesDeleted || 0;

    if (nodesDeleted === 0) {
      return res.status(404).json({ message: `No se encontró la venta con id ${id}` });
    }

    res.json({ message: `Venta ${id} eliminada correctamente` });

  } catch (error) {
    console.error('Error al eliminar la venta en Neo4j:', error);
    res.status(500).json({
      message: 'Error al eliminar la venta',
      error: error.message
    });
  } finally {
    await session.close();
  }
};

// Función para obtener todos los clientes desde Neo4j
const getClientes = async (req, res) => {
  console.log("Extrayendo clientes");
  const session = driver.session({ database: 'ventas' });
  
  try {
    const result = await session.run(
      'MATCH (c:Cliente) ' +
      'RETURN c.nombre AS nombre, c.idCliente AS id' // Solo traer el nombre del cliente
    );

    const clientes = result.records.map((record) => ({
      nombre: record.get('nombre'),
      id: record.get('id')
    }));

    res.json(clientes);
  } catch (error) {
    console.error('Error al obtener los clientes de Neo4j:', error);
    res.status(500).json({
      message: 'Error al obtener los clientes',
      error: error.message,
    });
  } finally {
    await session.close();
  }
};

// Función para obtener todos los productos desde Neo4j
const getProductos = async (req, res) => {
  console.log("Extrayendo productos");
  const session = driver.session({ database: 'ventas' });
  
  try {
    const result = await session.run(
      'MATCH (p:Producto) ' +
      'RETURN p.nombre AS nombre, p.idProducto AS id' // Solo traer el nombre del producto
    );

    const productos = result.records.map((record) => ({
      nombre: record.get('nombre'),
      id: record.get('id')
    }));

    res.json(productos);
  } catch (error) {
    console.error('Error al obtener los productos de Neo4j:', error);
    res.status(500).json({
      message: 'Error al obtener los productos',
      error: error.message,
    });
  } finally {
    await session.close();
  }
};

// Función para cerrar el driver cuando la aplicación termine
const closeDriver = async () => {
  await driver.close();
};

const ejecutarETL = async (req, res) => {
  console.log('🔄 Iniciando proceso ETL...');
  console.log('📂 Script:', PYTHON_SCRIPT_PATH);

  // Verificar que el archivo existe
  const fs = require('fs');
  if (!fs.existsSync(PYTHON_SCRIPT_PATH)) {
    return res.status(404).json({
      message: 'Script ETL no encontrado',
      path: PYTHON_SCRIPT_PATH
    });
  }

  try {
    // Spawn el proceso de Python
    const pythonProcess = spawn(PYTHON_COMMAND, [PYTHON_SCRIPT_PATH]);

    let stdoutData = '';
    let stderrData = '';

    // Capturar salida estándar (stdout)
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('📤 Python stdout:', output);
      stdoutData += output;
    });

    // Capturar errores (stderr)
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      console.error('❌ Python stderr:', error);
      stderrData += error;
    });

    // Cuando el proceso termina
    pythonProcess.on('close', (code) => {
      console.log(`🏁 Proceso ETL terminado con código: ${code}`);

      if (code === 0) {
        // Éxito
        res.json({
          success: true,
          message: 'ETL ejecutado exitosamente',
          output: stdoutData,
          exitCode: code
        });
      } else {
        // Error
        res.status(500).json({
          success: false,
          message: 'El proceso ETL finalizó con errores',
          error: stderrData || stdoutData,
          exitCode: code
        });
      }
    });

    // Manejar errores del proceso
    pythonProcess.on('error', (error) => {
      console.error('❌ Error al ejecutar Python:', error);
      res.status(500).json({
        success: false,
        message: 'Error al ejecutar el script ETL',
        error: error.message
      });
    });

  } catch (error) {
    console.error('❌ Error en ejecutarETL:', error);
    res.status(500).json({
      success: false,
      message: 'Error al iniciar el proceso ETL',
      error: error.message
    });
  }
};

module.exports = { getVentas, getClientes, getProductos, closeDriver, createVentas, getVentaById, deleteVenta, updateVenta, ejecutarETL };