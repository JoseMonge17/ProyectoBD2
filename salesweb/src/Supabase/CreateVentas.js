// src/pages/CrearVenta.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles.css";

const CreateVenta = () => {
    const navigate = useNavigate();

    // Datos generales de la venta
    const [venta, setVenta] = useState({
        cliente: "",
        canal: "",
    });

    // Producto actual
    const [productoActual, setProductoActual] = useState({
        nombre: "",
        cantidad: 1,
        precio: 0,
        moneda: "USD",
    });

    // Lista de productos agregados
    const [detalle, setDetalle] = useState([]);

    const handleVentaChange = (e) => {
        const { name, value } = e.target;
        setVenta({ ...venta, [name]: value });
    };

    const handleProductoChange = (e) => {
        const { name, value } = e.target;
        setProductoActual({ ...productoActual, [name]: value });
    };

    const agregarProducto = () => {
        if (!productoActual.nombre || productoActual.precio <= 0) return;

        setDetalle([...detalle, productoActual]);

        setProductoActual({
            nombre: "",
            cantidad: 1,
            precio: 0,
            moneda: productoActual.moneda,
        });
    };

    const cancelar = () => navigate("/ventasSupabase");

    const realizarVenta = () => {
        const total = detalle.reduce(
            (acc, p) => acc + p.precio * p.cantidad,
            0
        );

        const nuevaVenta = {
            ...venta,
            total,
            fecha: new Date().toISOString().split("T")[0],
            productos: detalle,
        };

        console.log("Venta creada (MOCK): ", nuevaVenta);

        navigate("/ventasSupabase");
    };

    return (
        <div className="container">
            <h2>Registrar Nueva Venta</h2>

            {/* DATOS GENERALES */}
            <div className="subcard">
                <h3>Datos Generales</h3>

                <label>Cliente:</label>
                <input
                    type="text"
                    name="cliente"
                    placeholder="Nombre del cliente"
                    value={venta.cliente}
                    onChange={handleVentaChange}
                />

                <label>Canal:</label>
                <input
                    type="text"
                    name="canal"
                    placeholder="Ej: Online, Tienda, WhatsApp"
                    value={venta.canal}
                    onChange={handleVentaChange}
                />
            </div>

            {/* PRODUCTOS */}
            <div className="subcard">
                <h3>Agregar Productos</h3>

                <label>Producto:</label>
                <input
                    type="text"
                    name="nombre"
                    placeholder="Nombre del producto"
                    value={productoActual.nombre}
                    onChange={handleProductoChange}
                />

                <label>Cantidad:</label>
                <input
                    type="number"
                    name="cantidad"
                    value={productoActual.cantidad}
                    onChange={handleProductoChange}
                />

                <label>Precio:</label>
                <input
                    type="number"
                    name="precio"
                    value={productoActual.precio}
                    onChange={handleProductoChange}
                />

                <label>Moneda:</label>
                <select
                    name="moneda"
                    value={productoActual.moneda}
                    onChange={handleProductoChange}
                >
                    <option value="USD">USD</option>
                    <option value="CRC">CRC</option>
                </select>

                <button
                    style={{ background: "#4caf50" }}
                    onClick={agregarProducto}
                >
                    + Insertar Producto
                </button>

                {/* TABLA DETALLE */}
                {detalle.length > 0 && (
                    <table style={{ marginTop: "20px" }}>
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Cant</th>
                                <th>Precio</th>
                                <th>Moneda</th>
                                <th>Subtotal</th>
                            </tr>
                        </thead>

                        <tbody>
                            {detalle.map((p, i) => (
                                <tr key={i}>
                                    <td>{p.nombre}</td>
                                    <td>{p.cantidad}</td>
                                    <td>{p.precio}</td>
                                    <td>{p.moneda}</td>
                                    <td>{p.precio * p.cantidad}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* BOTONES */}
            <button
                style={{ background: "#9e9e9e" }}
                onClick={cancelar}
            >
                Cancelar
            </button>

            <button
                style={{ background: "#2196f3" }}
                onClick={realizarVenta}
                disabled={detalle.length === 0 || !venta.cliente}
            >
                Realizar Venta
            </button>
        </div>
    );
};

export default CreateVenta;
