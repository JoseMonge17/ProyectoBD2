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
            className="px-3 py-1 text-sm rounded-md border hover:bg-gray-100"
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
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Ventas / Órdenes</h1>

      {/* 🔎 Barra de búsqueda */}
      <div className="mb-4 flex gap-2 items-center">
        <input
          type="text"
          placeholder="Buscar por ID, cliente, canal, moneda..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border rounded-md px-3 py-2 text-sm w-full max-w-md"
        />
      </div>

      {loadingVentas && <p>Cargando ventas...</p>}
      {errorVentas && (
        <p className="text-red-600 mb-2">Error: {errorVentas}</p>
      )}

      {!loadingVentas && !errorVentas && (
        <>
          {/* 📋 Tabla */}
          <div className="overflow-x-auto border rounded-lg mb-4">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => {
                      const canSort = header.column.getCanSort();
                      const sorted = header.column.getIsSorted(); // false | 'asc' | 'desc'

                      return (
                        <th
                          key={header.id}
                          className="text-left px-4 py-2 font-medium select-none"
                          onClick={
                            canSort ? header.column.getToggleSortingHandler() : undefined
                          }
                          style={{
                            cursor: canSort ? "pointer" : "default",
                          }}
                        >
                          <div className="flex items-center gap-1">
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                            {canSort && (
                              <span className="text-xs text-gray-500">
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
                      className="px-4 py-4 text-center text-gray-500"
                    >
                      No hay ventas que coincidan con la búsqueda.
                    </td>
                  </tr>
                )}

                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className="border-t">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-2">
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
          <div className="flex items-center justify-between gap-4 mb-6 text-sm">
            <div className="flex items-center gap-2">
              <button
                className="px-2 py-1 border rounded disabled:opacity-50"
                onClick={() => table.setPageIndex(0)}
                disabled={!table.getCanPreviousPage()}
              >
                {"<<"}
              </button>
              <button
                className="px-2 py-1 border rounded disabled:opacity-50"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                Anterior
              </button>
              <button
                className="px-2 py-1 border rounded disabled:opacity-50"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                Siguiente
              </button>
              <button
                className="px-2 py-1 border rounded disabled:opacity-50"
                onClick={() =>
                  table.setPageIndex(table.getPageCount() - 1)
                }
                disabled={!table.getCanNextPage()}
              >
                {">>"}
              </button>
            </div>

            <div>
              Página{" "}
              <strong>
                {table.getState().pagination.pageIndex + 1} de{" "}
                {table.getPageCount() || 1}
              </strong>
            </div>

            <div className="flex items-center gap-2">
              <span>Filas por página:</span>
              <select
                className="border rounded px-2 py-1"
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
      <div className="border rounded-lg p-4 bg-gray-50">
        <h2 className="text-lg font-semibold mb-2">Detalle de la venta</h2>

        {loadingDetalle && <p>Cargando detalle...</p>}
        {errorDetalle && (
          <p className="text-red-600 mb-2">Error: {errorDetalle}</p>
        )}

        {!loadingDetalle && !errorDetalle && !detalle && (
          <p className="text-gray-500 text-sm">
            Selecciona una venta con el botón <b>“Ver detalle”</b>.
          </p>
        )}

        {!loadingDetalle && !errorDetalle && detalle && (
          <div className="space-y-3">
            {/* Orden */}
            <div>
              <p>
                <span className="font-semibold">ID Orden:</span>{" "}
                {detalle.orden?.idOrden}
              </p>
              <p>
                <span className="font-semibold">Fecha:</span>{" "}
                {detalle.orden?.fecha}
              </p>
              <p>
                <span className="font-semibold">Total:</span>{" "}
                {detalle.orden?.total}
              </p>
              <p>
                <span className="font-semibold">Moneda:</span>{" "}
                {detalle.orden?.moneda}
              </p>
              <p>
                <span className="font-semibold">Canal:</span>{" "}
                {detalle.orden?.canal}
              </p>
            </div>

            {/* Cliente */}
            {detalle.cliente && (
              <div>
                <h3 className="font-semibold mt-2 mb-1">Cliente</h3>
                <p>
                  <span className="font-semibold">ID Cliente:</span>{" "}
                  {detalle.cliente.idCliente}
                </p>
                {detalle.cliente.nombre && (
                  <p>
                    <span className="font-semibold">Nombre:</span>{" "}
                    {detalle.cliente.nombre}
                  </p>
                )}
                {detalle.cliente.correo && (
                  <p>
                    <span className="font-semibold">Correo:</span>{" "}
                    {detalle.cliente.correo}
                  </p>
                )}
              </div>
            )}

            {Array.isArray(detalle.productos) &&
                detalle.productos.length > 0 && (
                    <div>
                    <h3 className="font-semibold mt-2 mb-1">Productos</h3>
                    <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                        <thead className="bg-gray-100">
                            <tr>
                            <th className="px-3 py-1 text-left">ID</th>
                            <th className="px-3 py-1 text-left">Nombre</th>
                            <th className="px-3 py-1 text-left">Cantidad</th>
                            <th className="px-3 py-1 text-left">Precio</th>
                            <th className="px-3 py-1 text-left">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detalle.productos.map((item, idx) => {
                            const producto = item.producto || item;
                            const rel = item.relacion || {};

                            const cantidad =
                                rel.propiedades?.cantidad ?? producto.cantidad ?? 0;
                            const precio =
                                rel.propiedades?.precio ?? producto.precio ?? 0;

                            const totalCalculado = Number(cantidad) * Number(precio);

                            return (
                                <tr key={idx} className="border-t">
                                <td className="px-3 py-1">{producto.idProducto}</td>
                                <td className="px-3 py-1">{producto.nombre}</td>
                                <td className="px-3 py-1">{cantidad}</td>
                                <td className="px-3 py-1">{precio}</td>
                                <td className="px-3 py-1">{totalCalculado}</td>
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
