// src/pages/EditVenta.js
import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./styless.css";

const round2 = (n) => Math.round(n * 100) / 100;

const EditVenta = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    // ========================================
    // ESTADOS GENERALES
    // ========================================
    const [venta, setVenta] = useState({
        cliente: "",
        canal: "",
        moneda: "USD",
        fecha: ""
    });

    const [detalle, setDetalle] = useState([]);

    const [clientes, setClientes] = useState([]);
    const [productos, setProductos] = useState([]);

    const [buscarProducto, setBuscarProducto] = useState("");
    const [showProductosDropdown, setShowProductosDropdown] = useState(false);

    const productoRef = useRef(null);

    // Producto a agregar
    const [productoActual, setProductoActual] = useState({
        producto_id: "",
        nombre: "",
        cantidad: 1,
        precio: 0,
    });

    // ========================================
    // CARGA INICIAL DE CLIENTES / PRODUCTOS
    // ========================================
    useEffect(() => {
        fetch("http://127.0.0.1:8000/clientes")
            .then(res => res.json())
            .then(setClientes)
            .catch(err => console.error("Error clientes:", err));

        fetch("http://127.0.0.1:8000/productos")
            .then(res => res.json())
            .then(setProductos)
            .catch(err => console.error("Error productos:", err));
    }, []);

    // ========================================
    // CARGAR LA VENTA A EDITAR
    // ========================================
    useEffect(() => {
        fetch(`http://127.0.0.1:8000/ordenes/${id}`)
            .then(res => res.json())
            .then(data => {
                console.log("DATA RECIBIDA:", data);

                // ============================
                // INFO GENERAL DE LA ORDEN
                // ============================
                const o = data.orden;

                setVenta({
                    cliente_id: o.cliente_id,
                    cliente_nombre: o.cliente_nombre,
                    canal: o.canal,
                    moneda: o.moneda,
                    fecha: o.fecha,
                    total: o.total
                });

                // ============================
                // DETALLES
                // ============================
                const mapped = data.detalles.map(d => ({
                    detalle_id: d.orden_detalle_id,
                    producto_id: d.producto_id,
                    nombre: d.producto_nombre,  
                    cantidad: d.cantidad,
                    precio: d.precio_unit,
                    moneda: o.moneda
                }));

                setDetalle(mapped);
            })
            .catch(err => console.error("Error cargando venta:", err));
    }, [id]);

    // ========================================
    // CLICK FUERA PARA CERRAR DROPDOWN
    // ========================================
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (productoRef.current && !productoRef.current.contains(e.target)) {
                setShowProductosDropdown(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // ========================================
    // CAMBIAR DATOS DE PRODUCTO A AGREGAR
    // ========================================
    const handleProductoChange = (e) => {
        const { name, value } = e.target;
        setProductoActual({
            ...productoActual,
            [name]: name === "cantidad" ? Number(value) : value,
        });
    };

    const seleccionarProducto = (p) => {
        setProductoActual({
            producto_id: p.producto_id,
            nombre: p.nombre,
            cantidad: 1,
            precio: 0
        });
        setBuscarProducto(p.nombre);
        setShowProductosDropdown(false);
    };

    const agregarProducto = () => {
        if (!productoActual.producto_id) return alert("Seleccione un producto");

        if (!productoActual.precio || productoActual.precio <= 0) {
            return alert("El precio debe ser mayor a 0");
        }

        setDetalle([
            ...detalle,
            {
                ...productoActual,
                moneda: venta.moneda
            }
        ]);

        setProductoActual({ producto_id: "", nombre: "", cantidad: 1, precio: 0 });
        setBuscarProducto("");
    };

    // ========================================
    // EDITAR CAMPOS DE PRODUCTOS EXISTENTES
    // ========================================
    const editarCampo = (index, campo, valor) => {
        const updated = [...detalle];
        updated[index][campo] = campo === "cantidad" || campo === "precio"
            ? Number(valor)
            : valor;

        setDetalle(updated);
    };

    const eliminarProducto = (index) => {
        setDetalle(detalle.filter((_, i) => i !== index));
    };

    // ========================================
    // TOTAL
    // ========================================
    const total = round2(
        detalle.reduce((acc, p) => acc + p.precio * p.cantidad, 0)
    );

    // ========================================
    // CANCELAR
    // ========================================
    const cancelar = () => navigate("/ventasSupabase");

    // ========================================
    // Guardar Cambios
    // ========================================
    const guardarCambios = async () => {
        const payload = {
            cliente_id: venta.cliente_id,
            canal: venta.canal,
            moneda: venta.moneda,
            total: total,
            detalles: detalle.map(d => ({
                producto_id: d.producto_id,   // <-- YA EXISTE
                cantidad: d.cantidad,
                precio_unit: d.precio         // <-- en tu estado se llama precio
            }))
        };

        console.log("PAYLOAD:", payload);

        const resp = await fetch(`http://127.0.0.1:8000/ordenes/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        console.log("EDIT RESPONSE:", data);

        if (!resp.ok) {
            console.error("ERROR:", data);
            return alert("Error al actualizar: " + data.detail);
        }

        alert("Venta actualizada correctamente");
        navigate("/ventasSupabase");
    };



    return (
        <div className="create-container">
            <h2>Editar Venta #{id}</h2>

            {/* ================= DATOS GENERALES (NO EDITABLES POR AHORA) ================ */}
            <div className="subcard">
                <h3>Datos Generales</h3>

                <label>Cliente:</label>
                <input value={venta.cliente_nombre} disabled />

                <label>Canal:</label>
                <input value={venta.canal} disabled />

                <label>Moneda:</label>
                <input value={venta.moneda} disabled />

                <label>Fecha:</label>
                <input value={venta.fecha} disabled />
            </div>

            {/* ======================= DETALLES ======================= */}
            <div className="subcard">
            <h3>Productos</h3>

            <table>
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio</th>
                        <th>Subtotal</th>
                        <th></th>
                    </tr>
                </thead>

                <tbody>
                    {detalle.map((p, i) => (
                        <tr key={i}>
                            <td>{p.nombre}</td>

                            <td>
                                <input
                                    type="number"
                                    value={p.cantidad}
                                    min={1}
                                    onChange={(e) =>
                                        editarCampo(i, "cantidad", e.target.value)
                                    }
                                />
                            </td>

                            <td>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={p.precio}
                                    onChange={(e) =>
                                        editarCampo(i, "precio", e.target.value)
                                    }
                                />
                            </td>

                            <td>{round2(p.precio * p.cantidad)}</td>

                            <td>
                                <button className="btn-delete" onClick={() => eliminarProducto(i)}>
                                    ✕
                                </button>
                            </td>
                        </tr>
                    ))}
                    
                    {/* FILA DEL TOTAL */}
                    {detalle.length > 0 && (
                        <tr className="total-row">
                            <td colSpan="3" style={{ textAlign: 'right', fontWeight: 'bold', paddingRight: '20px' }}>
                                TOTAL:
                            </td>
                            <td style={{ fontWeight: 'bold', fontSize: '1.1em' }}>
                                {total} {venta.moneda}
                            </td>
                            <td></td>
                        </tr>
                    )}
                </tbody>
            </table>

                {/* ===================== AGREGAR NUEVO PRODUCTO ======================= */}
                <h3>Agregar Producto</h3>

                <label>Buscar producto:</label>
                <div ref={productoRef} style={{ position: "relative", width: "100%" }}>
                    <input
                        type="text"
                        value={buscarProducto}
                        placeholder="Buscar..."
                        onChange={(e) => {
                            setBuscarProducto(e.target.value);
                            setShowProductosDropdown(true);
                        }}
                        onFocus={() => setShowProductosDropdown(true)}
                    />

                    {showProductosDropdown && buscarProducto.length > 0 && (
                        <div className="search-dropdown">
                            {productos
                                .filter(p =>
                                    p.nombre.toLowerCase().includes(buscarProducto.toLowerCase())
                                )
                                .map(p => (
                                    <div
                                        key={p.producto_id}
                                        className="dropdown-item"
                                        onClick={() => seleccionarProducto(p)}
                                    >
                                        <div className="dd-main">{p.nombre}</div>
                                        <div className="dd-sub">{p.categoria}</div>
                                    </div>
                                ))}
                        </div>
                    )}
                </div>

                <label>Cantidad:</label>
                <input
                    type="number"
                    name="cantidad"
                    value={productoActual.cantidad}
                    min={1}
                    onChange={handleProductoChange}
                />

                <label>Precio ({venta.moneda}):</label>
                <input
                    type="number"
                    step="0.01"
                    name="precio"
                    value={productoActual.precio}
                    onChange={handleProductoChange}
                />

                <button className="btn-add" onClick={agregarProducto}>
                    + Agregar Producto
                </button>
            </div>

            {/* FOOTER */}

            {/* CONTENEDOR PARA BOTONES - SE MANTIENE A LA IZQUIERDA */}
            <div className="botones-container">
                <button className="btn-secondary" onClick={cancelar}>
                    Cancelar
                </button>

                <button className="btn-primary" onClick={guardarCambios}>
                    Guardar Cambios
                </button>
            </div>
        </div>
    );
};

export default EditVenta;
