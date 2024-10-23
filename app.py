from flask import Flask, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import getpass
from pymongo.errors import OperationFailure

user = input('User: ')
password = getpass.getpass('Password: ')

app = Flask(__name__)

try:
    app.config["MONGO_URI"] = f"mongodb+srv://{user}:{password}@cluster0.rvm0f.mongodb.net/insper_food"
    mongo = PyMongo(app)
    mongo.cx.server_info()
    print("Conectado ao MongoDB com sucesso!")
except OperationFailure as x:
    print("Erro de autenticação: usuário ou senha incorretos.")
    exit()
except Exception as x:
    print(f"Erro ao conectar ao MongoDB: {x}")
    exit()


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)