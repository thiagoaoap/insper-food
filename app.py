from flask import Flask, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import getpass
from pymongo.errors import OperationFailure
from datetime import datetime
import pymongo

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


@app.route('/pedidos_em_andamento', methods=['GET'])
def get_pedidos_em_andamento():

    filtro = {}
    projecao = {"_id" : 0}
    dados_pedidos = mongo.db.pedidos_em_andamento.find(filtro, projecao).sort('horario_pedido', -1)

    resp = {
        "pedidos em andamento": list(dados_pedidos)
    }

    return resp, 200


@app.route('/pedidos_em_andamento/<senha>', methods=['GET'])
def get_pedido_em_andamento_especifico(senha):

    dados_pedido = mongo.db.pedidos_em_andamento.find_one(
        {"senha": senha},
        projection={"_id": 0},
        sort=[("data_pedido", -1)]
    )

    if not dados_pedido:
        return {"erro": "Usuário não encontrado"}, 404
    
    resp = dados_pedido

    return resp, 200


@app.route('/pedidos_em_andamento', methods=['POST'])
def post_pedido_em_andamento():
    
    data = request.json

    now = datetime.now()

    data['data_pedido'] = now.strftime("%Y-%m-%d")
    data['horario_pedido'] = now.strftime("%H:%M:%S")

    ultimo_pedido = mongo.db.pedidos_em_andamento.find_one(sort=[("senha", -1)])

    nova_senha = 1

    if ultimo_pedido and "senha" in ultimo_pedido:
        ultima_senha = int(ultimo_pedido["senha"])
        nova_senha = (ultima_senha + 1) if ultima_senha < 999 else 1

    data['senha'] = f"{nova_senha:03}"

    if 'id_itens' not in data or data['id_itens'] == "":
        return {"erro": f"Pedido sem nenhum item"}, 400
    
    result = mongo.db.pedidos_em_andamento.insert_one(data)

    return {"id": str(result.inserted_id)}, 201


@app.route('/pedidos_em_andamento/<senha>', methods=['PUT'])
def put_pedido_em_andamento(senha):

    dados_pedido = mongo.db.pedidos_em_andamento.find_one(
        {"senha": senha},
        sort=[("data_pedido", -1)]
    )

    if not dados_pedido:
        return{"erro": "Usuário não encontrado"}, 404
    
    data = request.json

    if 'id_itens' in data and data['id_itens'] == "":
        return {"erro": f"Pedido sem nenhum item"}, 400
    
    mongo.db.pedidos_em_andamento.update_one({"_id": dados_pedido['_id']}, {"$set": data})

    return {"msg": "Pedido atualizado com sucesso"}, 201


@app.route('/pedidos_em_andamento/<senha>', methods=['DELETE'])
def delete_pedido_em_andamento(senha):
    
    dados_pedido = mongo.db.pedidos_em_andamento.find_one(
        {"senha": senha},
        sort=[("data_pedido", -1)]
    )

    result = mongo.db.pedidos_em_andamento.delete_one({"_id": dados_pedido['_id']})

    if result.deleted_count == 1:
        return {"msg": "Pedido deletado com sucesso"}, 200
    else:
        return {"erro": "Pedido não encontrado"}, 404
    

@app.route('/pedidos_em_andamento/<senha>/completar', methods=['PUT'])
def completar_pedido(senha):

    dados_pedido = mongo.db.pedidos_em_andamento.find_one(
        {"senha": senha},
        sort=[("data_pedido", -1)]
    )

    if not dados_pedido:
        return {"erro": "Pedido não encontrado"}, 404
    
    id_pedido = dados_pedido['_id']
    
    dados_pedido.pop('_id', None)
    dados_pedido.pop('senha', None)

    result = mongo.db.pedidos_completos.insert_one(dados_pedido)

    mongo.db.pedidos_em_andamento.delete_one({"_id": id_pedido})

    return {"msg": "Pedido completado com sucesso", "id": str(result.inserted_id)}, 200



if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)