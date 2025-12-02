// server/server.js
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const mongoose = require('mongoose');
const neo4j = require('neo4j-driver');
const { updateExchangeRate } = require("./jobs/tipoCambioJob");


const app = express();
const port = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Importar rutas
const mongoRoutes = require('./routes/MongoRoutes');
const neo4jRoutes = require('./routes/Neo4jRoutes');
const aprioriRoutes = require('./routes/AprioriRoutes');
const sqlServerRoutes = require('./routes/SQLServerRoutes');
const mySqlRoutes = require('./routes/MySQLRouter');

// Usar las rutas
app.use('/api/mongo', mongoRoutes);
app.use('/api/neo4j', neo4jRoutes);
app.use('/api/apriori', aprioriRoutes);
app.use('/api/sqlserver', sqlServerRoutes);
app.use('/api/mysql', mySqlRoutes);

// Iniciar servidor
app.listen(port, () => {
  console.log(`Servidor corriendo en http://localhost:${port}`);
  // Cargar Job del tipo de cambio
  console.log("⏳ Job de tipo de cambio cargado. Se ejecutará automáticamente a las 5 a.m.");
});


