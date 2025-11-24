// src/VentasPage.js
import React, { useEffect, useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from "@tanstack/react-table";
import './OrdersPage.css'; // Estilos básicos

import { fetchVentas, fetchVentaDetalle } from "./api"; // ajusta la ruta si es necesaria

const columnHelper = createColumnHelper();

function VentasPage() {
  const [ventas, setVentas] = useState([]);
  const [loadingVentas, setLoadingVentas] = useState(false);
  const [errorVentas, setErrorVentas] = useState(null);

  const [detalle, setDetalle] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [errorDetalle, setErrorDetalle] = useState(null);

  const [sorting, setSorting] = useState([]);
  const [search, setSearch] = useState("");

  // 🔁 Cargar ventas desde tu API
  useEffect(() => {
    const loadVentas = async () => {
      try {
        setLoadingVentas(true);
        setErrorVentas(null);
        const data = await fetchVentas();
        setVentas(data || []);
      } catch (err) {
        setErrorVentas(err.message || "Error desconocido");
      } finally {
        setLoadingVentas(false);
      }
    };

    loadVentas();
  }, []);

  // 🔍 Filtrado simple por texto (ID, cliente, canal, moneda…)
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

  // 📊 Definir columnas
  const columns = useMemo(
    () => [
      columnHelper.accessor("id", {
        header: "ID",
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor("fecha", {
        header: "Fecha",
        cell: (info) => {
          const value = info.getValue();
          try {
            const d = new Date(value);
            if (isNaN(d.getTime())) return value;
            return d.toLocaleString("es-CR", {
              dateStyle: "short",
              timeStyle: "short",
            });
          } catch {
            return value;
          }
        },
      }),
      columnHelper.accessor("total", {
        header: "Total",
        cell: (info) => {
          const value = Number(info.getValue() ?? 0);
          return value.toLocaleString("es-CR", {
            style: "currency",
            currency: "CRC",
            maximumFractionDigits: 2,
          });
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
      columnHelper.accessor("cliente", {
        header: "Cliente",
        cell: (info) => info.getValue(),
      }),
      columnHelper.display({
        id: "acciones",
        header: "Acciones",
        cell: ({ row }) => (
          <button
            className="btn-detalle"
            onClick={() => handleVerDetalle(row.original)}
          >
            Ver detalle
          </button>
        ),
}),
    ],
    []
  );

  // 🧠 Configurar tabla con sorting + paginación
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

  // 🔍 Detalle de venta
  const handleVerDetalle = async (venta) => {
    try {
      setLoadingDetalle(true);
      setErrorDetalle(null);
      setDetalle(null);

      const data = await fetchVentaDetalle(venta.id);
      setDetalle(data);
    } catch (err) {
      setErrorDetalle(err.message || "Error al cargar detalle");
    } finally {
      setLoadingDetalle(false);
    }
  };

  return (
  <div className="ventas-container">
    <h1>Ventas / Órdenes</h1>

    {/* 🔎 Barra de búsqueda */}
    <div className="search-container">
      <input
        type="text"
        placeholder="Buscar por ID, cliente, canal, moneda..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
    </div>

    {loadingVentas && <p className="loading-message">Cargando ventas...</p>}
    {errorVentas && (
      <p className="error-message">Error: {errorVentas}</p>
    )}

    {!loadingVentas && !errorVentas && (
      <>
        {/* 📋 Tabla */}
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

    {/* 🧾 Detalle de la venta */}
    <div className="detalle-panel">
      <h2>Detalle de la venta</h2>

      {loadingDetalle && <p className="loading-message">Cargando detalle...</p>}
      {errorDetalle && (
        <p className="error-message">Error: {errorDetalle}</p>
      )}

      {!loadingDetalle && !errorDetalle && !detalle && (
        <p className="detalle-empty">
          Selecciona una venta con el botón <b>"Ver detalle"</b>.
        </p>
      )}

      {!loadingDetalle && !errorDetalle && detalle && (
        <div>
          {/* Orden */}
          <div className="detalle-info">
            <p>
              <span>ID Orden:</span> {detalle.orden?.idOrden}
            </p>
            <p>
              <span>Fecha:</span> {detalle.orden?.fecha}
            </p>
            <p>
              <span>Total:</span> {detalle.orden?.total}
            </p>
            <p>
              <span>Moneda:</span> {detalle.orden?.moneda}
            </p>
            <p>
              <span>Canal:</span> {detalle.orden?.canal}
            </p>
          </div>

          {/* Cliente */}
          {detalle.cliente && (
            <div>
              <h3>Cliente</h3>
              <div className="detalle-info">
                <p>
                  <span>ID Cliente:</span> {detalle.cliente.idCliente}
                </p>
                {detalle.cliente.nombre && (
                  <p>
                    <span>Nombre:</span> {detalle.cliente.nombre}
                  </p>
                )}
                {detalle.cliente.correo && (
                  <p>
                    <span>Correo:</span> {detalle.cliente.correo}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Productos */}
          {Array.isArray(detalle.productos) &&
            detalle.productos.length > 0 && (
              <div>
                <h3>Productos</h3>
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Cantidad</th>
                        <th>Precio</th>
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detalle.productos.map((item, idx) => {
                        const producto = item.producto || item;
                        const rel = item.relacion || {};
                        const cantidad = rel.propiedades?.cantidad ?? producto.cantidad ?? 0;
                        const precio = rel.propiedades?.precio ?? producto.precio ?? 0;
                        const totalCalculado = Number(cantidad) * Number(precio);

                        return (
                          <tr key={idx}>
                            <td>{producto.idProducto}</td>
                            <td>{producto.nombre}</td>
                            <td>{cantidad}</td>
                            <td>{precio}</td>
                            <td>{totalCalculado}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
        </div>
      )}
    </div>
  </div>
);
}

export default VentasPage;
