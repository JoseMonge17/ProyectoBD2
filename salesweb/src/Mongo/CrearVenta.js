import React, { useState, useEffect } from 'react';
import { createVenta, fetchClientes, fetchProductos } from './api';
import Select from 'react-select';
import { useNavigate } from 'react-router-dom';
import './CrearVenta.css';

const CrearVenta = () => {
  const navigate = useNavigate();

  const [newVenta, setNewVenta] = useState({
    fecha: '',
    cliente: '',
    total: 0,
    moneda: 'CRC',
    canal: '',
    productos: [],
    cupon: '',
  });

  const [clientes, setClientes] = useState([]);
  const [productos, setProductos] = useState([]);
  const [selectedProducto, setSelectedProducto] = useState(null);
  const [cantidad, setCantidad] = useState('');
  const [precio, setPrecio] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Nuevos estados para recomendaciones
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [cargandoRecomendaciones, setCargandoRecomendaciones] = useState(false);
  const [preciosRecomendados, setPreciosRecomendados] = useState({});

  // Cargar los clientes y productos desde la API
  useEffect(() => {
    async function fetchData() {
      const fetchedClientes = await fetchClientes();
      const fetchedProductos = await fetchProductos();
      setClientes(fetchedClientes);
      setProductos(fetchedProductos);
    }
    fetchData();
  }, []);

  // Función para obtener recomendaciones cuando se selecciona un producto
  const obtenerRecomendaciones = async (productoId) => {
    if (!productoId) {
      setRecomendaciones([]);
      return;
    }

    setCargandoRecomendaciones(true);
    try {
      const response = await fetch(`http://localhost:5000/api/apriori/recomendaciones/${productoId}`);
      if (response.ok) {
        const data = await response.json();
        setRecomendaciones(data.recomendaciones || []);
      } else {
        setRecomendaciones([]);
      }
    } catch (error) {
      console.error('Error al obtener recomendaciones:', error);
      setRecomendaciones([]);
    } finally {
      setCargandoRecomendaciones(false);
    }
  };

  // Manejar cambio de producto seleccionado
  const handleProductoChange = (selectedOption) => {
    setSelectedProducto(selectedOption);
    
    if (selectedOption) {
      // Obtener recomendaciones para el producto seleccionado
      obtenerRecomendaciones(selectedOption.value);
    } else {
      setRecomendaciones([]);
    }
  };

  // Manejar los cambios en el formulario
  const handleChange = (e) => {
    const { name, value } = e.target;
    setNewVenta((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  // Manejar el cambio de cliente (select)
  const handleSelectChange = (selectedOption, field) => {
    setNewVenta((prevState) => ({
      ...prevState,
      [field]: selectedOption ? selectedOption.value : '',
    }));
  };

  // Agregar producto recomendado directamente
  const agregarProductoRecomendado = (productoRecomendado) => {
    const precio = preciosRecomendados[productoRecomendado.productoId] || 1000;
    
    const nuevoProducto = {
      producto: productoRecomendado.nombre,
      id: productoRecomendado.productoId,
      precio: precio,
      cantidad: 1,
      total: precio,
    };

    setNewVenta((prevState) => ({
      ...prevState,
      productos: [...prevState.productos, nuevoProducto],
      total: prevState.total + nuevoProducto.total,
    }));
  };

  // Agregar función para manejar cambio de precio en recomendaciones
  const handlePrecioRecomendadoChange = (productoId, precio) => {
    setPreciosRecomendados(prev => ({
      ...prev,
      [productoId]: precio
    }));
  };

  // Agregar un producto con cantidad y precio (función original)
  const handleAgregarProducto = () => {
    if (!selectedProducto || !cantidad || !precio) {
      alert("Por favor, complete todos los campos.");
      return;
    }

    const nuevoProducto = {
      producto: selectedProducto.label,
      id: selectedProducto.value,
      precio: parseFloat(precio),
      cantidad: parseInt(cantidad),
      total: parseFloat(cantidad) * parseFloat(precio),
    };

    setNewVenta((prevState) => ({
      ...prevState,
      productos: [...prevState.productos, nuevoProducto],
      total: prevState.total + nuevoProducto.total,
    }));

    // Reiniciar los inputs después de agregar
    setCantidad('');
    setPrecio('');
    setSelectedProducto(null);
    setRecomendaciones([]); // Limpiar recomendaciones después de agregar
  };

  // Manejar el submit del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await createVenta(newVenta);
      
      setNewVenta({
        fecha: '',
        cliente: '',
        total: 0,
        moneda: 'CRC',
        canal: '',
        productos: [],
        cupon: '',
      });

      setLoading(false);
      alert('Venta creada exitosamente!');
    } catch (error) {
      setLoading(false);
      alert('Error al crear la venta');
    }
  };

  // Mapeo de datos para react-select
  const clienteOptions = clientes.map(cliente => ({
    value: cliente.id,
    label: cliente.nombre,
  }));

  const productoOptions = productos.map(producto => ({
    value: producto.id,
    label: producto.nombre,
  }));

  // Función para navegar hacia la página de ventas
  const handleVolver = () => {
    navigate('/ventasMongo');
  };

  return (
    <div className="container">
      <button className="back-btn" onClick={handleVolver}>Volver</button>

      <h2>Crear Venta</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-header">
          <Select
            options={clienteOptions}
            onChange={(selectedOption) => handleSelectChange(selectedOption, 'cliente')}
            placeholder="Selecciona un Cliente"
            isClearable
          />
        </div>

        <div className="form-details">
          <select
            name="canal"
            value={newVenta.canal}
            onChange={handleChange}
            required
          >
            <option value="">Selecciona un Canal</option>
            <option value="WEB">Web</option>
            <option value="TIENDA">Tienda</option>
            <option value="APP">Aplicación</option>
          </select>

          <input
            type="text"
            name="cupon"
            value={newVenta.cupon}
            onChange={handleChange}
            placeholder="Cupón (opcional)"
          />
        </div>

        {/* Formulario para agregar productos */}
        <div className="product-form">
          <h3>Agregar Producto</h3>
          <div className="form-inputs">
            <div className="input-column">
              <Select
                options={productoOptions}
                onChange={handleProductoChange}
                value={selectedProducto}
                placeholder="Selecciona un Producto"
                isClearable
              />
            </div>

            <div className="input-column">
              <input
                type="number"
                value={cantidad}
                onChange={(e) => setCantidad(e.target.value)}
                placeholder="Cantidad"
              />
              <input
                type="number"
                min="0"
                step="1"
                value={precio}
                onChange={(e) => {
                  const raw = e.target.value;
                  let intValue = parseInt(raw, 10);
                  if (isNaN(intValue)) intValue = 0;
                  if (intValue < 0) intValue = 0;
                  setPrecio(intValue);
                }}
                placeholder="Precio"
              />
            </div>
          </div>
          
          <button type="button" onClick={handleAgregarProducto}>
            Agregar Producto
          </button>
        </div>

        {/* Sección de Recomendaciones */}
        {recomendaciones.length > 0 && (
          <div className="recomendaciones-section">
            <h3>💡 Productos que otros clientes también compran:</h3>
            <div className="recomendaciones-grid">
              {recomendaciones.map((rec, index) => (
                <div key={index} className="recomendacion-card">
                  <div className="recomendacion-info">
                    <strong>{rec.nombre}</strong>
                    <div className="recomendacion-stats">
                      <span>Confianza: {rec.confidence}%</span>
                    </div>
                    <div className="precio-input">
                      <label>Precio:</label>
                      <input
                        type="number"
                        min="0"
                        step="1"
                        value={preciosRecomendados[rec.productoId] || 1000}
                        onChange={(e) => {
                          const valor = parseInt(e.target.value) || 0;
                          handlePrecioRecomendadoChange(rec.productoId, valor);
                        }}
                        className="precio-input-field"
                      />
                    </div>
                  </div>
                  <button 
                    type="button"
                    className="btn-agregar-recomendado"
                    onClick={() => agregarProductoRecomendado(rec)}
                  >
                    Agregar
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {cargandoRecomendaciones && (
          <div className="cargando-recomendaciones">
            <p>Buscando recomendaciones...</p>
          </div>
        )}

        {/* Tabla de productos agregados */}
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {newVenta.productos.map((producto, index) => (
                <tr key={index}>
                  <td>{producto.producto}</td>
                  <td>{producto.cantidad}</td>
                  <td>{producto.precio}</td>
                  <td>{producto.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Botón de crear venta */}
        <div className="submit-button">
          <button type="submit" disabled={loading}>
            {loading ? 'Cargando...' : 'Crear Venta'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CrearVenta;