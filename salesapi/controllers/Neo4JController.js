// server/controllers/ventasController.js

const neo4j = require('neo4j-driver');

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
  console.log("Estrayendo ventas");
  const session = driver.session({ database: 'ventas' }); // Crear sesión aquí
  
  try {
    const result = await session.run(
        'MATCH (c:Cliente)-[:REALIZO]->(o:Orden) ' +
        'RETURN o.idOrden AS id, o.fecha AS fecha, o.total AS total, o.moneda AS moneda, o.canal AS canal, c.nombre AS cliente ' +
        'ORDER BY o.idOrden ASC ' +  // Ordenar por fecha, de más reciente a más antigua
        'LIMIT 50'
    );
    // Mapear los resultados de la consulta
    const ventas = result.records.map(record => ({
      id: record.get('id'),
      fecha: record.get('fecha'),
      total: record.get('total'),
      moneda: record.get('moneda'),
      canal: record.get('canal'),
      cliente: record.get('cliente'),
    }));

    // Enviar los datos de las ventas como respuesta
    res.json(ventas);
  } catch (error) {
    console.error('Error al obtener las ventas de Neo4j:', error);
    res.status(500).json({ 
      message: 'Error al obtener las ventas',
      error: error.message 
    });
  } finally {
    await session.close(); // Cerrar la sesión de Neo4j
  }
};

// Función para crear una nueva venta
const createVenta = async (req, res) => {
  const session = driver.session({ database: 'ventas' }); // Crear sesión aquí

  const { fecha, cliente, moneda, canal, productos } = req.body;

  try {
    // Obtener el ID más alto de las órdenes existentes
    const result = await session.run(
      'MATCH (o:Orden) RETURN MAX(o.idOrden) AS maxId'
    );

    // Obtener el máximo ID y sumar 1
    const maxId = result.records[0].get('maxId') || 0; // Si no hay órdenes, empieza desde 0
    const nuevoId = maxId + 1;

    // Crear un nodo de la orden con el nuevo ID
    const ordenResult = await session.run(
      'CREATE (o:Orden {idOrden: $nuevoId, fecha: $fecha, total: $total, moneda: $moneda, canal: $canal}) RETURN o',
      {
        nuevoId: nuevoId,
        fecha: new Date(fecha).toISOString(),
        total: productos.reduce((acc, producto) => acc + producto.total, 0), // Sumar total de la venta
        moneda: moneda,
        canal: canal
      }
    );

    const orden = ordenResult.records[0].get('o'); // Orden creada

    // Crear la relación con el cliente
    await session.run(
      'MATCH (c:Cliente {idCliente: $clienteId}) ' +
      'MERGE (c)-[:REALIZO]->(o:Orden {idOrden: $ordenId})',
      {
        clienteId: cliente,
        ordenId: orden.properties.idOrden
      }
    );

    // Crear relaciones con los productos
    for (let producto of productos) {
      await session.run(
        'MATCH (p:Producto {idProducto: $productoId}) ' +
        'MERGE (o:Orden {idOrden: $ordenId})-[:CONTIENTE {cantidad: $cantidad, precio: $precio, total: $total}]->(p:Producto)',
        {
          productoId: producto.id,
          ordenId: orden.properties.idOrden,
          cantidad: producto.cantidad,
          precio: producto.precio,
          total: producto.total
        }
      );
    }

    res.status(201).json({ message: 'Venta creada con éxito', idOrden: orden.properties.idOrden });

  } catch (error) {
    console.error('Error al crear la venta en Neo4j:', error);
    res.status(500).json({ message: 'Error al crear la venta' });
  } finally {
    await session.close(); // Cerrar la sesión de Neo4j
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

module.exports = { getVentas, getClientes, getProductos, closeDriver, createVenta };