// Calcular el total de la orden sumando cantidad * precio de las relaciones CONTIENTE
MATCH (o:Orden)-[r:CONTIENTE]->(p:Producto)
WITH o, r, p, r.cantidad * r.precio AS total_producto
// Sumar los totales de todos los productos relacionados con la orden
WITH o, SUM(total_producto) AS nuevo_total
// Actualizar el total de la orden
SET o.total = nuevo_total
RETURN o.idOrden AS orden_id, o.total AS nuevo_total
