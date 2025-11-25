// server/server.js
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const mongoose = require('mongoose');
const neo4j = require('neo4j-driver');
const AprioriRoutes = require('./routes/AprioriRoutes');

const app = express();
const port = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Importar rutas
const mongoRoutes = require('./routes/MongoRoutes');
const neo4jRoutes = require('./routes/Neo4jRoutes');

// Usar las rutas
app.use('/api/mongo', mongoRoutes);
app.use('/api/neo4j', neo4jRoutes);

// Iniciar servidor
app.listen(port, () => {
  console.log(`Servidor corriendo en http://localhost:${port}`);
});
