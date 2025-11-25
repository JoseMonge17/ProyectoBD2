// server/routes/ventasRoutes.js
const express = require('express');
const router = express.Router();
const { getVentas, getClientes, getProductos, createVentas, getVentaById, updateVenta, deleteVenta, ejecutarETL} = require('../controllers/MongoController'); // Importamos el controlador

// Definir las rutas para ventas
router.get('/ventas', getVentas);
router.post('/ventas', createVentas);
router.get('/ventas/:id', getVentaById);
router.put('/ventas/:id', updateVenta);
router.delete('/ventas/:id', deleteVenta);

// Definir la ruta para clientes
router.get('/clientes', getClientes);

// Definir la ruta para productos
router.get('/productos', getProductos);

// Definar la ruta para ejecutar ETL
router.post('/etl', ejecutarETL);

module.exports = router;
