DECLARE @MesActual INT;
DECLARE @AnioActual INT = 2024;

WHILE @AnioActual <= 2025
BEGIN
    SET @MesActual = 1;

    WHILE @MesActual <= 12
    BEGIN

        INSERT INTO MetasVentas (idCliente, idProducto, anio, mes, metaUSD)
        SELECT 
            base.idCliente,
            base.idProducto,
            @AnioActual AS anio,
            @MesActual AS mes,

            CASE 
                WHEN base.metaBase * var.factor < 50 THEN 50
                WHEN base.metaBase * var.factor > 2500 THEN 2500
                ELSE base.metaBase * var.factor
            END AS metaUSD
        FROM
        (
            -- ================================
            -- 1) SUMA REAL DEL MES (por cliente y producto)
            -- ================================
            SELECT 
                v.idCliente,
                v.idProducto,
                CASE 
                    WHEN @AnioActual = 2024 THEN SUM(v.totalVenta) * 1.05
                    ELSE SUM(v.totalVenta) * 1.10
                END AS metaBase
            FROM FACT_Ventas v
            INNER JOIN DIM_Tiempo t ON v.idTiempo = t.idTiempo
            WHERE t.anio = @AnioActual
                AND t.mes = @MesActual
            GROUP BY v.idCliente, v.idProducto
        ) base

        CROSS APPLY (
            -- ================================
            -- 2) VARIACIÓN –40% A +40%
            -- ================================
            SELECT (1 + ((RAND(CHECKSUM(NEWID())) * 0.80) - 0.40)) AS factor
        ) var;

        SET @MesActual = @MesActual + 1;
    END;

    SET @AnioActual = @AnioActual + 1;
END;
