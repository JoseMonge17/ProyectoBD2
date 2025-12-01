import React, { useState } from 'react';
import './LoaderPage.css';

const LoaderPage = () => {
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  const ejecutarLoader = async () => {
    setLoading(true);
    setResultado(null);
    setError(null);

    try {
      // Endpoint específico para MySQL
      const response = await fetch('http://localhost:5000/api/mysql/loader', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Verificar si la respuesta es JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.error('Respuesta no JSON:', textResponse.substring(0, 200));
        throw new Error(`El servidor respondió con: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `Error ${response.status}: ${response.statusText}`);
      }

      setResultado(data);
    } catch (err) {
      console.error('Error completo:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="loader-container">
      <div className="loader-header">
        <h1>🐬 Loader de MySQL</h1>
        <p>Carga masiva de datos en MySQL</p>
      </div>

      <div className="loader-card">
        <div className="loader-info">
          <h3>Información del Loader MySQL</h3>
          <ul>
            <li>Carga datos desde archivos CSV específicos para MySQL</li>
            <li>Inserta en base de datos MySQL (sales_mysql)</li>
            <li>Genera datos masivos para pruebas</li>
            <li>Incluye validación de datos y estructura</li>
            <li>Conexión a MySQL en Docker (puerto 3307)</li>
          </ul>
        </div>

        <button 
          className="loader-button"
          onClick={ejecutarLoader}
          disabled={loading}
        >
          {loading ? '🔄 Ejecutando...' : '🐬 Ejecutar Loader MySQL'}
        </button>

        {loading && (
          <div className="loading-section">
            <div className="spinner"></div>
            <p>Procesando datos en MySQL... Esto puede tomar unos segundos</p>
          </div>
        )}

        {resultado && (
          <div className="result-section">
            <h3>✅ Loader MySQL Completado</h3>
            
            {resultado.estadisticas && (
              <div className="estadisticas">
                <h4>📊 Estadísticas de Carga MySQL:</h4>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span className="stat-number">{resultado.estadisticas.clientes}</span>
                    <span className="stat-label">Clientes</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-number">{resultado.estadisticas.productos}</span>
                    <span className="stat-label">Productos</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-number">{resultado.estadisticas.ordenes}</span>
                    <span className="stat-label">Órdenes</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-number">{resultado.estadisticas.detalles}</span>
                    <span className="stat-label">Detalles</span>
                  </div>
                </div>
              </div>
            )}

            <div className="output-section">
              <h4>📝 Output del Proceso MySQL:</h4>
              <pre className="output-log">{resultado.output}</pre>
            </div>
          </div>
        )}

        {error && (
          <div className="error-section">
            <h3>❌ Error en Loader MySQL</h3>
            <p>{error}</p>
            {resultado && resultado.output && (
              <div className="output-section">
                <h4>Output del Error:</h4>
                <pre className="output-log error-log">{resultado.output}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LoaderPage;