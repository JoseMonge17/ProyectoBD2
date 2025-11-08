//Categorias
UNWIND [
  'Electrónica','Hogar','Alimentos','Belleza','Ropa y Calzado',
  'Deportes','Jardín','Oficina','Mascotas','Salud'
] AS cat
MERGE (k:Categoria {id: cat})
  ON CREATE SET k.nombre = cat;

//Productos y relaciones con su respectiva categoria
WITH [
  'Electrónica','Hogar','Alimentos','Belleza','Ropa y Calzado',
  'Deportes','Jardín','Oficina','Mascotas','Salud'
] AS cats
UNWIND range(1,100) AS i
WITH i, cats,
     cats[toInteger(floor(rand()*size(cats)))] AS cat
WITH i, cat,
     'SKU-' + toString(1000 + i) AS sku,
     'ALT-' + toString(2000 + i) AS alt,
     'MN-'  + toString(3000 + i) AS mg
CREATE (p:Producto {
  id: toString(randomUUID()),
  sku: sku,
  nombre: 'Producto ' + toString(i),
  categoria: cat,
  codigo_alt: alt,
  codigo_mongo: mg
})
WITH p
MATCH (k:Categoria {id: p.categoria})
MERGE (p)-[:PERTENECE_A]->(k);

//Clientes
WITH ['M','F','Masculino','Femenino','Otro'] AS generos,
     ['CR','PA','HN','US','MX','CO'] AS paises
UNWIND range(1,600) AS i
WITH i, generos, paises,
     generos[toInteger(floor(rand()*size(generos)))] AS g,
     paises[toInteger(floor(rand()*size(paises)))]  AS pais
MERGE (c:Cliente {id: 'C' + toString(100000 + i)})
  ON CREATE SET
    c.nombre = 'Cliente ' + toString(i),
    c.genero = g,
    c.pais   = pais;

// Ordenes
MATCH (c:Cliente) WITH collect(c) AS cs
MATCH (p:Producto) WITH cs, collect(p) AS ps, date('2024-01-01') AS d0

UNWIND range(1,5000) AS i
WITH cs, ps, d0,
     cs[toInteger(floor(rand()*size(cs)))] AS c,
     d0 + duration({days: toInteger(floor(rand()*676))}) AS dd,
     ['WEB','TIENDA','APP','PARTNER'] AS canales,
     ['USD','CRC'] AS monedas
WITH c, ps, dd, canales, monedas,
     datetime({date: dd, time: time({hour: 12, minute: toInteger(floor(rand()*60))})}) AS fecha,
     canales[toInteger(floor(rand()*size(canales)))] AS canal,
     monedas[toInteger(floor(rand()*size(monedas)))] AS moneda
CREATE (o:Orden {id: randomUUID(), fecha: fecha, canal: canal, moneda: moneda, total: 0.0})
MERGE (c)-[:REALIZO]->(o)
WITH o, ps, moneda, toInteger(1 + floor(rand()*5)) AS renglones

UNWIND range(1, renglones) AS _
WITH o, ps, moneda,
     ps[toInteger(floor(rand()*size(ps)))] AS p,
     toInteger(1 + floor(rand()*4)) AS qty,
     CASE
       WHEN moneda = 'USD' THEN round(5 + rand()*95, 2)        // 5–100 USD
       ELSE toInteger(1000 + rand()*49000)                      // 1 000–50000 CRC
     END AS unit
CREATE (o)-[:CONTIENTE {cantidad: qty, precio_unit: unit}]->(p)
WITH o
MATCH (o)-[r:CONTIENTE]->()
WITH o, sum(toFloat(r.cantidad) * toFloat(r.precio_unit)) AS tot
SET o.total = round(tot, 2);






