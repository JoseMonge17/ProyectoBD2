// src/HomePage.js
import React from 'react';
import './HomePage.css'; // Importamos los estilos
import { Link } from 'react-router-dom'; // Importamos Link de react-router-dom

const HomePage = () => {
    return (
        <div className="home-container">
            <header className="home-header">
                <h1>Bienvenido al Proyecto de Gestión de Datos</h1>
                <p>
                    Aquí podrás acceder a distintas herramientas para gestionar y cargar datos en diversas bases de datos.
                </p>
            </header>
            
            <div className="options-container">
                <button className="option-btn">CRUD Ventas de Supabase</button>
                <Link to="/ventasNeo4j">
                    <button className="option-btn">CRUD Ventas de Neo4j</button>
                </Link>
                <button className="option-btn">CRUD Ventas de MongoDB</button>
                <button className="option-btn">Loader de MySQL</button>
                <button className="option-btn">Loader de SQL Server</button>
            </div>
        </div>
    );
};

export default HomePage;
