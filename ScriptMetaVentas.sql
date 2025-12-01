-- ============================
-- GENERACIÓN DE METAS MEJORADA
-- ============================

DECLARE @Meses TABLE (mes INT);
INSERT INTO @Meses VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12);

DECLARE @AnioActual INT = 2024;

WHILE @AnioActual <= 2025
BEGIN
    PRINT 'Procesando año: ' + CAST(@AnioActual AS NVARCHAR(4));

    DECLARE @MesActual INT = 1;

    WHILE @MesActual <= 12
    BEGIN
        -- Inserta metas por cliente y producto, con variación controlada
        INSERT INTO MetasVentas (idCliente, idProducto, anio, mes, metaUSD)
        SELECT 
            v.idCliente,
            v.idProducto,
            @AnioActual AS anio,
            @MesActual AS mes,

            -- ============================
            --  CÁLCULO BASE (suma del mes)
            -- ============================
            CASE 
                WHEN @AnioActual = 2024 THEN 
                    CASE 
                        WHEN SUM(v.totalVenta) * 1.15 < 100 THEN 100
                        WHEN SUM(v.totalVenta) * 1.15 > 8000 THEN 8000
                        ELSE SUM(v.totalVenta) * 1.15
                    END
                ELSE -- 2025
                    CASE 
                        WHEN SUM(v.totalVenta) * 1.20 < 100 THEN 100
                        WHEN SUM(v.totalVenta) * 1.20 > 10000 THEN 10000
                        ELSE SUM(v.totalVenta) * 1.20
                    END
            END

            -- ============================
            --   VARIACIÓN ALEATORIA ±8%
            -- ============================
            *
            (1 + ((RAND(CHECKSUM(NEWID())) * 0.16) - 0.08))  -- -8% a +8%

            AS metaUSD

        FROM FACT_Ventas v
        INNER JOIN DIM_Tiempo t ON v.idTiempo = t.idTiempo
        WHERE t.anio = @AnioActual 
            AND t.mes = @MesActual
        GROUP BY v.idCliente, v.idProducto;

        SET @MesActual = @MesActual + 1;
    END

    SET @AnioActual = @AnioActual + 1;
END


-- mostrar resultado
SELECT 
    'Proceso completado' AS Estado,
    (SELECT COUNT(*) FROM MetasVentas WHERE anio = 2024) AS Metas2024,
    (SELECT COUNT(*) FROM MetasVentas WHERE anio = 2025) AS Metas2025;
