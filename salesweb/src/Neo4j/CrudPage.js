// src/components/CrudPage.js
import React, { useState, useEffect } from 'react';
import { createVenta, fetchVentas, updateVenta, deleteVenta } from './api'; // Importamos las funciones de la API
import './CrudPage.css'; // Asegúrate de que los estilos estén importados

const CrudPage = () => {
  const [ventas, setVentas] = useState([]);
  const [newVenta, setNewVenta] = useState({
    id: '',
    fecha: '',
    cliente: '',
    total: 0,
    moneda: '',
    canal: '',
  });
  const [editMode, setEditMode] = useState(false); // Para verificar si estamos editando
  const [editId, setEditId] = useState(null); // ID de la venta que estamos editando

  // Cargar las ventas desde la API
  useEffect(() => {
    loadVentas();
  }, []);

  // Función para cargar todas las ventas
  const loadVentas = async () => {
    const result = await fetchVentas();
    setVentas(result);
  };

  // Función para manejar los cambios en el formulario
  const handleChange = (e) => {
    const { name, value } = e.target;
    setNewVenta((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  // Función para crear una nueva venta
  const handleCreate = async (e) => {
    e.preventDefault();
    await createVenta(newVenta);
    setNewVenta({ id: '', fecha: '', cliente: '', total: 0, moneda: '', canal: '' });
    loadVentas(); // Recargar las ventas
  };

  // Función para editar una venta
  const handleEdit = (venta) => {
    setNewVenta(venta);
    setEditMode(true);
    setEditId(venta.id);
  };

  // Función para actualizar una venta
  const handleUpdate = async (e) => {
    e.preventDefault();
    await updateVenta(editId, newVenta);
    setEditMode(false);
    setEditId(null);
    loadVentas(); // Recargar las ventas
  };

  // Función para eliminar una venta
  const handleDelete = async (id) => {
    await deleteVenta(id);
    loadVentas(); // Recargar las ventas
  };

  return (
    <div className="container">
      <h2>{editMode ? 'Actualizar Venta' : 'Agregar Nueva Venta'}</h2>

      <form onSubmit={editMode ? handleUpdate : handleCreate}>
        <input
          type="text"
          name="fecha"
          placeholder="Fecha"
          value={newVenta.fecha}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="cliente"
          placeholder="Cliente"
          value={newVenta.cliente}
          onChange={handleChange}
          required
        />
        <input
          type="number"
          name="total"
          placeholder="Total"
          value={newVenta.total}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="moneda"
          placeholder="Moneda"
          value={newVenta.moneda}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="canal"
          placeholder="Canal"
          value={newVenta.canal}
          onChange={handleChange}
          required
        />
        <button type="submit">{editMode ? 'Actualizar' : 'Crear'}</button>
      </form>

      <h2>Lista de Ventas</h2>
      <table>
        <thead>
          <tr>
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
          {ventas.map((venta) => (
            <tr key={venta.id}>
              <td>{venta.id}</td>
              <td>{venta.fecha}</td>
              <td>{venta.cliente}</td>
              <td>{venta.total}</td>
              <td>{venta.moneda}</td>
              <td>{venta.canal}</td>
              <td>
                <button onClick={() => handleEdit(venta)}>Editar</button>
                <button onClick={() => handleDelete(venta.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CrudPage;
