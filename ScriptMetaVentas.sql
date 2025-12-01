-- Esta versión asegura que TODOS los meses tengan metas, incluso si no hubo ventas

-- Tabla temporal con todos los meses
DECLARE @Meses TABLE (mes INT);
INSERT INTO @Meses VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12);

-- Para cada año (2024, 2025)
DECLARE @AnioActual INT = 2024;
WHILE @AnioActual <= 2025
BEGIN
    PRINT 'Procesando año: ' + CAST(@AnioActual AS NVARCHAR(4));
    
    -- Para cada mes
    DECLARE @MesActual INT = 1;
    WHILE @MesActual <= 12
    BEGIN
        -- Insertar metas basadas en ventas del mismo mes (si existen)
        INSERT INTO MetasVentas (idCliente, idProducto, anio, mes, metaUSD)
        SELECT 
            v.idCliente,
            v.idProducto,
            @AnioActual as anio,
            @MesActual as mes,
            CASE 
                WHEN @AnioActual = 2024 THEN 
                    CASE WHEN AVG(v.totalVenta) * 1.15 < 100 THEN 100
                         WHEN AVG(v.totalVenta) * 1.15 > 8000 THEN 8000
                         ELSE ROUND(AVG(v.totalVenta) * 1.15, 2) END
                ELSE -- 2025
                    CASE WHEN AVG(v.totalVenta) * 1.20 < 100 THEN 100
                         WHEN AVG(v.totalVenta) * 1.20 > 10000 THEN 10000
                         ELSE ROUND(AVG(v.totalVenta) * 1.20, 2) END
            END as metaUSD
        FROM FACT_Ventas v
        INNER JOIN DIM_Tiempo t ON v.idTiempo = t.idTiempo
        WHERE t.anio = @AnioActual 
        AND t.mes = @MesActual
        GROUP BY v.idCliente, v.idProducto;
        
        SET @MesActual = @MesActual + 1;
    END
    
    SET @AnioActual = @AnioActual + 1;
END

-- Mostrar resultado final
SELECT 
    'Proceso completado' as Estado,
    (SELECT COUNT(*) FROM MetasVentas WHERE anio = 2024) as Metas2024,
    (SELECT COUNT(*) FROM MetasVentas WHERE anio = 2025) as Metas2025;