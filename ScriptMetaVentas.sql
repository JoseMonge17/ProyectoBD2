DECLARE @MesActual INT = 1;
DECLARE @AnioActual INT = 2024;

WHILE @AnioActual <= 2025
BEGIN
    SET @MesActual = 1;
    WHILE @MesActual <= 12
    BEGIN
        INSERT INTO MetasVentas (idCliente, idProducto, anio, mes, metaUSD)
        SELECT 
            v.idCliente,
            v.idProducto,
            @AnioActual AS anio,
            @MesActual AS mes,
            -- META CALCULADA PARA QUE EL % ESTÉ ENTRE 70% Y 120%
            SUM(v.totalVenta) / 
            (0.70 + (RAND(CHECKSUM(NEWID())) * 0.50))  -- Divisor entre 0.70 y 1.20
            AS metaUSD
        FROM FACT_Ventas v
        INNER JOIN DIM_Tiempo t ON v.idTiempo = t.idTiempo
        WHERE t.anio = @AnioActual
          AND t.mes = @MesActual
        GROUP BY v.idCliente, v.idProducto;
        
        SET @MesActual = @MesActual + 1;
    END;
    SET @AnioActual = @AnioActual + 1;
END;