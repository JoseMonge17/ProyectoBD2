// Obtener todos los productos
MATCH (p:Producto)
WITH p
// Generar un número aleatorio entre 1 y 3 para decidir cuántos campos eliminar (1 o 2)
WITH p, toInteger(rand() * 2) + 1 AS numToRemove
// Si numToRemove es 1 o 2, eliminamos uno o dos campos aleatorios, asegurando que al menos uno se quede
WITH p, numToRemove, [p.sku, p.codigo_alt, p.codigo_mongo] AS fields
// Si numToRemove es 1, eliminamos uno de los campos aleatoriamente
FOREACH (ignore IN CASE WHEN numToRemove = 1 THEN [1] ELSE [] END | 
    // Seleccionamos aleatoriamente uno de los tres campos para eliminar
    FOREACH (ignore2 IN CASE WHEN rand() < 0.33 THEN [1] ELSE [] END | REMOVE p.sku)
    FOREACH (ignore2 IN CASE WHEN rand() >= 0.33 AND rand() < 0.66 THEN [1] ELSE [] END | REMOVE p.codigo_alt)
    FOREACH (ignore2 IN CASE WHEN rand() >= 0.66 THEN [1] ELSE [] END | REMOVE p.codigo_mongo)
)
// Si numToRemove es 2, eliminamos dos de los tres campos
FOREACH (ignore IN CASE WHEN numToRemove = 2 THEN [1] ELSE [] END | 
    // Seleccionamos aleatoriamente dos de los tres campos para eliminar
    FOREACH (ignore2 IN CASE WHEN rand() < 0.5 THEN [1] ELSE [] END | REMOVE p.sku)
    FOREACH (ignore2 IN CASE WHEN rand() >= 0.5 AND rand() < 0.75 THEN [1] ELSE [] END | REMOVE p.codigo_alt)
    FOREACH (ignore2 IN CASE WHEN rand() >= 0.75 THEN [1] ELSE [] END | REMOVE p.codigo_mongo)
)
// Regresar los productos con sus campos modificados
RETURN p;

// Calcular el total de la orden sumando cantidad * precio de las relaciones CONTIENTE
MATCH (o:Orden)-[r:CONTIENTE]->(p:Producto)
WITH o, r, p, r.cantidad * r.precio AS total_producto
// Sumar los totales de todos los productos relacionados con la orden
WITH o, SUM(total_producto) AS nuevo_total
// Actualizar el total de la orden
SET o.total = nuevo_total
RETURN o.id AS orden_id, o.total AS nuevo_total
