import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.wrappers import response

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'network.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Saving the keys failed'
        }
        return jsonify(response), 500


@app.route('/keys', methods=['GET'])
def create_browser_keys():
    wallet.create_keys()
    response = {
        'publicKey': wallet.public_key,
        'privateKey': wallet.private_key
    }
    return jsonify(response), 200


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Loading the keys failed'
        }
        return jsonify(response), 500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance is None:
        response = {
            'message': 'Loading balanace failed',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(response), 500
    else:
        response = {
            'message': 'Fetched balance successfully',
            'funds': balance
        }
        return jsonify(response), 200


@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    body = request.get_json()
    if not body:
        response = {'message': 'No data found'}
        return jsonify(response), 400
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(key in body for key in required):
        response = {'message': 'Some data is missing'}
        return jsonify(response), 400

    success = blockchain.add_transaction(body['recipient'],
                                         body['sender'],
                                         body['signature'],
                                         body['amount'],
                                         is_receiving=True)
    print(success)
    print(body)
    if success:
        response = {
            'message': 'Successfully added transaction',
            'transaction': {
                'sender': body['sender'],
                'recipient': body['recipient'],
                'amount': body['amount'],
                'signature': body['signature']
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed'
        }
        return jsonify(response), 500


@app.route('/broadcast-block', methods=['POST'])
def broadcast_block():
    body = request.get_json()
    if not body:
        response = {'message': 'No data found'}
        return jsonify(response), 400
    if 'block' not in body:
        response = {'message': 'Some data is missing'}
        return jsonify(response), 400
    block = body['block']
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {'message': 'Block added'}
            return jsonify(response), 201
        else:
            response = {'message': 'Block seems invalid'}
            return jsonify(response), 409
    elif block['index'] > blockchain.chain[-1].index:
        response = {
            'message': 'Blockchain seems to differ from local blockchain'
            }
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {
            'message': 'Blockchain seems to be shorted, block not added'
            }
        return jsonify(response), 409


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key is None:
        response = {
            'message': 'No wallet set up'
        }
        return jsonify(response), 400
    body = request.get_json()
    if not body:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required_fields = ['recipient', 'amount']
    if not all(field in body for field in required_fields):
        response = {
            'message': 'Required data is missing'
        }
        return jsonify(response), 400
    recipient = body['recipient']
    amount = body['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient,
                                         wallet.public_key,
                                         signature,
                                         amount)
    if success:
        response = {
            'message': 'Successfully added transaction',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed'
        }
        return jsonify(response), 500

@app.route('/buy', methods=['POST'])
def buy_currency():
    body = request.get_json()
    if not body:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required_fields = ['seller', 'buyer', 'amount']
    if not all(field in body for field in required_fields):
        response = {
            'message': 'Required data is missing'
        }
        return jsonify(response), 400
    recipient = body['buyer']
    amount = body['amount']
    seller = body['seller']
    signature = wallet.sign_transaction_as_seller(wallet.public_key, recipient, amount)
    print(f'Signature: {signature}')
    success = blockchain.add_transaction(recipient,
                                         wallet.public_key,
                                         signature,
                                         amount)
    if success:
        response = {
            'message': 'Successfully added transaction',
            'transaction': {
                'sender': seller,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed'
        }
        return jsonify(response), 500


@app.route('/mine', methods=['POST'])
def mine():
    if blockchain.resolve_conflicts:
        response = {'message': 'Resolve conflicts first, block not added'}
        return jsonify(response), 409
    block = blockchain.mine_block()
    if block is not None:
        dict_block = block.__dict__.copy()
        dict_block['transactions'] = [tx.__dict__ for tx in
                                      dict_block['transactions']]
        response = {
            'message': 'Block added successfully',
            'block': dict_block,
            'funds': blockchain.get_balance()
        }
        return response, 200
    else:
        response = {
            'message': 'Adding a block failed',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(response), 500


@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain was replaced'}
    else:
        response = {'message': 'Local chain kept'}
    return jsonify(response), 200


@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in
                                      dict_block['transactions']]
    return jsonify(dict_chain), 200


@app.route('/wallets', methods=['GET'])
def get_wallets():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in
                                      dict_block['transactions']]
    accounts = set()
    for block in dict_chain:
        for transaction in block['transactions']:
            accounts.add(transaction['recipient'])
    response = []
    for account in accounts:
        balance = blockchain.get_balance(account)
        response.append({'account': account, 'balance': balance})
    return jsonify(response), 200


@app.route('/node', methods=['POST'])
def add_node():
    body = request.get_json()
    if not body:
        response = {
            'message': 'No data attached'
        }
        return jsonify(response), 400
    if 'node' not in body:
        response = {
            'message': 'No node data found'
        }
        return jsonify(response), 400
    node = body['node']
    blockchain.add_peer_node(node)
    response = {
        'message': 'Node added succesfully',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url is None:
        response = {
            'message': 'No node found'
        }
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {
        'message': 'Node removed',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200


@app.route('/sell', methods=['POST'])
def sell_coins():
    body = request.get_json()
    return {'message': 'Working on this'}


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port=port)
