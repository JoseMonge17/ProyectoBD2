// server/routes/ventasRoutes.js
const express = require('express');
const router = express.Router();
const { getVentas, getClientes, getProductos, createVentas, getVentaById } = require('../controllers/Neo4JController'); // Importamos el controlador

// Definir las rutas para ventas
router.get('/', getVentas);
router.post('/', createVentas);
router.get('/:id', getVentaById);

// Definir las rutas para clientes
router.get('/clientes', getClientes);

// Definir las rutas para productos
router.get('/productos', getProductos);

module.exports = router;
