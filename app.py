from PIL import Image
import io
import face_recognition
from flask import Flask, request, jsonify
import mysql.connector
import cv2
import numpy as np
from models import Usuario
from flask_cors import CORS
import os
import base64

app = Flask(__name__)
CORS(app)
app.config.from_pyfile('config.py')

db = mysql.connector.connect(
    host=app.config['DB_HOST'],
    user=app.config['DB_USER'],
    password=app.config['DB_PASSWORD'],
    database=app.config['DB_NAME']
)

# Ruta para el registro de usuarios
@app.route('/registro', methods=['POST'])
def registro():
    data = request.json
    username = data['username']
    password = data['password']

    # Leer la imagen en formato base64
    imagen_base64 = data['imagen_rostro']

    # Decodificar la imagen base64 en bytes
    imagen_bytes = base64.b64decode(imagen_base64)

    new_user = Usuario(username, password, imagen_bytes)
    cursor = db.cursor()
    cursor.execute("INSERT INTO usuarios (username, password_hash, imagen_rostro) VALUES (%s, %s, %s)",
                   (new_user.username, new_user.password_hash, imagen_bytes))
    db.commit()
    cursor.close()
    return jsonify({'mensaje': 'Usuario registrado con éxito'})

# Ruta para iniciar sesión con reconocimiento facial
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = %s", (data['username'],))
    user = cursor.fetchone()
    if user:
        stored_password_hash = user[2]

        # Verificar la contraseña ingresada
        if Usuario.verify_password(stored_password_hash, data['password']):
            stored_imagen_longblob = user[3]
            if stored_imagen_longblob:
                print("dentro")
                # Convertir la imagen almacenada en formato longblob a un archivo de imagen JPEG
                stored_imagen = Image.open(io.BytesIO(stored_imagen_longblob))
                stored_imagen.save('stored.jpg', 'JPEG')  # Guardar la imagen como JPEG

                # Convertir la imagen PIL a una matriz NumPy
                stored_imagen_array = np.array(stored_imagen)

                # Obtener ubicaciones faciales
                stored_face_locations = face_recognition.face_locations(stored_imagen_array)
                input_imagen_base64 = data['imagen_rostro']
                input_imagen_bytes = base64.b64decode(input_imagen_base64)
                input_imagen = Image.open(io.BytesIO(input_imagen_bytes))
                input_imagen.save('envio.jpg', 'JPEG')  # Guardar la imagen como JPEG

                # Convertir la imagen PIL a una matriz NumPy
                input_imagen_array = np.array(input_imagen)

                input_face_locations = face_recognition.face_locations(input_imagen_array)

                # Continuar con la comparación de rostros
                if stored_face_locations and input_face_locations:
                    stored_rostro = face_recognition.face_encodings(stored_imagen_array, stored_face_locations)[0]
                    input_rostro = face_recognition.face_encodings(input_imagen_array, input_face_locations)[0]

                    # Compara los rostros
                    result = face_recognition.compare_faces([stored_rostro], input_rostro)

                    if result[0]:
                        print('Inicio de sesión exitoso')
                        return jsonify({'mensaje': 'Inicio de sesión exitoso'})
                    else:
                        print('Inicio de sesión fallido: los rostros no son compatibles')

    # Si se llega a este punto, significa que no se encontró el usuario o la contraseña es incorrecta
    return jsonify({'mensaje': 'Inicio de sesión fallido'})
                
if __name__ == '__main__':
    app.run(debug=True)
