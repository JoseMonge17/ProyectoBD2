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

// Función para cerrar el driver cuando la aplicación termine
const closeDriver = async () => {
  await driver.close();
};

module.exports = { getVentas, closeDriver };