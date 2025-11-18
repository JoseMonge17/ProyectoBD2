-- Crear la base de datos
CREATE DATABASE Ventas_Transactional;
GO

USE Ventas_Transactional;
GO

-- Crear el esquema para las ventas de MS SQL Server
CREATE SCHEMA sales_ms;
GO

-- Tabla Cliente
CREATE TABLE sales_ms.Cliente (
    ClienteId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(120) NOT NULL,
    Email NVARCHAR(150) UNIQUE,
    Genero NVARCHAR(12) CHECK (Genero IN ('Masculino','Femenino')),
    Pais NVARCHAR(60) NOT NULL,
    FechaRegistro DATE NOT NULL DEFAULT (GETDATE())
);

-- Tabla Producto
CREATE TABLE sales_ms.Producto (
    ProductoId INT IDENTITY(1,1) PRIMARY KEY,
    SKU NVARCHAR(40) UNIQUE NOT NULL,  -- SKU "oficial"
    Nombre NVARCHAR(150) NOT NULL,
    Categoria NVARCHAR(80) NOT NULL
);

-- Tabla Orden
CREATE TABLE sales_ms.Orden (
    OrdenId INT IDENTITY(1,1) PRIMARY KEY,
    ClienteId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Cliente(ClienteId),
    Fecha DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
    Canal NVARCHAR(20) NOT NULL CHECK (Canal IN ('WEB','TIENDA','APP')),
    Moneda CHAR(3) NOT NULL DEFAULT 'USD',
    Total DECIMAL(18,2) NOT NULL
);

-- Tabla OrdenDetalle
CREATE TABLE sales_ms.OrdenDetalle (
    OrdenDetalleId INT IDENTITY(1,1) PRIMARY KEY,
    OrdenId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Orden(OrdenId),
    ProductoId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Producto(ProductoId),
    Cantidad INT NOT NULL CHECK (Cantidad > 0),
    PrecioUnit DECIMAL(18,2) NOT NULL,  -- en USD
    DescuentoPct DECIMAL(5,2) NULL
);

-- Índices para optimización
CREATE INDEX IX_Orden_Fecha ON sales_ms.Orden(Fecha);
CREATE INDEX IX_Orden_Cliente ON sales_ms.Orden(ClienteId);
CREATE INDEX IX_Detalle_Orden ON sales_ms.OrdenDetalle(OrdenId);
CREATE INDEX IX_Detalle_Prod ON sales_ms.OrdenDetalle(ProductoId);
CREATE INDEX IX_Cliente_Email ON sales_ms.Cliente(Email);
CREATE INDEX IX_Producto_SKU ON sales_ms.Producto(SKU);