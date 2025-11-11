-- DIMENSIONES
CREATE TABLE DIM_Cliente (
    idCliente INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(120) NOT NULL,
    email NVARCHAR(150) NOT NULL,
    genero NVARCHAR(12) NOT NULL,
    pais NVARCHAR(60) NOT NULL,
    fechaRegistro DATE NOT NULL DEFAULT (GETDATE())
);
GO

CREATE TABLE DIM_Producto (
    idProducto INT IDENTITY PRIMARY KEY,
    sku NVARCHAR(40) NOT NULL UNIQUE,
    nombre NVARCHAR(150) NOT NULL,
    categoria NVARCHAR(80) NOT NULL
);
GO

CREATE TABLE DIM_Tiempo (
    idTiempo INT IDENTITY PRIMARY KEY, 
    fecha DATE NOT NULL,
    anio INT NOT NULL,
    mes INT NOT NULL,
    dia INT NOT NULL,
    trimestre INT NOT NULL,
    numeroMes INT NOT NULL,
    tipoCambio DECIMAL(18,6) NOT NULL
);
GO

CREATE TABLE DIM_Canal (
    idCanal INT IDENTITY PRIMARY KEY,
    canal NVARCHAR(50) NOT NULL UNIQUE
);
GO

-- HECHOS
CREATE TABLE FACT_Ventas (
    idVenta INT IDENTITY PRIMARY KEY,
    idCliente INT NOT NULL FOREIGN KEY REFERENCES DIM_Cliente(idCliente),
    idProducto INT NOT NULL FOREIGN KEY REFERENCES DIM_Producto(idProducto),
    idTiempo  INT NOT NULL FOREIGN KEY REFERENCES DIM_Tiempo(idTiempo),
    idCanal   INT NOT NULL FOREIGN KEY REFERENCES DIM_Canal(idCanal),
    cantidad INT NOT NULL,
    precioUnitario DECIMAL(18, 2) NOT NULL,
    descuentoPct DECIMAL(5, 2) NOT NULL DEFAULT 0,
    totalVenta DECIMAL(18, 2) NOT NULL,
    totalCRC DECIMAL(18, 2) NOT NULL
);
GO

CREATE TABLE MetasVentas (
	idMeta INT IDENTITY PRIMARY KEY,
	idCliente INT NOT NULL FOREIGN KEY REFERENCES DIM_Cliente(idCliente),
	idProducto INT NOT NULL FOREIGN KEY REFERENCES DIM_Producto(idProducto),
	anio INT NOT NULL,
	mes INT NOT NULL,
	metaUSD DECIMAL(18,2) NOT NULL
);
GO

CREATE TABLE EquivalenciasProductos (
    idProducto INT IDENTITY PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    codigo_alterno VARCHAR(50),
    codigo_mongo VARCHAR(50)
);
GO
