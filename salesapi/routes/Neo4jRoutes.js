// server/routes/ventasRoutes.js
const express = require('express');
const router = express.Router();
const { getVentas } = require('../controllers/Neo4JController'); // Importamos el controlador

// Definir la ruta para obtener las ventas
router.get('/', getVentas);

module.exports = router;
