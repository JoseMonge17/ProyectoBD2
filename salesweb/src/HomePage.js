// src/HomePage.js
import React from 'react';
import './HomePage.css';
import { Link } from 'react-router-dom';

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
                <Link to="/ventasSupabase">
                    <button className="option-btn">CRUD Ventas de Supabase</button>
                </Link>
                <Link to="/ventasNeo4j">
                    <button className="option-btn">CRUD Ventas de Neo4j</button>
                </Link>
                <Link to="/ventasMongo">
                    <button className="option-btn">CRUD Ventas de MongoDB</button>
                </Link>
                <Link to="/mysql/loader">
                    <button className="option-btn">Loader de MySQL</button>
                </Link>
                <Link to="/sqlserver/loader">
                    <button className="option-btn">Loader de SQL Server</button>
                </Link>
            </div>
        </div>
    );
};

export default HomePage;