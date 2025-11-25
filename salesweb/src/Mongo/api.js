// src/api/api.js

// URL base para la API
const API_URL = 'http://localhost:5000/api/mongo'; // Ajusta a tu URL de backend

// Función para obtener todas las ventas
export const fetchVentas = async () => {
  try {
    const response = await fetch(`${API_URL}/ventas`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error al obtener las ventas:', error);
    return [];
  }
};

export const fetchVentaDetalle = async (id) => {
  try {
    const response = await fetch(`${API_URL}/ventas/${id}`);
    if (!response.ok) {
      throw new Error('Error al obtener el detalle de la venta');
    }
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
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
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
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
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error al obtener los productos:', error);
    return [];
  }
};

// Función para crear una nueva venta
export const createVenta = async (venta) => {
  try {
    const response = await fetch(`${API_URL}/ventas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(venta),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error al crear la venta:', error);
  }
};

// Función para actualizar una venta
export const updateVenta = async (id, venta) => {
  try {
    const response = await fetch(`${API_URL}/ventas/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(venta),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error al actualizar la venta:', error);
  }
};

// Función para eliminar una venta
export const deleteVenta = async (id) => {
  try {
    const response = await fetch(`${API_URL}/ventas/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error al eliminar la venta:', error);
  }
};

// Función para eliminar una venta
export const ejecutarETL = async () => {
  try {
    const response = await fetch(`${API_URL}/etl`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error al eliminar la venta:', error);
  }
};
