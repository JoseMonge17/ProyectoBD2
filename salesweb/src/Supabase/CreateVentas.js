// src/pages/CrearVenta.js
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./styless.css";

// Función para redondear a 2 decimales
const round2 = (num) => Math.round(num * 100) / 100;

const CreateVenta = () => {
    const navigate = useNavigate();

    // ===============================
    // ESTADOS PARA LISTAS DE API
    // ===============================
    const [clientes, setClientes] = useState([]);
    const [productos, setProductos] = useState([]);

    // textos de búsqueda (inputs únicos)
    const [buscarCliente, setBuscarCliente] = useState("");
    const [buscarProducto, setBuscarProducto] = useState("");

    // control de dropdowns
    const [showClientesDropdown, setShowClientesDropdown] = useState(false);
    const [showProductosDropdown, setShowProductosDropdown] = useState(false);

    // refs para detectar click fuera
    const clienteRef = useRef(null);
    const productoRef = useRef(null);

    // ===============================
    // CARGAR DATOS DEL API
    // ===============================
    useEffect(() => {
        fetch("http://127.0.0.1:8000/clientes")
            .then(res => res.json())
            .then(data => setClientes(data))
            .catch(err => console.error("Error clientes:", err));

        fetch("http://127.0.0.1:8000/productos")
            .then(res => res.json())
            .then(data => setProductos(data))
            .catch(err => console.error("Error productos:", err));
    }, []);

    // cerrar dropdowns si se hace click fuera
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (clienteRef.current && !clienteRef.current.contains(e.target)) {
                setShowClientesDropdown(false);
            }
            if (productoRef.current && !productoRef.current.contains(e.target)) {
                setShowProductosDropdown(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // ===============================
    // DATOS GENERALES
    // ===============================
    const [venta, setVenta] = useState({
        cliente: "",
        canal: "",
        moneda: "USD",
    });

    const handleVentaChange = (e) => {
        const { name, value } = e.target;
        setVenta({ ...venta, [name]: value });
    };

    // -------------------------------
    // PRODUCTO ACTUAL
    // -------------------------------
    const [productoActual, setProductoActual] = useState({
        producto_id: "",
        nombre: "",
        cantidad: 1,
        precio: 0,
    });

    const handleProductoChange = (e) => {
        const { name, value } = e.target;
        // asegurar que cantidad sea número
        setProductoActual({
            ...productoActual,
            [name]: name === "cantidad" ? Number(value) : value,
        });
    };

    // Lista final
    const [detalle, setDetalle] = useState([]);

    const agregarProducto = () => {
        if (!productoActual.producto_id) {
            alert("Seleccione un producto válido.");
            return;
        }

        const precio = Number(productoActual.precio);

        if (isNaN(precio) || precio <= 0) {
            alert("El precio debe ser mayor a 0.");
            return;
        }

        const productoConMoneda = {
            ...productoActual,
            moneda: venta.moneda,
        };

        setDetalle([...detalle, productoConMoneda]);

        setProductoActual({
            producto_id: "",
            nombre: "",
            cantidad: 1,
            precio: 0,
        });

        setBuscarProducto("");
        setShowProductosDropdown(false);
    }

    const cancelar = () => navigate("/ventasSupabase");

    const totalFooter = round2(
        detalle.reduce((acc, p) => acc + (Number(p.precio) * Number(p.cantidad || 0)), 0)
    );

    const realizarVenta = async () => {
        if (!venta.cliente || detalle.length === 0) return;

        const total = round2(
            detalle.reduce((acc, p) => acc + (Number(p.precio) * Number(p.cantidad || 0)), 0)
        );

        const nuevaVenta = {
            cliente_id: venta.cliente,         // ← CAMPO CORRECTO
            canal: venta.canal,
            moneda: venta.moneda,
            total: total,
            detalles: detalle.map(p => ({
                producto_id: p.producto_id,
                cantidad: Number(p.cantidad),
                precio_unit: Number(p.precio)  // ← nombre correcto y convertido a número
            }))
        };

        console.log("JSON enviado:", nuevaVenta);

        try {
            const res = await fetch("http://127.0.0.1:8000/ordenes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(nuevaVenta),
            });

            if (!res.ok) {
                const err = await res.json();
                alert("Error al crear la orden: " + err.detail);
                return;
            }

            alert("Venta registrada correctamente.");
            navigate("/ventasSupabase");

        } catch (e) {
            alert("Error conectando al servidor: " + e.message);
        }
    };



    // ===============================
    // FILTRADOS EN VIVO
    // ===============================
    const clientesFiltrados = clientes.filter(c =>
        c.nombre.toLowerCase().includes(buscarCliente.toLowerCase())
    );

    const productosFiltrados = productos.filter(p =>
        p.nombre.toLowerCase().includes(buscarProducto.toLowerCase())
    );

    // seleccionar cliente -> guarda cliente_id en venta.cliente
    const seleccionarCliente = (c) => {
        setVenta({ ...venta, cliente: c.cliente_id });
        setBuscarCliente(c.nombre);
        setShowClientesDropdown(false);
    };

    // seleccionar producto -> llena productoActual.producto_id y nombre
    const seleccionarProducto = (p) => {
        setProductoActual({
            ...productoActual,
            producto_id: p.producto_id,
            nombre: p.nombre,
        });
        setBuscarProducto(p.nombre);
        setShowProductosDropdown(false);
    };

    return (
        <div className="create-container">
            <h2>Registrar Nueva Venta</h2>

            {/* DATOS GENERALES */}
            <div className="subcard">
                <h3>Datos Generales</h3>

                {/* ======================= CLIENTE (input único con dropdown) ======================== */}
                <label>Cliente:</label>
                <div ref={clienteRef} style={{ position: "relative", width: "100%" }}>
                    <input
                        type="text"
                        placeholder="Buscar cliente..."
                        value={buscarCliente}
                        onChange={(e) => {
                            setBuscarCliente(e.target.value);
                            setShowClientesDropdown(true);
                        }}
                        onFocus={() => setShowClientesDropdown(true)}
                        autoComplete="off"
                    />

                    {showClientesDropdown && buscarCliente.length > 0 && (
                        <div className="search-dropdown">
                            {clientesFiltrados.length === 0 ? (
                                <div className="dropdown-empty">No se encontraron clientes</div>
                            ) : (
                                clientesFiltrados.map((c) => (
                                    <div
                                        key={c.cliente_id}
                                        className="dropdown-item"
                                        onClick={() => seleccionarCliente(c)}
                                    >
                                        <div className="dd-main">{c.nombre}</div>
                                        <div className="dd-sub">{c.email}</div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>

                {/* ======================= CANAL ======================== */}
                <label>Canal:</label>
                <select
                    name="canal"
                    value={venta.canal}
                    onChange={handleVentaChange}
                >
                    <option value="">Seleccione canal</option>
                    <option value="WEB">WEB</option>
                    <option value="APP">APP</option>
                    <option value="PARTNER">PARTNER</option>
                </select>

                {/* ======================= MONEDA ======================== */}
                <label>Moneda:</label>
                <select
                    name="moneda"
                    value={venta.moneda}
                    onChange={(e) => {
                        if (detalle.length > 0) {
                            alert("No puede cambiar la moneda después de agregar productos.");
                            return;
                        }
                        handleVentaChange(e);
                    }}
                    disabled={detalle.length > 0}
                >
                    <option value="USD">USD</option>
                    <option value="CRC">CRC</option>
                </select>
            </div>

            {/* PRODUCTOS */}
            <div className="subcard">
                <h3>Agregar Productos</h3>

                {/* ======================= PRODUCTO (input único con dropdown) ======================== */}
                <label>Producto:</label>
                <div ref={productoRef} style={{ position: "relative", width: "100%" }}>
                    <input
                        type="text"
                        placeholder="Buscar producto..."
                        value={buscarProducto}
                        onChange={(e) => {
                            setBuscarProducto(e.target.value);
                            setShowProductosDropdown(true);
                        }}
                        onFocus={() => setShowProductosDropdown(true)}
                        autoComplete="off"
                    />

                    {showProductosDropdown && buscarProducto.length > 0 && (
                        <div className="search-dropdown">
                            {productosFiltrados.length === 0 ? (
                                <div className="dropdown-empty">No se encontraron productos</div>
                            ) : (
                                productosFiltrados.map((p) => (
                                    <div
                                        key={p.producto_id}
                                        className="dropdown-item"
                                        onClick={() => seleccionarProducto(p)}
                                    >
                                        <div className="dd-main">{p.nombre}</div>
                                        <div className="dd-sub">{p.categoria}</div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>

                {/* ======================= CANTIDAD ======================== */}
                <label>Cantidad:</label>
                <input
                    type="number"
                    name="cantidad"
                    value={productoActual.cantidad}
                    onChange={handleProductoChange}
                    min={1}
                />

                {/* ======================= PRECIO ======================== */}
                <label>Precio ({venta.moneda}):</label>
                <input
                    type="number"
                    name="precio"
                    value={productoActual.precio}
                    onChange={handleProductoChange}
                    step="0.01"
                />

                <button className="btn-add" onClick={agregarProducto}>
                    + Insertar Producto
                </button>

                {/* TABLA DE PRODUCTOS */}
                {detalle.length > 0 && (
                    <table>
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Cant</th>
                                <th>Precio</th>
                                <th>Moneda</th>
                                <th>Subtotal</th>
                                <th></th>
                            </tr>
                        </thead>

                        <tbody>
                            {detalle.map((p, i) => (
                                <tr key={i}>
                                    <td>{p.nombre}</td>
                                    <td>{p.cantidad}</td>
                                    <td>{round2(p.precio)}</td>
                                    <td>{p.moneda}</td>
                                    <td>{round2(p.precio * p.cantidad)}</td>
                                    <td>
                                        <button
                                            className="btn-delete"
                                            onClick={() =>
                                                setDetalle(detalle.filter((_, index) => index !== i))
                                            }
                                        >
                                            ✕
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* FOOTER DE TOTAL */}
            {detalle.length > 0 && (
                <div className="total-footer">
                    <span>Total:</span>
                    <strong>{totalFooter} {venta.moneda}</strong>
                </div>
            )}

            {/* BOTONES */}
            <button className="btn-secondary" onClick={cancelar}>
                Cancelar
            </button>

            <button
                className="btn-primary"
                onClick={realizarVenta}
                disabled={detalle.length === 0 || !venta.cliente}
            >
                Realizar Venta
            </button>
        </div>
    );
};

export default CreateVenta;
