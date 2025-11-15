import csv
import uuid
import random
from datetime import datetime, timedelta

# Listas ampliadas
nombres_m = [
    "Juan","Carlos","Diego","Andres","Luis","Jorge","Fernando","Miguel","Ricardo",
    "Rafael","Sergio","Pedro","Pablo","Roberto","Mario","Gabriel","Eduardo","Julio",
    "Hector","Raul","Esteban","Oscar","Alfonso","Ruben","Samuel","Antonio","Arturo",
    "Francisco","Jose","Adrian","Bruno","Cristian","David","Ernesto","Felipe","Ignacio",
    "Ivan","Javier","Leonardo","Manuel","Mauricio","Nicolas","Orlando","Rodolfo","Sebastian",
    "Tomas","Victor","Wilson","Alex","Benjamin","Camilo","Dario","Emilio","Federico","Hernan",
    "Luciano","Marcos","Renato","Santiago","Ulises","Valentin","Guillermo","Alejandro","Cesar",
    "Hugo","Lorenzo","Ramon","Teodoro"
]

nombres_f = [
    "Maria","Ana","Laura","Daniela","Carolina","Patricia","Sofia","Valeria","Claudia",
    "Isabel","Monica","Beatriz","Gabriela","Lucia","Silvia","Adriana","Veronica","Sandra",
    "Carmen","Diana","Andrea","Rosa","Gloria","Teresa","Lorena","Paola","Marina","Alicia",
    "Vanessa","Natalia","Camila","Julieta","Alejandra","Noelia","Viviana","Renata","Estefania",
    "Elena","Marta","Liliana","Angela","Tatiana","Ines","Fernanda","Jimena","Clara","Susana",
    "Evelyn","Nicole","Rocio","Cecilia","Carla","Melina","Pamela","Rebeca","Tania","Lidia",
    "Florencia","Milagros","Bianca","Catalina","Yolanda","Miriam","Belinda","Adela","Josefina",
    "Aurora","Yesenia"
]

apellidos = [
    "Perez","Gonzalez","Lopez","Martinez","Rodriguez","Diaz","Torres","Ramirez","Sanchez",
    "Castro","Morales","Herrera","Ortega","Romero","Vargas","Mendoza","Rios","Cordero",
    "Jimenez","Navarro","Reyes","Fernandez","Suarez","Mora","Salazar","Cruz","Montes",
    "Nunez","Pena","Cortes","Blanco","Chavez","Fuentes","Leon","Campos","Guzman","Vega",
    "Solis","Cabrera","Paredes","Acosta","Bermudez","Carrillo","Rosales","Estrada",
    "Maldonado","Aguilar","Mejia","Padilla","Soto","Rivera","Ruiz","Bravo","Ochoa",
    "Delgado","Zamora","Molina","Villalobos","Flores","Escobar","Palacios","Pizarro",
    "Lara","Bautista","Silva","Benitez","Araya","Santos","Moraes","Menendez","Porras",
    "Chacon","Rangel","Tejada","Matos","Pinto","Velasquez","Lobo","Fajardo","Barrios","Hernandez"
]

paises = [
    "Costa Rica","Mexico","España","Colombia","Argentina","Chile","Estados Unidos",
    "Guatemala","Ecuador","Panama","Uruguay","Republica Dominicana","Venezuela",
    "Bolivia","Paraguay","El Salvador","Honduras","Nicaragua","Peru","Brasil",
    "Canada","Italia","Alemania","Francia","Portugal"
]

clientes = []
emails_usados = set()
fecha_inicio = datetime(2023, 1, 1)

for i in range(600):
    genero = random.choice(["M","F"])
    nombre = random.choice(nombres_m if genero == "M" else nombres_f)
    apellido1 = random.choice(apellidos)
    apellido2 = random.choice(apellidos)
    nombre_completo = f"{nombre} {apellido1} {apellido2}"
    pais = random.choice(paises)
    fecha = fecha_inicio + timedelta(days=random.randint(0, 1100))
    fecha_str = fecha.strftime("%Y-%m-%d")

    # generar email único
    base = f"{nombre.lower()}.{apellido1.lower()}"
    email = f"{base}@email.com"
    contador = 1
    while email in emails_usados:
        contador += 1
        email = f"{base}{contador}@email.com"
    emails_usados.add(email)

    cliente_id = str(uuid.uuid4())
    clientes.append([cliente_id, nombre_completo, email, genero, pais, fecha_str])

# Guardar CSV
with open("clientes_supabase_600.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["cliente_id","nombre","email","genero","pais","fecha_registro"])
    writer.writerows(clientes)

print("✅ Archivo 'clientes_supabase_600.csv' creado exitosamente con 600 clientes y emails unicos.")
