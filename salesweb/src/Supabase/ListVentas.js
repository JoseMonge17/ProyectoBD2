// src/pages/ListaVentas.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles.css";

const ListVentas = () => {
    const [ventas, setVentas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        loadVentas();
    }, []);

    const loadVentas = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch("http://127.0.0.1:8000/ordenes");
            if (!response.ok) {
                throw new Error("Error al obtener las ventas");
            }
            const data = await response.json();
            const mapped = data.map((v) => ({
                id: v.orden_id,
                fecha: new Date(v.fecha).toLocaleString(),
                cliente: v.cliente_nombre,
                total: v.total,
                moneda: v.moneda,
                canal: v.canal
            }));
            setVentas(mapped);
        } catch (err) {
            console.error(err);
            setError(err.message || "Error desconocido");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <button
                style={{ backgroundColor: "#9e9e9e" }}
                onClick={() => navigate("/")}
            >
                ← Volver
            </button>

            <h2>Listado de Ventas</h2>

            <button
                style={{ backgroundColor: "#2196f3" }}
                onClick={() => navigate("/crearVentaSupabase")}
            >
                + Nueva Venta
            </button>

            {loading ? (
                <p>Cargando ventas...</p>
            ) : error ? (
                <p style={{ color: "red" }}>{error}</p>
            ) : (
                <div className="scroll-table">
                    <table className="ventas-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>ID</th>
                                <th>Fecha</th>
                                <th>Cliente</th>
                                <th>Total</th>
                                <th>Moneda</th>
                                <th>Canal</th>
                            </tr>
                        </thead>

                        <tbody>
                            {ventas.length === 0 ? (
                                <tr>
                                    <td colSpan="7" style={{ textAlign: "center", padding: "20px" }}>
                                        No hay ventas registradas
                                    </td>
                                </tr>
                            ) : (
                                ventas.map((v, index) => (
                                    <tr key={v.id}>
                                        <td>{index + 1}</td>
                                        <td>{v.id}</td>
                                        <td>{v.fecha}</td>
                                        <td>{v.cliente}</td>
                                        <td>{v.total}</td>
                                        <td>{v.moneda}</td>
                                        <td>{v.canal}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default ListVentas;