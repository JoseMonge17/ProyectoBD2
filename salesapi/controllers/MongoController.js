// server/controllers/ventasController.js

const { MongoClient, ObjectId } = require('mongodb');

const fs = require('fs');
const { spawn } = require('child_process');
const path = require('path');

const MONGO_URI = 'mongodb+srv://jmonge18:Jjmb260505@micluster.aqjfniv.mongodb.net/?appName=MiCluster'; // ajusta si usas Atlas u otra URI
const MONGO_DB_NAME = 'Ventas'; 

const LOG_PATH = 'E:/BD2/Proyecto/ProyectoBD2/Mongo/log.json'; 
const PYTHON_SCRIPT_PATH = 'E:/BD2/Proyecto/ProyectoBD2/Mongo/ETLMongo.py';
const PYTHON_COMMAND = 'python';

let mongoClient;
let db;

async function getDb() {
  if (!mongoClient) {
    mongoClient = new MongoClient(MONGO_URI);
    await mongoClient.connect();
    db = mongoClient.db(MONGO_DB_NAME);
    console.log('✅ Conectado a MongoDB:', MONGO_URI, 'DB:', MONGO_DB_NAME);
  }
  return db;
}

function parseFechaCarga(fechaStr) {
  if (!fechaStr) return null;

  // 👉 Caso 1: Formato ISO de Mongo (2025-11-21T18:36:25.182606Z)
  if (fechaStr.includes("T")) {
    const d = new Date(fechaStr);
    return isNaN(d.getTime()) ? null : d;
  }

  // 👉 Caso 2: Formato antiguo "YYYY-MM-DD HH:mm:SS"
  try {
    const [datePart, timePart] = fechaStr.split(" ");
    const [year, month, day] = datePart.split("-").map(Number);
    const [hour, minute, second] = timePart.split(":").map(Number);
    const d = new Date(year, month - 1, day, hour, minute, second || 0);
    return isNaN(d.getTime()) ? null : d;
  } catch {
    return null;
  }
}

// Función para obtener las ventas desde Mongo
const getVentas = async (req, res) => {
  console.log("Extrayendo ventas (Mongo)");
  try {
    const db = await getDb();
    const ordenesCol = db.collection('Ordenes');
    const clientesCol = db.collection('Clientes');

    // 🔹 Leer log.json desde el disco
    let fechaLimiteDate = null;
    try {
      const rawLog = fs.readFileSync(LOG_PATH, 'utf8');
      const logJson = JSON.parse(rawLog); // { last_id, fechaCarga }

      if (logJson.fechaCarga === "") {
        logJson.fechaCarga = "2000-11-23 18:28:55";
      }
      fechaLimiteDate = parseFechaCarga(logJson.fechaCarga);
      console.log('Fecha límite desde log.json:', logJson.fechaCarga, fechaLimiteDate);
    } catch (e) {
      console.warn('No se pudo leer log.json, no se aplicará lógica de edición:', e.message);
    }

    // 👇 Traemos órdenes + nombre del cliente
    const pipeline = [
      {
        $lookup: {
          from: 'Clientes',
          localField: 'cliente_id',
          foreignField: '_id',
          as: 'clienteDoc'
        }
      },
      { $unwind: { path: '$clienteDoc', preserveNullAndEmptyArrays: true } },
      { $sort: { fecha: 1 } }, // o por _id, como prefieras
    ];

    const docs = await ordenesCol.aggregate(pipeline).toArray();

    const ventas = docs.map(doc => {
      const fechaVenta = doc.fecha instanceof Date ? doc.fecha : new Date(doc.fecha);
      let puedeEditar = false;
      if (fechaLimiteDate && !isNaN(fechaVenta.getTime())) {
        puedeEditar = fechaVenta > fechaLimiteDate;
      }
      
      return {
        id: doc._id.toString(),                 // 👈 ID que usa el front
        fecha: doc.fecha,                       // Date -> se serializa a ISO
        total: doc.total || 0,
        moneda: doc.moneda || 'CRC',
        canal: doc.canal || '',
        cliente: doc.clienteDoc?.nombre || '',  // nombre cliente
        puedeEditar,
      };
    });

    res.json(ventas);
  } catch (error) {
    console.error('Error al obtener las ventas (Mongo):', error);
    res.status(500).json({
      message: 'Error al obtener las ventas',
      error: error.message
    });
  }
};

// Funcion para obtener los datos de una venta en concreto
const getVentaById = async (req, res) => {
  const { id } = req.params;
  console.log('Obteniendo venta por id (Mongo):', id);

  try {
    const db = await getDb();
    const ordenesCol = db.collection('Ordenes');
    const clientesCol = db.collection('Clientes');
    const productosCol = db.collection('Productos');

    const oid = new ObjectId(id);

    const orden = await ordenesCol.findOne({ _id: oid });
    if (!orden) {
      return res.status(404).json({ message: 'Venta no encontrada' });
    }

    const cliente = await clientesCol.findOne({ _id: orden.cliente_id });
    const items = orden.items || [];

    const productoIds = items.map(it => it.producto_id).filter(Boolean);
    const productosDocs = await productosCol
      .find({ _id: { $in: productoIds } })
      .toArray();

    const productos = items.map(item => {
      const prodDoc = productosDocs.find(p => p._id.equals(item.producto_id));

      return {
        producto: {
          idProducto: prodDoc?._id.toString(),
          nombre: prodDoc?.nombre || '',
          categoria: prodDoc?.categoria || '',
          codigo_mongo: prodDoc?.codigo_mongo || '',
        },
        relacion: {
          tipo: 'ITEM',
          propiedades: {
            cantidad: item.cantidad,
            precio: item.precio_unit,
          },
        },
      };
    });

    res.json({
      orden: {
        idOrden: orden._id.toString(),
        fecha: orden.fecha,
        total: orden.total,
        moneda: orden.moneda || 'CRC',
        canal: orden.canal || '',
        cupon: orden.metadatos?.cupon || null,
      },
      cliente: cliente
        ? {
            idCliente: cliente._id.toString(),
            nombre: cliente.nombre,
            telefono: cliente.telefono || '',
            correo: cliente.email || '',
          }
        : null,
      relacion_cliente_orden: null, // ya no aplica como en Neo4j
      productos,
    });
  } catch (error) {
    console.error('Error al obtener la venta (Mongo):', error);
    res.status(500).json({
      message: 'Error al obtener la venta',
      error: error.message,
    });
  }
};

const createVentas = async (req, res) => {
  console.log('Crear venta (Mongo) body:', req.body);
  const { cliente, canal, productos, cupon } = req.body;

  try {
    const db = await getDb();
    const ordenesCol = db.collection('Ordenes');

    const fechaActual = new Date();

    const items = (productos || []).map(p => {
      const cantidad = parseInt(p.cantidad, 10) || 0;
      const precio = parseInt(p.precio, 10) || 0;
      return {
        producto_id: new ObjectId(p.id),
        cantidad,
        precio_unit: precio,
      };
    });

    const totalOrden = items.reduce(
      (acc, it) => acc + (it.cantidad * it.precio_unit),
      0
    );

    const doc = {
      cliente_id: new ObjectId(cliente),
      fecha: fechaActual,
      canal: canal || '',
      moneda: 'CRC',          // 👈 fijo CRC
      total: totalOrden,
      items,
    };

    if (cupon && cupon.trim() !== '') {
      doc.metadatos = {
        cupon: cupon.trim(),
      };
    }

    const result = await ordenesCol.insertOne(doc);

    res.status(201).json({
      message: 'Venta creada con éxito',
      idOrden: result.insertedId.toString(),
      fecha: fechaActual.toISOString(),
    });
  } catch (error) {
    console.error('Error al crear la venta (Mongo):', error);
    res.status(500).json({
      message: 'Error al crear la venta',
      error: error.message,
    });
  }
};

const updateVenta = async (req, res) => {
  const { id } = req.params;
  const { cliente, canal, productos, cupon } = req.body;

  console.log('Actualizar venta (Mongo):', id, req.body);

  try {
    const db = await getDb();
    const ordenesCol = db.collection('Ordenes');

    const oid = new ObjectId(id);

    const existe = await ordenesCol.findOne({ _id: oid });
    if (!existe) {
      return res.status(404).json({ message: `Venta con id ${id} no encontrada` });
    }

    const items = (productos || []).map(p => {
      const cantidad = parseInt(p.cantidad, 10) || 0;
      const precio = parseInt(p.precio, 10) || 0;
      return {
        producto_id: new ObjectId(p.id),
        cantidad,
        precio_unit: precio,
      };
    });

    const totalOrden = items.reduce(
      (acc, it) => acc + (it.cantidad * it.precio_unit),
      0
    );

    const updateDoc = {
      $set: {
        cliente_id: new ObjectId(cliente),
        canal: canal || '',
        moneda: 'CRC',
        total: totalOrden,
        items,
      },
      $unset: {},
    };

    if (cupon && cupon.trim() !== '') {
      updateDoc.$set['metadatos'] = { cupon: cupon.trim() };
    } else {
      updateDoc.$unset['metadatos'] = '';
    }

    await ordenesCol.updateOne({ _id: oid }, updateDoc);

    res.json({
      message: 'Venta actualizada con éxito',
      idOrden: id,
      total: totalOrden,
    });
  } catch (error) {
    console.error('Error al actualizar la venta (Mongo):', error);
    res.status(500).json({
      message: 'Error al actualizar la venta',
      error: error.message,
    });
  }
};

const deleteVenta = async (req, res) => {
  const { id } = req.params;
  console.log('Eliminar venta (Mongo):', id);

  try {
    const db = await getDb();
    const ordenesCol = db.collection('Ordenes');

    const oid = new ObjectId(id);
    const result = await ordenesCol.deleteOne({ _id: oid });

    if (result.deletedCount === 0) {
      return res.status(404).json({ message: `No se encontró la venta con id ${id}` });
    }

    res.json({ message: `Venta ${id} eliminada correctamente` });
  } catch (error) {
    console.error('Error al eliminar la venta (Mongo):', error);
    res.status(500).json({
      message: 'Error al eliminar la venta',
      error: error.message,
    });
  }
};

const getClientes = async (req, res) => {
  console.log("Extrayendo clientes (Mongo)");
  try {
    const db = await getDb();
    const clientesCol = db.collection('Clientes');

    const docs = await clientesCol
      .find({}, { projection: { nombre: 1 } })
      .toArray();

    const clientes = docs.map(c => ({
      nombre: c.nombre,
      id: c._id.toString(),
    }));

    res.json(clientes);
  } catch (error) {
    console.error('Error al obtener los clientes (Mongo):', error);
    res.status(500).json({
      message: 'Error al obtener los clientes',
      error: error.message,
    });
  }
};

const getProductos = async (req, res) => {
  console.log("Extrayendo productos (Mongo)");
  try {
    const db = await getDb();
    const productosCol = db.collection('Productos');

    const docs = await productosCol
      .find({}, { projection: { nombre: 1 } })
      .toArray();

    const productos = docs.map(p => ({
      nombre: p.nombre,
      id: p._id.toString(),
    }));

    res.json(productos);
  } catch (error) {
    console.error('Error al obtener los productos (Mongo):', error);
    res.status(500).json({
      message: 'Error al obtener los productos',
      error: error.message,
    });
  }
};

const closeDriver = async () => {
  if (mongoClient) {
    await mongoClient.close();
    console.log('🔌 Conexión a Mongo cerrada');
  }
};

const ejecutarETL = async (req, res) => {
  console.log('🔄 Iniciando proceso ETL...');
  console.log('📂 Script:', PYTHON_SCRIPT_PATH);

  if (!fs.existsSync(PYTHON_SCRIPT_PATH)) {
    return res.status(404).json({
      message: 'Script ETL no encontrado',
      path: PYTHON_SCRIPT_PATH
    });
  }

  try {
    const pythonProcess = spawn(PYTHON_COMMAND, [PYTHON_SCRIPT_PATH]);

    let stdoutData = '';
    let stderrData = '';

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('📤 Python stdout:', output);
      stdoutData += output;
    });

    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      console.error('❌ Python stderr:', error);
      stderrData += error;
    });

    pythonProcess.on('close', (code) => {
      console.log(`🏁 Proceso ETL terminado con código: ${code}`);

      if (code === 0) {
        res.json({
          success: true,
          message: 'ETL ejecutado exitosamente',
          output: stdoutData,
          exitCode: code
        });
      } else {
        res.status(500).json({
          success: false,
          message: 'El proceso ETL finalizó con errores',
          error: stderrData || stdoutData,
          exitCode: code
        });
      }
    });

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