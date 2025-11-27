const express = require('express');
const { MongoClient, ObjectId } = require('mongodb'); // ← ObjectId aquí
const router = express.Router();

const MONGO_URI = 'mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/?appName=MiCluster';

let mongoClient;

async function getDb() {
  if (!mongoClient) {
    mongoClient = new MongoClient(MONGO_URI);
    await mongoClient.connect();
    console.log('✅ Conectado a MongoDB para recomendaciones');
  }
  return mongoClient.db('Recomendaciones');
}

async function getVentasDb() {
  return mongoClient.db('Ventas');
}

router.get('/recomendaciones/:productoId', async (req, res) => {
  const { productoId } = req.params;
  console.log('Buscando recomendaciones para producto:', productoId);

  try {
    const db = await getDb();
    const ventasDb = await getVentasDb();
    const reglasCol = db.collection('reglas_apriori');
    const productosCol = ventasDb.collection('Productos');

    // 1. Obtener las reglas de asociación
    const reglas = await reglasCol.find({
      antecedents: { $in: [productoId] },
      fuente: 'mongo'
    })
    .sort({ confidence: -1 })
    .limit(10)
    .toArray();

    console.log(`Encontradas ${reglas.length} reglas para producto ${productoId}`);

    if (reglas.length === 0) {
      return res.json({ 
        productoId,
        recomendaciones: []
      });
    }

    // 2. Extraer todos los IDs de productos recomendados
    const productosRecomendadosIds = [];
    const productosVistos = new Set();
    
    reglas.forEach(regla => {
      const productoRecomendadoId = regla.consequents[0];
      if (!productosVistos.has(productoRecomendadoId)) {
        productosVistos.add(productoRecomendadoId);
        productosRecomendadosIds.push(productoRecomendadoId);
      }
    });

    // 3. Obtener los nombres de los productos recomendados - CORREGIDO
    const productosRecomendados = await productosCol.find({
      _id: { $in: productosRecomendadosIds.map(id => new ObjectId(id)) } // ← ObjectId aquí
    }).toArray();

    // 4. Crear mapa de ID -> nombre
    const productosMap = {};
    productosRecomendados.forEach(prod => {
      productosMap[prod._id.toString()] = prod.nombre;
    });

    // 5. Construir respuesta con nombres
    const recomendaciones = reglas.map(regla => {
      const productoRecomendadoId = regla.consequents[0];
      return {
        productoId: productoRecomendadoId,
        nombre: productosMap[productoRecomendadoId] || 'Producto no encontrado',
        confidence: Math.round(regla.confidence * 100), // Porcentaje
        lift: Math.round(regla.lift * 100) / 100, // 2 decimales
        support: Math.round(regla.support * 1000) / 10 // Porcentaje con 1 decimal
      };
    });

    // 6. Obtener también el nombre del producto original - CORREGIDO
    const productoOriginal = await productosCol.findOne({
      _id: new ObjectId(productoId) // ← ObjectId aquí
    });

    res.json({ 
      productoId,
      productoNombre: productoOriginal?.nombre || 'Producto no encontrado',
      recomendaciones: recomendaciones
    });

  } catch (error) {
    console.error('Error al obtener recomendaciones:', error);
    res.status(500).json({
      message: 'Error al obtener recomendaciones',
      error: error.message
    });
  }
});

module.exports = router;