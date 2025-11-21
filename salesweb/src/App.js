// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; // Usar Routes en lugar de Switch
import HomePage from './HomePage';
import VentasNeo4j from './Neo4j/CrudPage'; // Asegúrate de importar VentasPage

function App() {
  return (
    <Router>
      <Routes>
        {/* Ruta principal */}
        <Route path="/" element={<HomePage />} />
        
        {/* Ruta para la página de ventas de Neo4j */}
        <Route path="/ventasNeo4j" element={<VentasNeo4j />} />
      </Routes>
    </Router>
  );
}

export default App;
