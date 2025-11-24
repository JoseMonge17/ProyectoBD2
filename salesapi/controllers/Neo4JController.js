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
        'ORDER BY o.idOrden ASC '
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

module.exports = { getVentas, getClientes, getProductos, closeDriver, createVentas, getVentaById };