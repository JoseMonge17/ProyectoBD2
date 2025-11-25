// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; // Usar Routes en lugar de Switch
import HomePage from './HomePage';
import CrearVentaNeo4j from './Neo4j/CrearVenta';
import EditarVentaNeo4j from './Neo4j/EditarVenta';
import OrdersPageNeo4j from './Neo4j/OrdersPage';
import CrearVentaMongo from './Mongo/CrearVenta';
import EditarVentaMongo from './Mongo/EditarVenta';
import OrdersPageMongo from './Mongo/OrdersPage';
import ListVentas from "./Supabase/ListVentas";
import CreateVenta from "./Supabase/CreateVentas";

function App() {
  return (
    <Router>
      <Routes>
        {/* Ruta principal */}
        <Route path="/" element={<HomePage />} />
        
        <Route path="/ventasNeo4j/crear" element={<CrearVentaNeo4j />} />
        <Route path="/ventasNeo4j/" element={<OrdersPageNeo4j />} />
        <Route path="/ventasNeo4j/editar/:id" element={<EditarVentaNeo4j />} />

        <Route path="/ventasMongo/crear" element={<CrearVentaMongo />} />
        <Route path="/ventasMongo/" element={<OrdersPageMongo />} />
        <Route path="/ventasMongo/editar/:id" element={<EditarVentaMongo />} />

        <Route path="/ventasSupabase" element={<ListVentas />} />
        <Route path="/crearVentaSupabase" element={<CreateVenta />} />
      </Routes>
    </Router>
  );
}

export default App;
