// src/pages/ListDetalles.js
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./styles.css";

const ListDetalles = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    const [orden, setOrden] = useState(null);
    const [detalles, setDetalles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadDetalles();
    }, []);

    const loadDetalles = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://127.0.0.1:8000/ordenes/${id}`);

            if (!response.ok) {
                throw new Error("No se pudo obtener los detalles de la orden");
            }

            const data = await response.json();
            setOrden(data.orden);
            setDetalles(data.detalles);
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <button
                style={{ backgroundColor: "#9e9e9e" }}
                onClick={() => navigate("/ventasSupabase")}
            >
                ← Volver
            </button>

            <h2>Detalles de la Orden</h2>

            {loading ? (
                <p>Cargando...</p>
            ) : error ? (
                <p style={{ color: "red" }}>{error}</p>
            ) : (
                <>
                    {/* INFO GENERAL */}
                    <div className="info-box">
                        <p><strong>ID Orden:</strong> {orden.orden_id}</p>
                        <p><strong>ID Cliente:</strong> {orden.cliente_id}</p>
                        <p><strong>Cliente:</strong> {orden.cliente_nombre}</p>
                        <p><strong>Fecha:</strong> {new Date(orden.fecha).toLocaleString()}</p>
                        <p><strong>Canal:</strong> {orden.canal}</p>
                        <p><strong>Moneda:</strong> {orden.moneda}</p>
                        <p><strong>Total:</strong> {orden.total}</p>
                    </div>

                    <h3>Items</h3>

                    <div className="scroll-table">
                        <table className="ventas-table">
                            <thead>
                                <tr>
                                    <th>ID Detalle</th>
                                    <th>Producto</th>
                                    <th>Cantidad</th>
                                    <th>Precio</th>
                                </tr>
                            </thead>
                            
                            <tbody>
                                {detalles.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" style={{ textAlign: "center" }}>
                                            No hay detalles
                                        </td>
                                    </tr>
                                ) : (
                                    detalles.map((d) => (
                                        <tr key={d.orden_detalle_id}>
                                            <td>{d.orden_detalle_id}</td>
                                            <td>{d.producto_nombre}</td>
                                            <td>{d.cantidad}</td>
                                            <td>{d.precio_unit}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
};

export default ListDetalles;
