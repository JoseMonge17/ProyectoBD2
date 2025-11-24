// src/api/api.js

// URL base para la API
const API_URL = 'http://localhost:5000/api/neo4j'; // Ajusta a tu URL de backend

// Función para obtener todas las ventas
export const fetchVentas = async () => {
  try {
    const response = await fetch(API_URL);
    return await response.json();
  } catch (error) {
    console.error('Error al obtener las ventas:', error);
    return [];
  }
};

export const fetchVentaDetalle = async (id) => {
  try {
    const response = await fetch(`${API_URL}/${id}`);
    if (!response.ok) {
      throw new Error('Error al obtener el detalle de la venta');
    }
    return await response.json();
  } catch (error) {
    console.error('Error al obtener el detalle de la venta:', error);
    throw error;
  }
};

// Función para obtener todos los clientes
export const fetchClientes = async () => {
  try {
    const response = await fetch(`${API_URL}/clientes`); // Ruta de clientes
    console.log("Extraccion clientes")
    console.log(response.json)
    return await response.json();
  } catch (error) {
    console.error('Error al obtener los clientes:', error);
    return [];
  }
};

// Función para obtener todos los productos
export const fetchProductos = async () => {
  try {
    const response = await fetch(`${API_URL}/productos`); // Ruta de productos
    console.log("Venta insertada")
    return await response.json();
  } catch (error) {
    console.error('Error al obtener los productos:', error);
    return [];
  }
};

// Función para crear una nueva venta
export const createVenta = async (venta) => {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(venta),
    });
    return await response.json();
  } catch (error) {
    console.error('Error al crear la venta:', error);
  }
};

// Función para actualizar una venta
export const updateVenta = async (id, venta) => {
  try {
    const response = await fetch(`${API_URL}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(venta),
    });
    return await response.json();
  } catch (error) {
    console.error('Error al actualizar la venta:', error);
  }
};

// Función para eliminar una venta
export const deleteVenta = async (id) => {
  try {
    const response = await fetch(`${API_URL}/${id}`, {
      method: 'DELETE',
    });
    return await response.json();
  } catch (error) {
    console.error('Error al eliminar la venta:', error);
  }
};
