import React, { useState, useEffect } from 'react';
import { updateVenta, fetchVentaDetalle, fetchClientes, fetchProductos } from './api';
import Select from 'react-select';
import { useNavigate, useParams } from 'react-router-dom';
import './CrearVenta.css'; // Reutilizamos los mismos estilos

const EditarVenta = () => {
  const navigate = useNavigate();
  const { id } = useParams(); // Obtenemos el ID de la URL

  const [venta, setVenta] = useState({
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
  const [loadingData, setLoadingData] = useState(true);

  // Agregar después de los estados existentes
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [cargandoRecomendaciones, setCargandoRecomendaciones] = useState(false);
  const [preciosRecomendados, setPreciosRecomendados] = useState({});

  // Cargar datos iniciales
  useEffect(() => {
    async function fetchData() {
      try {
        setLoadingData(true);
        console.log('🔍 Cargando venta con ID:', id);
        
        // Cargar venta existente
        const ventaData = await fetchVentaDetalle(id);
        console.log('📦 Venta cargada:', ventaData);
        
        // Cargar clientes y productos
        const fetchedClientes = await fetchClientes();
        const fetchedProductos = await fetchProductos();
        
        setClientes(Array.isArray(fetchedClientes) ? fetchedClientes : []);
        setProductos(Array.isArray(fetchedProductos) ? fetchedProductos : []);
        
        // Mapear los datos de la venta al formato del formulario
        if (ventaData && ventaData.orden) {
          const productosFormateados = Array.isArray(ventaData.productos) 
            ? ventaData.productos.map(item => {
                const producto = item.producto || item;
                const rel = item.relacion || {};
                return {
                  producto: producto.nombre,
                  id: producto.idProducto,
                  cantidad: rel.propiedades?.cantidad ?? producto.cantidad ?? 0,
                  precio: rel.propiedades?.precio ?? producto.precio ?? 0,
                  total: (rel.propiedades?.cantidad ?? producto.cantidad ?? 0) * 
                         (rel.propiedades?.precio ?? producto.precio ?? 0),
                };
              })
            : [];

          setVenta({
            fecha: ventaData.orden.fecha || '',
            cliente: ventaData.cliente?.idCliente || '',
            total: ventaData.orden.total || 0,
            moneda: 'CRC',
            canal: ventaData.orden.canal || '',
            productos: productosFormateados,
            cupon: ventaData.cupon || '',
          });
        }
      } catch (error) {
        console.error('❌ Error al cargar datos:', error);
        alert('Error al cargar la venta: ' + error.message);
      } finally {
        setLoadingData(false);
      }
    }

    fetchData();
  }, [id]);

  // Manejar los cambios en el formulario
  const handleChange = (e) => {
    const { name, value } = e.target;
    setVenta((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  // Manejar el cambio de cliente (select)
  const handleSelectChange = (selectedOption, field) => {
    setVenta((prevState) => ({
      ...prevState,
      [field]: selectedOption ? selectedOption.value : '',
    }));
  };

  // Agregar un producto con cantidad y precio
  // Agregar un producto con cantidad y precio
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

    setVenta((prevState) => ({
      ...prevState,
      productos: [...prevState.productos, nuevoProducto],
      total: prevState.total + nuevoProducto.total,
    }));

    // Solo reiniciar inputs, NO las recomendaciones
    setCantidad('');
    setPrecio('');
    setSelectedProducto(null);
  };

  // Eliminar un producto de la lista
  const handleEliminarProducto = (index) => {
    const productoAEliminar = venta.productos[index];
    setVenta((prevState) => ({
      ...prevState,
      productos: prevState.productos.filter((_, i) => i !== index),
      total: prevState.total - productoAEliminar.total,
    }));
  };

  // Manejar el submit del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (venta.productos.length === 0) {
      alert('Debe agregar al menos un producto');
      return;
    }

    setLoading(true);

    try {
      await updateVenta(id, venta);
      
      setLoading(false);
      alert('Venta actualizada exitosamente!');
      navigate('/ventasMongo');
    } catch (error) {
      setLoading(false);
      alert('Error al actualizar la venta: ' + error.message);
    }
  };

  // Mapeo de datos para react-select con validación
  const clienteOptions = Array.isArray(clientes) 
    ? clientes.map(cliente => ({
        value: cliente.id,
        label: cliente.nombre,
      }))
    : [];

  const productoOptions = Array.isArray(productos)
    ? productos.map(producto => ({
        value: producto.id,
        label: producto.nombre,
      }))
    : [];

  // Función para navegar hacia la página de ventas
  const handleVolver = () => {
    navigate('/ventasMongo');
  };

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

  // Manejar cambio de precio en recomendaciones
  const handlePrecioRecomendadoChange = (productoId, precio) => {
    setPreciosRecomendados(prev => ({
      ...prev,
      [productoId]: precio
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

    setVenta((prevState) => ({
      ...prevState,
      productos: [...prevState.productos, nuevoProducto],
      total: prevState.total + nuevoProducto.total,
    }));
  };

  // Mostrar loading mientras se cargan los datos
  if (loadingData) {
    return (
      <div className="container">
        <p style={{ textAlign: 'center', padding: '40px', color: '#667eea', fontSize: '18px' }}>
          Cargando datos de la venta...
        </p>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Botón Volver */}
      <button className="back-btn" onClick={handleVolver}>Volver</button>

      {/* Encabezado de la factura */}
      <h2>Actualizar Venta #{id}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-header">
          {/* Select de clientes */}
          <Select
            options={clienteOptions}
            onChange={(selectedOption) => handleSelectChange(selectedOption, 'cliente')}
            value={clienteOptions.find(opt => opt.value === venta.cliente)}
            placeholder="Selecciona un Cliente"
            isClearable
            isDisabled={clienteOptions.length === 0}
          />
        </div>

        <div className="form-details">
          {/* Select de canal */}
          <select
            name="canal"
            value={venta.canal}
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
            value={venta.cupon}
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
                isDisabled={productoOptions.length === 0}
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
                step="0.01"
                value={precio}
                onChange={(e) => setPrecio(e.target.value)}
                placeholder="Precio"
              />
            </div>
          </div>
          
          <button type="button" onClick={handleAgregarProducto}>
            Agregar Producto
          </button>
        </div>

        {/* SECCIÓN DE RECOMENDACIONES */}
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
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {venta.productos.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '20px', color: '#95a5a6', fontStyle: 'italic' }}>
                    No hay productos agregados
                  </td>
                </tr>
              ) : (
                venta.productos.map((producto, index) => (
                  <tr key={index}>
                    <td>{producto.producto}</td>
                    <td>{producto.cantidad}</td>
                    <td>{producto.precio}</td>
                    <td>{producto.total}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => handleEliminarProducto(index)}
                        style={{
                          background: '#e74c3c',
                          color: 'white',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: '5px',
                          fontSize: '12px',
                          cursor: 'pointer',
                          fontWeight: '600',
                        }}
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Total */}
        <div style={{ 
          textAlign: 'right', 
          fontSize: '20px', 
          fontWeight: 'bold', 
          color: '#2c3e50',
          marginTop: '15px',
          paddingRight: '15px'
        }}>
          Total: ₡{venta.total.toLocaleString('es-CR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>

        {/* Botón de actualizar venta */}
        <div className="submit-button">
          <button type="submit" disabled={loading}>
            {loading ? 'Actualizando...' : 'Actualizar Venta'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditarVenta;