import bcrypt

class Usuario:
    def __init__(self, username, password, imagen_rostro=None):
        self.username = username
        self.password_hash = self.set_password(password)
        self.imagen_rostro = imagen_rostro

    def set_password(self, password):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return password_hash.decode('utf-8')

    @staticmethod
    def verify_password(stored_password_hash, password):
        return bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8'))
