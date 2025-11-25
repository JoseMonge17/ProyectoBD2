// src/pages/ListaVentas.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles.css";

const ListVentas = () => {
    const [ventas, setVentas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Estados para el popup
    const [showConfirm, setShowConfirm] = useState(false);
    const [ventaAEliminar, setVentaAEliminar] = useState(null);
    const [deleting, setDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState(null);
    const [search, setSearch] = useState("");


    const navigate = useNavigate();

    useEffect(() => {
        loadVentas();
    }, []);

    const filteredVentas = ventas.filter(v => {
        const s = search.toLowerCase();

        return (
            v.id.toLowerCase().includes(s) ||
            v.fecha.toLowerCase().includes(s) ||
            v.cliente.toLowerCase().includes(s) ||
            v.canal.toLowerCase().includes(s) ||
            v.moneda.toLowerCase().includes(s)
        );
    });


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

    // Funciones del popup
    const confirmarEliminacion = (id) => {
        setVentaAEliminar(id);
        setShowConfirm(true);
    };

    const cancelarEliminacion = () => {
        setShowConfirm(false);
        setVentaAEliminar(null);
    };

    async function ejecutarETL() {
        const res = await fetch("http://127.0.0.1:8000/ejecutar-etl", {
            method: "POST"
        });

        const data = await res.json();
        console.log(data);

        if (data.status === "success") {
            alert("ETL ejecutado correctamente");
        } else {
            alert("Error ejecutando ETL");
        }
    }

    const eliminarVenta = async () => {
        if (!ventaAEliminar) return;

        setDeleting(true);
        setDeleteError(null);

        try {
            const res = await fetch(`http://127.0.0.1:8000/ordenes/${ventaAEliminar}`, {
                method: "DELETE",
            });

            // Si el backend retorna JSON con mensaje
            let payload = null;
            try {
                payload = await res.json();
            } catch (e) {
                // si no viene JSON, ok
            }

            if (!res.ok) {
                // mostrar detalle si lo hay, sino un mensaje genérico
                const detail = payload?.detail || payload?.mensaje || `Error ${res.status}`;
                throw new Error(detail);
            }

            // Éxito: recargar la lista
            await loadVentas();

            // Cerrar modal
            setShowConfirm(false);
            setVentaAEliminar(null);

        } catch (err) {
            console.error("Error eliminando venta:", err);
            setDeleteError(err.message || "Error desconocido al eliminar");
            // opcional: avisar al usuario
            alert("No se pudo eliminar: " + (err.message || "Error desconocido"));
        } finally {
            setDeleting(false);
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

            <button style={{ backgroundColor: "#9e9e9e" }} onClick={ejecutarETL}>
                Ejecutar ETL
            </button>

            <h2>Listado de Ventas</h2>

            <button
                style={{ backgroundColor: "#2196f3" }}
                onClick={() => navigate("/crearVentaSupabase")}
            >
                + Nueva Venta
            </button>

            <div style={{ marginTop: "20px", marginBottom: "10px" }}>
                <input
                    type="text"
                    placeholder="Buscar por ID, fecha, cliente, canal o moneda..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{
                        width: "100%",
                        padding: "10px",
                        borderRadius: "6px",
                        border: "1px solid #ccc",
                        fontSize: "16px"
                    }}
                />
            </div>


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
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        

                        <tbody>
                            {filteredVentas.length === 0 ? (
                                <tr>
                                    <td colSpan="8" style={{ textAlign: "center", padding: "20px" }}>
                                        No hay ventas registradas
                                    </td>
                                </tr>
                            ) : (
                                filteredVentas.map((v, index) => (
                                    <tr key={v.id}>
                                        <td>{index + 1}</td>
                                        <td>{v.id}</td>
                                        <td>{v.fecha}</td>
                                        <td>{v.cliente}</td>
                                        <td>{v.total}</td>
                                        <td>{v.moneda}</td>
                                        <td>{v.canal}</td>

                                        {/* NUEVA COLUMNA DE ACCIONES */}
                                        <td>
                                            <button
                                                style={{ backgroundColor: "#4caf50" }}
                                                onClick={() => navigate(`/detallesVentaSupabase/${v.id}`)}
                                            >
                                                Ver
                                            </button>

                                            <button
                                                style={{ backgroundColor: "#ff9800" }}
                                                onClick={() => navigate(`/editarVentaSupabase/${v.id}`)}
                                            >
                                                Editar
                                            </button>

                                            <button
                                                style={{ backgroundColor: "#f44336" }}
                                                onClick={() => confirmarEliminacion(v.id)}
                                            >
                                                Eliminar
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {/* POPUP DE CONFIRMACIÓN */}
            {showConfirm && (
                <div className="modal-overlay">
                    <div className="modal-box">
                        <h3>¿Eliminar venta?</h3>
                        <p>¿Seguro que deseas eliminar la venta con ID:</p>
                        <p style={{ fontWeight: "bold" }}>{ventaAEliminar}</p>

                        <div className="modal-actions">
                            <button
                                style={{ backgroundColor: "#9e9e9e" }}
                                onClick={cancelarEliminacion}
                            >
                                Cancelar
                            </button>

                            <button
                                style={{ backgroundColor: "#f44336" }}
                                onClick={eliminarVenta}
                            >
                                Confirmar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ListVentas;
