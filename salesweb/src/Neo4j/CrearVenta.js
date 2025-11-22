import React, { useState, useEffect } from 'react';
import { createVenta, fetchClientes, fetchProductos } from './api'; // Usamos las funciones para obtener datos
import Select from 'react-select'; // Importamos react-select
import { useNavigate } from 'react-router-dom'; // Usamos useNavigate para la navegación
import '../styles.css'; // Estilos básicos

const CrearVenta = () => {
  const navigate = useNavigate(); // Para la navegación

  const [newVenta, setNewVenta] = useState({
    fecha: '',
    cliente: '',
    total: 0,
    moneda: '',
    canal: '',
    productos: [],
  });

  const [clientes, setClientes] = useState([]);
  const [productos, setProductos] = useState([]);
  const [selectedProducto, setSelectedProducto] = useState(null); // Producto seleccionado
  const [cantidad, setCantidad] = useState('');
  const [precio, setPrecio] = useState('');
  const [loading, setLoading] = useState(false);

  // Cargar los clientes y productos desde la API
  useEffect(() => {
    async function fetchData() {
      const fetchedClientes = await fetchClientes(); // Llamada a la API para obtener clientes
      const fetchedProductos = await fetchProductos(); // Llamada a la API para obtener productos
      setClientes(fetchedClientes);
      setProductos(fetchedProductos);
    }

    fetchData();
  }, []);

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

  // Agregar un producto con cantidad y precio
  const handleAgregarProducto = () => {
    if (!selectedProducto || !cantidad || !precio) {
      alert("Por favor, complete todos los campos.");
      return;
    }

    const nuevoProducto = {
      producto: selectedProducto.label,
      precio: parseFloat(precio),
      cantidad: parseInt(cantidad),
      total: parseFloat(cantidad) * parseFloat(precio),
    };

    setNewVenta((prevState) => ({
      ...prevState,
      productos: [...prevState.productos, nuevoProducto],
      total: prevState.total + nuevoProducto.total, // Actualiza el total de la venta
    }));

    // Reiniciar los inputs después de agregar
    setCantidad('');
    setPrecio('');
    setSelectedProducto(null);
  };

  // Manejar el submit del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Establecer la fecha actual cuando se haga el submit
    const currentDate = new Date().toLocaleString(); // Puedes usar `toISOString()` si prefieres ese formato
    newVenta.fecha = currentDate;

    try {
      await createVenta(newVenta);
      
      setNewVenta({
        fecha: '',
        cliente: '',
        total: 0,
        moneda: '',
        canal: '',
        productos: [],
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
    navigate('/ventasNeo4j'); // Redirige a la página de ventas
  };

  return (
    <div className="container">
      {/* Botón Volver */}
      <button className="back-btn" onClick={handleVolver}>Volver</button>

      {/* Encabezado de la factura */}
      <h2>Crear Venta</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-header">
          {/* Select de clientes */}
          <Select
            options={clienteOptions}
            onChange={(selectedOption) => handleSelectChange(selectedOption, 'cliente')}
            placeholder="Selecciona un Cliente"
            isClearable
          />
        </div>

        <div className="form-details">
          {/* Select de moneda */}
          <select
            name="moneda"
            value={newVenta.moneda}
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una Moneda</option>
            <option value="USD">USD</option>
            <option value="CRC">CRC</option>
          </select>

          {/* Select de canal */}
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
        </div>

        {/* Formulario para agregar productos */}
        <div className="product-form">
          <h3>Agregar Producto</h3>
          <div className="form-inputs">
            <div className="input-column">
              <Select
                options={productoOptions}
                onChange={setSelectedProducto}
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
