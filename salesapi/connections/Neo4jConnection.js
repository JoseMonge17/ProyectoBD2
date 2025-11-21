const neo4j = require('neo4j-driver');

// Configuración global de la conexión (similar a tu código en Python)
const URI = "bolt://localhost:7687"; // Cambia si estás usando otro puerto
const AUTH_USER = "neo4j";
const AUTH_PASS = "Jjmb260505*";
const DATABASE_NAME = "ventas"; // Base de datos que deseas usar

const driver = neo4j.driver(
  'bolt://127.0.0.1:7687', // Cambiar localhost a 127.0.0.1
  neo4j.auth.basic('neo4j', 'Jjmb260505*'), // Credenciales de Neo4j
  { database: 'ventas' } // Base de datos 'ventas'
);

// Función para obtener el driver
const getDriver = () => {
  return driver;
};

module.exports = { getDriver };
