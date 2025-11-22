// src/CrudPage.js
import React from 'react';
import { Link } from 'react-router-dom';
import './CrudPage.css';

const CrudPage = () => {
  return (
    <div className="crud-container">
      <header className="crud-header">
        <h1>Gestión de Ventas – Neo4j</h1>
        <p>
          Desde este panel puedes administrar las ventas almacenadas en Neo4j 
          y ejecutar el proceso de carga ETL hacia el Data Warehouse.
        </p>
      </header>

      <section className="crud-options">
        {/* Crear */}
        <Link to="/ventasNeo4j/crear" className="crud-card-link">
          <div className="crud-card">
            <h2>Crear Venta</h2>
            <p>
              Registrar una nueva venta en Neo4j, seleccionando cliente, productos, 
              moneda y canal, junto con el detalle de líneas de venta.
            </p>
          </div>
        </Link>

        {/* Buscar */}
        <Link to="/ventasNeo4j/buscar" className="crud-card-link">
          <div className="crud-card">
            <h2>Buscar Ventas</h2>
            <p>
              Consultar ventas existentes por rango de fechas, cliente, canal o moneda. 
              Ideal para revisión o auditoría rápida.
            </p>
          </div>
        </Link>

        {/* Actualizar */}
        <Link to="/ventasNeo4j/actualizar" className="crud-card-link">
          <div className="crud-card">
            <h2>Actualizar Venta</h2>
            <p>
              Modificar datos de ventas que aún no han sido cargadas al DW 
              (por ejemplo, corregir cantidades, precios o cliente).
            </p>
          </div>
        </Link>

        {/* Eliminar */}
        <Link to="/ventasNeo4j/eliminar" className="crud-card-link">
          <div className="crud-card crud-card-danger">
            <h2>Eliminar Venta</h2>
            <p>
              Eliminar ventas permitidas según las reglas del proyecto 
              (por ejemplo, solo aquellas que no hayan sido cargadas por el ETL).
            </p>
          </div>
        </Link>

        {/* Cargar ETL */}
        <Link to="/ventasNeo4j/etl" className="crud-card-link">
          <div className="crud-card crud-card-highlight">
            <h2>Cargar ETL</h2>
            <p>
              Ejecutar el proceso ETL para enviar las ventas de Neo4j 
              hacia el Data Warehouse en SQL Server u otros destinos.
            </p>
          </div>
        </Link>
      </section>
    </div>
  );
};

export default CrudPage;
