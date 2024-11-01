from flask import request, Response
from functools import wraps
import hashlib

mongo = None 

def init_mongo(mongo_instance):
    global mongo
    mongo = mongo_instance

def hash_password(password):
    """Gera um hash SHA-256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth(username, password):
    """Verifica se as credenciais de usuário e senha são válidas."""
    # Use a senha em texto simples temporariamente para depuração
    print(f"Verificando usuário: {username} com senha: {password}")  # Debugging
    filtro_ = {"usuario": username, "senha": password}  # Usar senha em texto simples
    usuario = mongo.db.usuarios.find_one(filtro_)
    return bool(usuario)

def authenticate():
    """Envia uma resposta que solicita autenticação ao usuário.""" 
    return Response(
        'Acesso negado. Por favor, autentique-se.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    """Decorador que protege rotas específicas com autenticação básica.""" 
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
