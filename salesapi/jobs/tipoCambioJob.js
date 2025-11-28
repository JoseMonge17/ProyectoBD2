// jobs/exchangeRateJob.js
const cron = require("node-cron");
const { spawn } = require("child_process");
require("dotenv").config();

const PYTHON_TC_PATH = "E:/BD2/Proyecto/ProyectoBD2/tasaCambio.py"; 

function runPythonScript(args = []) {
  return new Promise((resolve, reject) => {
    const process = spawn("python", [PYTHON_TC_PATH, ...args]);

    process.stdout.on("data", data => {
      console.log(`[PYTHON OUT]: ${data}`);
    });

    process.stderr.on("data", data => {
      console.error(`[PYTHON ERROR]: ${data}`);
    });

    process.on("close", code => {
      if (code === 0) {
        resolve(`Python script finished OK`);
      } else {
        reject(`Python script exited with code ${code}`);
      }
    });
  });
}

async function updateExchangeRate() {
  console.log("Ejecutando job: actualización de tipo de cambio...");

  try {
    await runPythonScript();
    console.log("Tipo de cambio actualizado exitosamente.");
  } catch (err) {
    console.error("Error ejecutando el script:", err);
  }
}

// --------- PROGRAMADOR (CRON) --------------
// Corre todos los días a las 5:00 a.m.
// Formato cron: min hora dia mes diaSemana
// 0 5 * * *   = 5:00am todos los días
cron.schedule("22 16 * * *", () => {
  updateExchangeRate();
});

module.exports = {
  updateExchangeRate,
};
