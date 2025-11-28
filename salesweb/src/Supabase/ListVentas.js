// src/pages/ListaVentas.js
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from "@tanstack/react-table";
import "./styles.css";

const ListVentas = () => {
    const [ventas, setVentas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [logData, setLogData] = useState(null);
    const [logLoading, setLogLoading] = useState(true);

    // Estados para el popup
    const [showConfirm, setShowConfirm] = useState(false);
    const [ventaAEliminar, setVentaAEliminar] = useState(null);
    const [deleting, setDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState(null);
    const [search, setSearch] = useState("");
    const [sorting, setSorting] = useState([]);

    const navigate = useNavigate();
    const columnHelper = createColumnHelper();

    useEffect(() => {
        loadLogData();
        loadVentas();
    }, []);

    // Cargar datos del log
    const loadLogData = async () => {
        try {
            const response = await fetch("http://127.0.0.1:8000/get-log-data");
            if (!response.ok) {
                throw new Error("Error al obtener datos del log");
            }
            const data = await response.json();
            setLogData(data);
        } catch (err) {
            console.error("Error cargando log:", err);
            setLogData(null);
        } finally {
            setLogLoading(false);
        }
    };

    // Función para verificar si una venta es editable/eliminable
    const isVentaEditable = (venta) => {
        if (!logData || !logData.last_processed_date) return true;
        
        try {
            const ventaDate = new Date(venta.fechaOriginal);
            const lastProcessedDate = new Date(logData.last_processed_date);
            
            // Si la fecha de la venta es posterior a la última procesada, es editable
            return ventaDate > lastProcessedDate;
        } catch (error) {
            console.error("Error comparando fechas:", error);
            return true;
        }
    };

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
                fechaOriginal: v.fecha, // Guardamos la fecha original para comparar
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

    // 🔍 Filtrado simple por texto
    const filteredData = useMemo(() => {
        if (!search.trim()) return ventas;

        const term = search.toLowerCase();
        return ventas.filter((venta) => {
            return (
                String(venta.id ?? "").toLowerCase().includes(term) ||
                String(venta.cliente ?? "").toLowerCase().includes(term) ||
                String(venta.canal ?? "").toLowerCase().includes(term) ||
                String(venta.moneda ?? "").toLowerCase().includes(term) ||
                String(venta.fecha ?? "").toLowerCase().includes(term)
            );
        });
    }, [ventas, search]);

    // Definir columnas
    const columns = useMemo(
        () => [
            columnHelper.accessor("id", {
                header: "ID",
                cell: (info) => info.getValue(),
            }),
            columnHelper.accessor("fecha", {
                header: "Fecha",
                cell: (info) => info.getValue(),
            }),
            columnHelper.accessor("cliente", {
                header: "Cliente",
                cell: (info) => info.getValue(),
            }),
            columnHelper.accessor("total", {
                header: "Total",
                cell: (info) => {
                    const value = Number(info.getValue() ?? 0);
                    const moneda = info.row.original.moneda; // Obtener la moneda de la fila
                    
                    if (moneda?.toLowerCase() === "usd") {
                        return value.toLocaleString("en-US", {
                            style: "currency",
                            currency: "USD",
                            maximumFractionDigits: 2,
                        });
                    } else {
                        // Por defecto mostrar colones
                        return value.toLocaleString("es-CR", {
                            style: "currency",
                            currency: "CRC",
                            maximumFractionDigits: 2,
                        });
                    }
                },
            }),
            columnHelper.accessor("moneda", {
                header: "Moneda",
                cell: (info) => info.getValue(),
            }),
            columnHelper.accessor("canal", {
                header: "Canal",
                cell: (info) => info.getValue(),
            }),
            columnHelper.display({
                id: "acciones",
                header: "Acciones",
                cell: ({ row }) => {
                    const venta = row.original;
                    const esEditable = isVentaEditable(venta);

                    return (
                        <div className="action-buttons">
                            {/* Botón VER - siempre disponible */}
                            <button
                                style={{ backgroundColor: "#4caf50" }}
                                onClick={() => navigate(`/detallesVentaSupabase/${venta.id}`)}
                            >
                                Ver
                            </button>

                            {/* Botón EDITAR - condicional */}
                            {esEditable ? (
                                <button
                                    style={{ backgroundColor: "#ff9800" }}
                                    onClick={() => navigate(`/editarVentaSupabase/${venta.id}`)}
                                >
                                    Editar
                                </button>
                            ) : (
                                <button
                                    style={{ 
                                        backgroundColor: "#cccccc",
                                        color: "#666666",
                                        cursor: "not-allowed"
                                    }}
                                    disabled
                                >
                                    Editar
                                </button>
                            )}

                            {/* Botón ELIMINAR - condicional */}
                            {esEditable ? (
                                <button
                                    style={{ backgroundColor: "#f44336" }}
                                    onClick={() => confirmarEliminacion(venta.id)}
                                >
                                    Eliminar
                                </button>
                            ) : (
                                <button
                                    style={{ 
                                        backgroundColor: "#cccccc",
                                        color: "#666666",
                                        cursor: "not-allowed"
                                    }}
                                    disabled
                                >
                                    Eliminar
                                </button>
                            )}
                        </div>
                    );
                },
            }),
        ],
        [logData]
    );

    // 🧠 Configurar tabla
    const table = useReactTable({
        data: filteredData,
        columns,
        state: {
            sorting,
        },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        initialState: {
            pagination: {
                pageSize: 10,
                pageIndex: 0,
            },
        },
    });

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
            // Recargar datos del log después de ejecutar ETL
            await loadLogData();
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

            let payload = null;
            try {
                payload = await res.json();
            } catch (e) {
                // si no viene JSON, ok
            }

            if (!res.ok) {
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
            alert("No se pudo eliminar: " + (err.message || "Error desconocido"));
        } finally {
            setDeleting(false);
        }
    };

    // Mostrar información del log
    const renderLogInfo = () => {
        if (logLoading) return <p>Cargando información del log...</p>;
        if (!logData) return <p style={{ color: 'orange' }}>No se pudo cargar información del log</p>;
        
        return (
            <div style={{ 
                margin: '10px 0', 
                padding: '10px', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '5px',
                fontSize: '14px'
            }}>
                <strong>Última ejecución ETL:</strong> {new Date(logData.last_run).toLocaleString()} |
                <strong> Última venta procesada:</strong> {new Date(logData.last_processed_date).toLocaleString()}
            </div>
        );
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

            {renderLogInfo()}

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
                <>
                    {/* 📋 Tabla con @tanstack/react-table */}
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                {table.getHeaderGroups().map((headerGroup) => (
                                    <tr key={headerGroup.id}>
                                        {headerGroup.headers.map((header) => {
                                            const canSort = header.column.getCanSort();
                                            const sorted = header.column.getIsSorted();

                                            return (
                                                <th
                                                    key={header.id}
                                                    onClick={
                                                        canSort ? header.column.getToggleSortingHandler() : undefined
                                                    }
                                                    style={{
                                                        cursor: canSort ? "pointer" : "default",
                                                    }}
                                                >
                                                    <div className="flex">
                                                        {header.isPlaceholder
                                                            ? null
                                                            : flexRender(
                                                                header.column.columnDef.header,
                                                                header.getContext()
                                                            )}
                                                        {canSort && (
                                                            <span className="sort-icon">
                                                                {sorted === "asc"
                                                                    ? "▲"
                                                                    : sorted === "desc"
                                                                    ? "▼"
                                                                    : "↕"}
                                                            </span>
                                                        )}
                                                    </div>
                                                </th>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </thead>
                            <tbody>
                                {table.getRowModel().rows.length === 0 && (
                                    <tr>
                                        <td
                                            colSpan={columns.length}
                                            className="empty-message"
                                        >
                                            No hay ventas que coincidan con la búsqueda.
                                        </td>
                                    </tr>
                                )}

                                {table.getRowModel().rows.map((row) => (
                                    <tr key={row.id}>
                                        {row.getVisibleCells().map((cell) => (
                                            <td key={cell.id}>
                                                {flexRender(
                                                    cell.column.columnDef.cell,
                                                    cell.getContext()
                                                )}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* 📄 Controles de paginación */}
                    <div className="pagination-controls">
                        <div className="pagination-buttons">
                            <button
                                onClick={() => table.setPageIndex(0)}
                                disabled={!table.getCanPreviousPage()}
                            >
                                {"<<"}
                            </button>
                            <button
                                onClick={() => table.previousPage()}
                                disabled={!table.getCanPreviousPage()}
                            >
                                Anterior
                            </button>
                            <button
                                onClick={() => table.nextPage()}
                                disabled={!table.getCanNextPage()}
                            >
                                Siguiente
                            </button>
                            <button
                                onClick={() =>
                                    table.setPageIndex(table.getPageCount() - 1)
                                }
                                disabled={!table.getCanNextPage()}
                            >
                                {">>"}
                            </button>
                        </div>

                        <div className="pagination-info">
                            Página{" "}
                            <strong>
                                {table.getState().pagination.pageIndex + 1} de{" "}
                                {table.getPageCount() || 1}
                            </strong>
                        </div>

                        <div className="page-size-selector">
                            <span>Filas por página:</span>
                            <select
                                value={table.getState().pagination.pageSize}
                                onChange={(e) => {
                                    table.setPageSize(Number(e.target.value));
                                }}
                            >
                                {[5, 10, 20, 50].map((size) => (
                                    <option key={size} value={size}>
                                        {size}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </>
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