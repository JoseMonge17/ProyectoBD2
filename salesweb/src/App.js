// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; // Usar Routes en lugar de Switch
import HomePage from './HomePage';
import VentasNeo4j from './Neo4j/CrudPage';
import CrearVentaNeo4j from './Neo4j/CrearVenta'; // Asegúrate de importar VentasPage
import ListVentas from "./Supabase/ListVentas";
import CreateVenta from "./Supabase/CreateVentas";

function App() {
  return (
    <Router>
      <Routes>
        {/* Ruta principal */}
        <Route path="/" element={<HomePage />} />
        
        {/* Ruta para la página de ventas de Neo4j */}
        <Route path="/ventasNeo4j" element={<VentasNeo4j />} />
        <Route path="/ventasNeo4j/crear" element={<CrearVentaNeo4j />} />

        <Route path="/ventasSupabase" element={<ListVentas />} />
        <Route path="/crearVentaSupabase" element={<CreateVenta />} />
      </Routes>
    </Router>
  );
}

export default App;
