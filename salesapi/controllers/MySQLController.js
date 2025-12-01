const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const LOADER_SCRIPT_PATH = path.join(__dirname, '../../MySQL/Data/loader.py');

const ejecutarLoader = async (req, res) => {
  console.log('🔄 Iniciando Loader de MySQL...');
  console.log('📂 Script:', LOADER_SCRIPT_PATH);

  if (!fs.existsSync(LOADER_SCRIPT_PATH)) {
    return res.status(404).json({
      success: false,
      message: 'Script loader de MySQL no encontrado',
      path: LOADER_SCRIPT_PATH
    });
  }

  try {
    const pythonProcess = spawn('python', [LOADER_SCRIPT_PATH]);

    let stdoutData = '';
    let stderrData = '';

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('📤 Python stdout (MySQL):', output);
      stdoutData += output;
    });

    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      console.error('❌ Python stderr (MySQL):', error);
      stderrData += error;
    });

    pythonProcess.on('close', (code) => {
      console.log(`🏁 Proceso Loader MySQL terminado con código: ${code}`);

      // Extraer estadísticas del output
      const estadisticas = extraerEstadisticas(stdoutData);

      if (code === 0) {
        res.json({
          success: true,
          message: 'Loader MySQL ejecutado exitosamente',
          estadisticas: estadisticas,
          output: stdoutData,
          exitCode: code
        });
      } else {
        res.status(500).json({
          success: false,
          message: 'El proceso Loader MySQL finalizó con errores',
          error: stderrData || stdoutData,
          estadisticas: estadisticas,
          exitCode: code
        });
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('❌ Error al ejecutar Python (MySQL):', error);
      res.status(500).json({
        success: false,
        message: 'Error al ejecutar el script Loader MySQL',
        error: error.message
      });
    });

  } catch (error) {
    console.error('❌ Error en ejecutarLoader MySQL:', error);
    res.status(500).json({
      success: false,
      message: 'Error al iniciar el proceso Loader MySQL',
      error: error.message
    });
  }
};

// Función para extraer estadísticas del output del script MySQL
function extraerEstadisticas(output) {
  const estadisticas = {
    clientes: 0,
    productos: 0,
    ordenes: 0,
    detalles: 0
  };

  // Buscar líneas específicas del output
  const lineas = output.split('\n');
  lineas.forEach(linea => {
    // Buscar patrones del script MySQL
    if (linea.includes('clientes cargados') || linea.includes('CLIENTES:')) {
      const match = linea.match(/(\d+)\s+clientes/);
      if (match) estadisticas.clientes = parseInt(match[1]);
    }
    if (linea.includes('productos cargados') || linea.includes('PRODUCTOS:')) {
      const match = linea.match(/(\d+)\s+productos/);
      if (match) estadisticas.productos = parseInt(match[1]);
    }
    if (linea.includes('órdenes cargadas') || linea.includes('ORDENES:')) {
      const match = linea.match(/(\d+)\s+órdenes/);
      if (match) estadisticas.ordenes = parseInt(match[1]);
    }
    if (linea.includes('detalles cargados') || linea.includes('DETALLES:')) {
      const match = linea.match(/(\d+)\s+detalles/);
      if (match) estadisticas.detalles = parseInt(match[1]);
    }
    
    // También buscar patrones genéricos
    if (!estadisticas.clientes) {
      const match = linea.match(/CLIENTES:\s*(\d+)/i);
      if (match) estadisticas.clientes = parseInt(match[1]);
    }
    if (!estadisticas.productos) {
      const match = linea.match(/PRODUCTOS:\s*(\d+)/i);
      if (match) estadisticas.productos = parseInt(match[1]);
    }
    if (!estadisticas.ordenes) {
      const match = linea.match(/ORDENES:\s*(\d+)/i);
      if (match) estadisticas.ordenes = parseInt(match[1]);
    }
    if (!estadisticas.detalles) {
      const match = linea.match(/DETALLES:\s*(\d+)/i);
      if (match) estadisticas.detalles = parseInt(match[1]);
    }
  });

  return estadisticas;
}

module.exports = {
  ejecutarLoader
};