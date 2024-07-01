#--------------------------------------------------------------------
# Instalar con pip install Flask
from flask import Flask, request, jsonify
#from flask import request

# Instalar con pip install flask-cors
from flask_cors import CORS

# Instalar con pip install mysql-connector-python
import mysql.connector

# Si es necesario, pip install Werkzeug
from werkzeug.utils import secure_filename

# No es necesario instalar, es parte del sistema standard de Python
import os
import time
#--------------------------------------------------------------------



app = Flask(__name__)
CORS(app) # Esto habilitará CORS para todas las rutas

#--------------------------------------------------------------------
class Catalogo:
    #----------------------------------------------------------------
    # Constructor de la clase
    def __init__(self, host, user, password, database):
        # Primero, establecemos una conexión sin especificar la base de datos
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

        # Intentamos seleccionar la base de datos
        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        # Una vez que la base de datos está establecida, creamos la tabla si no existe
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS contactos (
            codigo INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            surname VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            imagen_url VARCHAR(255),
            phone VARCHAR(255))''')
        self.conn.commit()

        # Cerrar el cursor inicial y abrir uno nuevo con el parámetro dictionary=True
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)
        
    #----------------------------------------------------------------
    def agregar_contacto(self, name, surname, email, imagen, phone):
               
        sql = "INSERT INTO contactos (name, surname, email, imagen_url, phone) VALUES (%s, %s, %s, %s, %s)"
        valores = (name, surname, email, imagen, phone)

        self.cursor.execute(sql, valores)        
        self.conn.commit()
        return self.cursor.lastrowid

    #----------------------------------------------------------------
    def consultar_contacto(self, codigo):
        # Consultamos un contacto a partir de su código
        self.cursor.execute(f"SELECT * FROM contactos WHERE codigo = {codigo}")
        return self.cursor.fetchone()

    #----------------------------------------------------------------
    def modificar_contacto(self, codigo, nueva_name, nueva_surname, nuevo_email, nueva_imagen, nuevo_phone):
        sql = "UPDATE contactos SET name = %s, surname = %s, email = %s, imagen_url = %s, phone = %s WHERE codigo = %s"
        valores = (nueva_name, nueva_surname, nuevo_email, nueva_imagen, nuevo_phone, codigo)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------
    def listar_contactos(self):
        self.cursor.execute("SELECT * FROM contactos")
        contactos = self.cursor.fetchall()
        return contactos

    #----------------------------------------------------------------
    def eliminar_contacto(self, codigo):
        # Eliminamos un contacto de la tabla a partir de su código
        self.cursor.execute(f"DELETE FROM contactos WHERE codigo = {codigo}")
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------
    def mostrar_contacto(self, codigo):
        # Mostramos los datos de un contacto a partir de su código
        contacto = self.consultar_contacto(codigo)
        if contacto:
            print("-" * 40)
            print(f"Código.....: {contacto['codigo']}")
            print(f"Nombre.....: {contacto['name']}")
            print(f"Apellido...: {contacto['surname']}")
            print(f"Email......: {contacto['email']}")
            print(f"Imagen.....: {contacto['imagen_url']}")
            print(f"Teléfono...: {contacto['phone']}")
            print("-" * 40)
        else:
            print("Contactos no encontrado.")


#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------
# Crear una instancia de la clase Catalogo
# catalogo = Catalogo(host='localhost', user='root', password='', database='backend_db')
catalogo = Catalogo(host='ngatti68.mysql.pythonanywhere-services.com', user='ngatti68', password='lc1d09m7MySQL', database='ngatti68$backend_db')


# Carpeta para guardar las imagenes.
# RUTA_DESTINO = './static/imagenes'

#Al subir al servidor, deberá utilizarse la siguiente ruta. USUARIO debe ser reemplazado por el nombre de usuario de Pythonanywhere
RUTA_DESTINO = '/home/ngatti68/mysite/static/imagenes'


#--------------------------------------------------------------------
# Listar todos los contactos
#--------------------------------------------------------------------
#La ruta Flask /contactos con el método HTTP GET está diseñada para proporcionar los detalles de todos los contactos almacenados en la base de datos.
#El método devuelve una lista con todos los contactos en formato JSON.
@app.route("/contactos", methods=["GET"])
def listar_contactos():
    contactos = catalogo.listar_contactos()
    return jsonify(contactos)


#--------------------------------------------------------------------
# Mostrar un sólo contacto según su código
#--------------------------------------------------------------------
#La ruta Flask /contactos/<int:codigo> con el método HTTP GET está diseñada para proporcionar los detalles de un contacto específico basado en su código.
#El método busca en la base de datos el contacto con el código especificado y devuelve un JSON con los detalles del contacto si lo encuentra, o None si no lo encuentra.
@app.route("/contactos/<int:codigo>", methods=["GET"])
def mostrar_contacto(codigo):
    contacto = catalogo.consultar_contacto(codigo)
    if contacto:
        return jsonify(contacto), 201
    else:
        return "Contacto no encontrado", 404


#--------------------------------------------------------------------
# Agregar un contacto
#--------------------------------------------------------------------
@app.route("/contactos", methods=["POST"])
#La ruta Flask `/contactos` con el método HTTP POST está diseñada para permitir la adición de un nuevo contacto a la base de datos.
#La función agregar_contacto se asocia con esta URL y es llamada cuando se hace una solicitud POST a /contactos.
def agregar_contacto():
    #Recojo los datos del form
    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']
    imagen = request.files['imagen']
    phone = request.form['phone']  
    nombre_imagen=""

    
    # Genero el nombre de la imagen
    nombre_imagen = secure_filename(imagen.filename) #Chequea el nombre del archivo de la imagen, asegurándose de que sea seguro para guardar en el sistema de archivos
    nombre_base, extension = os.path.splitext(nombre_imagen) #Separa el nombre del archivo de su extensión.
    nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" #Genera un nuevo nombre para la imagen usando un timestamp, para evitar sobreescrituras y conflictos de nombres.

    nuevo_codigo = catalogo.agregar_contacto(name, surname, email, nombre_imagen, phone)
    if nuevo_codigo:    
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

        #Si el contacto se agrega con éxito, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 201 (Creado).
        return jsonify({"mensaje": "Contacto agregado correctamente.", "codigo": nuevo_codigo, "imagen": nombre_imagen}), 201
    else:
        #Si el contacto no se puede agregar, se devuelve una respuesta JSON con un mensaje de error y un código de estado HTTP 500 (Internal Server Error).
        return jsonify({"mensaje": "Error al agregar el contacto."}), 500
    

#--------------------------------------------------------------------
# Modificar un contacto según su código
#--------------------------------------------------------------------
@app.route("/contactos/<int:codigo>", methods=["PUT"])
#La ruta Flask /contactos/<int:codigo> con el método HTTP PUT está diseñada para actualizar la información de un contacto existente en la base de datos, identificado por su código.
#La función modificar_contacto se asocia con esta URL y es invocada cuando se realiza una solicitud PUT a /contactos/ seguido de un número (el código del contacto).
def modificar_contacto(codigo):
    #Se recuperan los nuevos datos del formulario
    nueva_name = request.form.get("name")
    nueva_surname = request.form.get("surname")
    nuevo_email = request.form.get("email")
    nuevo_phone = request.form.get("phone")
    
    
    # Verifica si se proporcionó una nueva imagen
    if 'imagen' in request.files:
        imagen = request.files['imagen']
        # Procesamiento de la imagen
        nombre_imagen = secure_filename(imagen.filename) #Chequea el nombre del archivo de la imagen, asegurándose de que sea seguro para guardar en el sistema de archivos
        nombre_base, extension = os.path.splitext(nombre_imagen) #Separa el nombre del archivo de su extensión.
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" #Genera un nuevo nombre para la imagen usando un timestamp, para evitar sobreescrituras y conflictos de nombres.

        # Guardar la imagen en el servidor
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))
        
        # Busco el contacto guardado
        contacto = catalogo.consultar_contacto(codigo)
        if contacto: # Si existe el contacto...
            imagen_vieja = contacto["imagen_url"]
            # Armo la ruta a la imagen
            ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

            # Y si existe la borro.
            if os.path.exists(ruta_imagen):
                os.remove(ruta_imagen)
    
    else:
        # Si no se proporciona una nueva imagen, simplemente usa la imagen existente del contacto
        contacto = catalogo.consultar_contacto(codigo)
        if contacto:
            nombre_imagen = contacto["imagen_url"]


    # Se llama al método modificar_contacto pasando el codigo del contacto y los nuevos datos.
    if catalogo.modificar_contacto(codigo, nueva_name, nueva_surname, nuevo_email, nombre_imagen, nuevo_phone):
        
        #Si la actualización es exitosa, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
        return jsonify({"mensaje": "Contacto modificado"}), 200
    else:
        #Si el contacto no se encuentra (por ejemplo, si no hay ningún contacto con el código dado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado).
        return jsonify({"mensaje": "Contacto no encontrado"}), 403



#--------------------------------------------------------------------
# Eliminar un contacto según su código
#--------------------------------------------------------------------
@app.route("/contactos/<int:codigo>", methods=["DELETE"])
#La ruta Flask /contactos/<int:codigo> con el método HTTP DELETE está diseñada para eliminar un contacto específico de la base de datos, utilizando su código como identificador.
#La función eliminar_contacto se asocia con esta URL y es llamada cuando se realiza una solicitud DELETE a /contactos/ seguido de un número (el código del contacto).
def eliminar_contacto(codigo):
    # Busco el contacto en la base de datos
    contacto = catalogo.consultar_contacto(codigo)
    if contacto: # Si el contacto existe, verifica si hay una imagen asociada en el servidor.
        imagen_vieja = contacto["imagen_url"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe, la elimina del sistema de archivos.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

        # Luego, elimina el contacto del catálogo
        if catalogo.eliminar_contacto(codigo):
            #Si el contacto se elimina correctamente, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
            return jsonify({"mensaje": "Contacto eliminado"}), 200
        else:
            #Si ocurre un error durante la eliminación (por ejemplo, si el contacto no se puede eliminar de la base de datos por alguna razón), se devuelve un mensaje de error con un código de estado HTTP 500 (Error Interno del Servidor).
            return jsonify({"mensaje": "Error al eliminar el contacto"}), 500
    else:
        #Si el contacto no se encuentra (por ejemplo, si no existe un contacto con el codigo proporcionado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado). 
        return jsonify({"mensaje": "Contacto no encontrado"}), 404

#--------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)