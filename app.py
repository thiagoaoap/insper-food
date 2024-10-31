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


########################################################################################## PEDIDOS EM ANDAMENTO


@app.route('/pedidos', methods=['GET'])
def get_pedidos_em_andamento():

    filtro = {}
    projecao = {"_id" : 0}
    dados_pedidos = mongo.db.pedidos_em_andamento.find(filtro, projecao).sort('horario_pedido', -1)

    resp = {
        "pedidos_em_andamento": list(dados_pedidos)
    }

    return resp, 200


@app.route('/pedidos/<senha>', methods=['GET'])
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


@app.route('/pedidos', methods=['POST'])
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

    if 'codigos_itens' not in data or data['codigos_itens'] == "":
        return {"erro": f"Pedido sem nenhum item"}, 400

    preco_total = 0

    for codigo in data['codigos_itens']:
        item = mongo.db.itens_cardapio.find_one({"codigo": codigo})
        preco_total += item['preco']
    
    data['preco_total'] = preco_total

    result = mongo.db.pedidos_em_andamento.insert_one(data)

    return {"id": str(result.inserted_id)}, 201


@app.route('/pedidos/<senha>', methods=['PUT'])
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


@app.route('/pedidos/<senha>', methods=['DELETE'])
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
    

@app.route('/pedidos/<senha>/completar', methods=['PUT'])
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


########################################################################################## PEDIDOS COMPLETOS


@app.route('/pedidos_completos', methods=['GET'])
def get_pedidos_completos():

    filtro = {}
    dados_pedidos = mongo.db.pedidos_completos.find(filtro)

    pedidos = []

    for pedido in dados_pedidos:
        pedido["_id"] = str(pedido["_id"])
        pedidos.append(pedido)

    resp = {
        "pedidos_completos": pedidos
    }

    return resp, 200


@app.route('/pedidos_completos/<id>', methods=['GET'])
def get_pedido_completo_especifico(id):

    if not ObjectId.is_valid(id):
        return {"erro": "ID digitado incorretamente"}, 400

    filtro = {"_id": ObjectId(id)}
    projecao = {"_id": 0}
    dados_pedido = mongo.db.pedidos_completos.find_one(filtro, projecao)

    if not dados_pedido:
        return {"erro": "Pedido não encontrado"}, 404
    
    resp = dados_pedido

    return resp, 200


@app.route('/pedidos_completos/<id>', methods=['DELETE'])
def delete_pedido_completo(id):

    if not ObjectId.is_valid(id):
        return {"erro": "ID digitado incorretamente"}, 400
    
    filtro = {"_id": ObjectId(id)}
    result = mongo.db.pedidos_completos.delete_one(filtro)

    if result.deleted_count == 1:
        return {"msg": "Pedido deletado com sucesso"}, 200
    else:
        return {"erro": "Pedido não encontrado"}, 404


########################################################################################## ITENS CARDAPIO


@app.route('/cardapio', methods=['GET'])
def get_itens_cardapio():

    filtro = {}
    projecao = {"_id": 0}
    dados_cardapio = mongo.db.itens_cardapio.find(filtro, projecao)

    resp = {
        "itens_cardapio": list(dados_cardapio)
    }

    return resp, 200


@app.route('/cardapio/<int:codigo>', methods=['GET'])
def get_item_cardapio_especifico(codigo):

    filtro = {"codigo": codigo}
    projecao = {"_id": 0}
    dados_item = mongo.db.itens_cardapio.find_one(filtro, projecao)

    if not dados_item:
        return {"erro": "Item não encontrado"}, 404
    
    resp = dados_item

    return resp, 200


@app.route('/cardapio', methods=['POST'])
def post_item_cardapio():
    
    data = request.json

    keys = ["nome", "preco", "codigo"]

    for key in keys:
        if key not in data or data[key] == "":
            return {"erro": f"Está faltando {key}"}, 400
        
    filtro = {"codigo": data['codigo']}

    if mongo.db.itens_cardapio.find_one(filtro):
        return {"erro": "Código já cadastrado"}
    
    result = mongo.db.itens_cardapio.insert_one(data)

    return {"id": str(result.inserted_id)}, 201


@app.route('/cardapio/<int:codigo>', methods=['PUT'])
def put_item_cardapio(codigo):

    filtro = {"codigo": codigo}
    projecao = {"_id": 0}
    dados_item = mongo.db.itens_cardapio.find_one(filtro, projecao)

    if not dados_item:
        return{"erro": "Item não encontrado"}, 404
    
    data = request.json

    keys = ["nome", "preco", "codigo"]

    for key in keys:
        if key in data and data[key] == "":
            return {"erro": f"{key} está vazio"}, 400
    
    mongo.db.itens_cardapio.update_one({"codigo": codigo}, {"$set": data})

    return {"msg": "Item atualizado com sucesso"}, 201


@app.route('/cardapio/<int:codigo>', methods=['DELETE'])
def delete_item_cardapio(codigo):

    filtro = {"codigo": codigo}
    result = mongo.db.itens_cardapio.delete_one(filtro)

    if result.deleted_count == 1:
        return {"msg": "Item deletado com sucesso"}, 200
    else:
        return {"erro": "Item não encontrado"}, 404


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)