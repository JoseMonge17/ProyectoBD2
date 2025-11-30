-- Versión ligeramente mejorada
DECLARE @AnioMeta INT = YEAR(GETDATE()) + 1;

INSERT INTO MetasVentas (idCliente, idProducto, anio, mes, metaUSD)
SELECT 
    v.idCliente,
    v.idProducto,
    @AnioMeta as anio,
    t.mes,
    CASE 
        WHEN AVG(v.totalVenta) * 1.1 < 100 THEN 100
        WHEN AVG(v.totalVenta) * 1.1 > 10000 THEN 10000
        ELSE ROUND(AVG(v.totalVenta) * 1.1, 2)  -- Redondeo a 2 decimales
    END as metaUSD
FROM FACT_Ventas v
INNER JOIN DIM_Tiempo t ON v.idTiempo = t.idTiempo
WHERE t.anio >= YEAR(GETDATE()) - 2  -- Solo últimos 2 años para cálculo
AND NOT EXISTS (
    SELECT 1 FROM MetasVentas mv 
    WHERE mv.idCliente = v.idCliente 
    AND mv.idProducto = v.idProducto 
    AND mv.anio = @AnioMeta 
    AND mv.mes = t.mes
)
GROUP BY v.idCliente, v.idProducto, t.mes
HAVING COUNT(*) >= 2;  -- Mínimo 2 transacciones para promedio confiable