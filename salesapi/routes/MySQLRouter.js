const express = require('express');
const router = express.Router();
const { ejecutarLoader } = require('../controllers/MySQLController');

// Ruta para ejecutar el loader (ambos métodos)
router.post('/loader', ejecutarLoader);
router.get('/loader', ejecutarLoader); // ← Agregar GET también

module.exports = router;