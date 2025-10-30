CREATE TABLE DIM_Cliente (
    idCliente INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(120) NOT NULL,
    email NVARCHAR(150) NOT NULL UNIQUE,
    genero NVARCHAR(12) CHECK (Genero IN ('Masculino', 'Femenino', 'Otro')),
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
    numeroMes INT NOT NULL
);
GO

CREATE TABLE FACT_Ventas (
    idVenta INT IDENTITY PRIMARY KEY,
    idCliente INT NOT NULL FOREIGN KEY REFERENCES DIM_Cliente(idCliente),
    idProducto INT NOT NULL FOREIGN KEY REFERENCES DIM_Producto(idProducto),
    idTiempo INT NOT NULL FOREIGN KEY REFERENCES DIM_Tiempo(idTiempo),
    canal NVARCHAR(20) NOT NULL CHECK (Canal IN ('WEB', 'TIENDA', 'APP')),
    cantidad INT NOT NULL,
    precioUnitario DECIMAL(18, 2) NOT NULL,
    descuentoPct DECIMAL(5, 2) NOT NULL,
    totalVenta DECIMAL(18, 2) NOT NULL,
    moneda CHAR(3) NOT NULL,
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
