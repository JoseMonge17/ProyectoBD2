-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS sales_mysql
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE sales_mysql;

---------------------------------------------------------
-- TABLA: Cliente
CREATE TABLE Cliente (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  correo VARCHAR(150),
  genero ENUM('M','F','X') DEFAULT 'M',
  pais VARCHAR(60) NOT NULL,
  created_at VARCHAR(10) NOT NULL  -- 'YYYY-MM-DD'
);

---------------------------------------------------------
-- TABLA: Producto
CREATE TABLE Producto (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo_alt VARCHAR(64) UNIQUE NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  categoria VARCHAR(80) NOT NULL
);

---------------------------------------------------------
-- TABLA: Orden
CREATE TABLE Orden (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  fecha VARCHAR(19) NOT NULL,       -- 'YYYY-MM-DD HH:MM:SS'
  canal VARCHAR(20) NOT NULL,       -- libre
  moneda CHAR(3) NOT NULL,          -- 'USD' o 'CRC'
  total VARCHAR(20) NOT NULL,       -- '1200.50', '1,200.50', '800'
  FOREIGN KEY (cliente_id) REFERENCES Cliente(id)
);

---------------------------------------------------------
-- TABLA: OrdenDetalle
CREATE TABLE OrdenDetalle (
  id INT AUTO_INCREMENT PRIMARY KEY,
  orden_id INT NOT NULL,
  producto_id INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unit VARCHAR(20) NOT NULL,
  FOREIGN KEY (orden_id) REFERENCES Orden(id),
  FOREIGN KEY (producto_id) REFERENCES Producto(id)
);

---------------------------------------------------------
-- ÍNDICES
CREATE INDEX IX_Orden_cliente ON Orden(cliente_id);
CREATE INDEX IX_Detalle_producto ON OrdenDetalle(producto_id);
CREATE INDEX IX_Orden_fecha ON Orden(fecha);
CREATE INDEX IX_Detalle_orden ON OrdenDetalle(orden_id);
CREATE INDEX IX_Cliente_correo ON Cliente(correo);

