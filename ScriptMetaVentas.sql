
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

            -- META BASE MÁS REALISTA
            CASE 
                WHEN @AnioActual = 2024 THEN 
                    SUM(v.totalVenta) * 1.05    -- solo +5%
                ELSE
                    SUM(v.totalVenta) * 1.10    -- segundo año +10%
            END
            *
            (1 + ((RAND(CHECKSUM(NEWID())) * 0.10) - 0.05))  -- variación ±5%

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
