import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_restplus import Api, Resource, fields
import requests

from wallet import Wallet
from blockchain import Blockchain
from database.access import get_value, save_user_to_db, add_like, table_counts, get_value, set_value
from database.setup import initialise_db

port = 5000
wallet = Wallet(port)
blockchain = Blockchain(wallet.public_key, port)
app = Flask(__name__)
app.config['ERROR_404_HELP'] = False
CORS(app)
api = Api(
    app,
    version='0.3.0',
    title='Electric Pigeon Coin',
    description='The hottest new meme coin on the block 🚀'
)






# Builtin UI endpoints

@app.route('/frontend', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'network.html')


# Backend

backend_space = api.namespace('backend', description='Setting up the initial configuration/restting an existing session')

@backend_space.route('/initialise_db')
class InitialiseDB(Resource):
    def get(self):
        """Initialises the tables for use by the blockchain"""
        message, status = initialise_db()
        response = jsonify(message)
        response.status_code = status
        return response


@backend_space.route('/reset_blockchain')
class ResetBlockchain(Resource):
    def get(self):
        """Currently Disabled"""
        try:
            # blockchain.clear_data_old
            response = jsonify({"message": "Blockchain reset"})
            response.status_code = 200
            return response
        except:
            response = jsonify({'message': 'Blockchain not reset'})
            response.statud_code = 500
            return response


# Wallets and Keys

wallet_keys = api.namespace('wallet_and_keys', description='Loading wallet and keys')

balance_fields = api.model('Get the balance for an individual wallet', {
    'public_key': fields.String(required=True, description='The public key for the wallet whose balance is being checked', example="30819f300d06092a864886f70d010101050003818d0030818902818100cc848b48e0554b6dd70f37983d9eb6487c1845d13e7b399d5210f04a898539883d0a2760046e5ad2f194210155e8df5d39c2d7295af07e0c843673701211216e098283d10d802ae1a51c88df8481335ec3f841d20b1820da1641aee92a16b40af6dd94aa12456da7f795c3314b71146a85f4676e5e0113aece18916e59281fbd0203010001")
})


@wallet_keys.route('/keys')
class Keys(Resource):
    def get(self):
        """Generates a new public/private key pair for user and saves them to the database"""
        private_key, public_key = wallet.create_keys_for_users()
        id = save_user_to_db(public_key, private_key, 0)
        if id:
            response = {
                'id': id,
                'publicKey': public_key,
                'privateKey': private_key
            }
            response = jsonify(response)
            response.status_code = 200
            return  response
        else:
            response = jsonify({'message': 'Keys not created'})
            response.status_code = 500
            return response


@wallet_keys.route('/balance')
class Balance(Resource):
    @api.expect(balance_fields)
    def post(self):
        body = request.get_json()
        balance = blockchain.get_balance(body['public_key'])
        if balance is None:
            message = {
                'message': 'Loading balanace failed',
                'wallet_set_up': wallet.public_key is not None
            }
            response = jsonify(message)
            response.status_code = 500
            return response
        else:
            message = {
                'message': 'Fetched balance successfully',
                'balance': balance
            }
            response = jsonify(message)
            response.status_code = 200
            return response



@wallet_keys.route('/wallets')
class GetWallets(Resource):
    def get(self):
        """Get a list of wallets and balances"""
        chain_snapshot = blockchain.chain
        dict_chain = [block.__dict__.copy() for block in chain_snapshot]
        for dict_block in dict_chain:
            dict_block['transactions'] = [tx.__dict__ for tx in
                                        dict_block['transactions']]
        accounts = set()
        for block in dict_chain:
            for transaction in block['transactions']:
                accounts.add(transaction['recipient'])
        message = []
        for account in accounts:
            balance = blockchain.get_balance(account)
            message.append({'account': account, 'balance': balance})
        response = jsonify(message)
        response.status_code = 200
        return response


# Node management

node_space = api.namespace('nodes', description="Node wallet management and Mining")
load_wallet_fields = api.model('Load existing keys for the node', {})

@node_space.route('/wallet')
class NodeWallet(Resource):
    def post(self):
        """Generate new keys for the node. `CAUTION!!! Your node may lose it's current balance`"""
        wallet.create_keys()
        if wallet.save_keys():
            global blockchain
            blockchain = Blockchain(wallet.public_key, port)
            message = {
                'public_key': wallet.public_key,
                'private_key': wallet.private_key,
                'funds': blockchain.get_balance()
            }
            response = jsonify(message)
            response.status_code = 201
            return response
        else:
            response = jsonify({'message': 'Saving the keys failed'})
            response.status_code = 500
            return response

    def get(self):
        """Load the keys for the current node"""
        if wallet.load_keys():
            global blockchain
            blockchain = Blockchain(wallet.public_key, port)
            message = {
                'public_key': wallet.public_key,
                'private_key': wallet.private_key,
                'funds': blockchain.get_balance()
            }
            response = jsonify(message)
            response.status_code = 201
            return response
        else:
            response = jsonify({'message': 'Loading the keys failed'})
            response.status_code = 500
            return response


@node_space.route('/balance')
class NodeBalance(Resource):
    def get(self):
        """Returns the balance for the Node"""
        balance = blockchain.get_balance()
        if balance is None:
            message = {
                'message': 'Loading balanace failed',
                'wallet_set_up': wallet.public_key is not None
            }
            response = jsonify(message)
            response.status_code = 500
            return response
        else:
            message = {
                'message': 'Fetched balance successfully',
                'funds': balance
            }
            response = jsonify(message)
            response.status_code = 200
            return response


@node_space.route('/mine')
class Mine(Resource):
    def get(self):
        """Validates all open transactions and adds them to a new block"""
        if wallet.public_key is None:
            try:
                response = requests.get('http://localhost:5000/nodes/wallet')
            except: 
                pass
        if blockchain.resolve_conflicts:
            response = jsonify({'message': 'Resolve conflicts first, block not added'})
            response.status_code = 409
            return response
        block = blockchain.mine_block()
        print(f'BLOCK: {block}')
        if block is not None:
            dict_block = block.__dict__.copy()
            dict_block['transactions'] = [tx.__dict__ for tx in
                                        dict_block['transactions']]
            message = {
                'message': 'Block added successfully',
                'block': dict_block,
                'funds': blockchain.get_balance()
            }
            response = jsonify(message)
            response.status_code = 200
            return response
        else:
            message = {
                'message': 'Adding a block failed',
                'wallet_set_up': wallet.public_key is not None
            }
            response = jsonify(message)
            response.status_code = 500
            return response



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


# Transactions

transaction_space = api.namespace('transactions', description="Make transactions on the blockchain")
transaction_fields = api.model('Make a transaction', {
    'id': fields.Integer(required=True, description="An autogenerated ID made during the key generation", example=201),
    'buyer': fields.String(required=True, description="The public key of the buyer's wallet", example="30819f300d06092a864886f70d010101050003818d0030818902818100a3807aad16a2fbfcd743ec77e121a299823fbcf159cfe56af886cc576f34f386c34b2fd05dd629f7bfd3a725249dc0778dbad45995d580e9f513fdcc0351613caf24ce374e8f9781871fe3d784e9e024f78685015756a23b71e39a070f94493142588526dc6143a29f64e3aa90a519a640bbc5806786b248e434cad23e8a8d0f0203010001"),
    'seller': fields.String(required=True, description="The public key of the seller's wallet", example="30819f300d06092a864886f70d010101050003818d0030818902818100cc848b48e0554b6dd70f37983d9eb6487c1845d13e7b399d5210f04a898539883d0a2760046e5ad2f194210155e8df5d39c2d7295af07e0c843673701211216e098283d10d802ae1a51c88df8481335ec3f841d20b1820da1641aee92a16b40af6dd94aa12456da7f795c3314b71146a85f4676e5e0113aece18916e59281fbd0203010001"),
    'amount': fields.String(required=True, description="The amount of coins the buyer is looking to purchase", example=200)
})


@transaction_space.route('/buy')
class Buy(Resource):
    @api.expect(transaction_fields)
    def post(self):
        body = request.get_json()
        if not body:
            response = jsonify({'message': 'No data found in request body'})
            response.status_code = 400
            return response
        required_fields = ['seller', 'buyer', 'amount', 'id']
        if not all(field in body for field in required_fields):
            response = jsonify({'message': 'Required data is missing from request body'})
            response.status_code = 400
            return response
        recipient = body['buyer']
        amount = body['amount']
        seller = body['seller']
        id = body['id']
        signature = wallet.sign_transaction_as_seller(seller, recipient, amount, id)
        success = blockchain.add_transaction(recipient,
                                            seller,
                                            signature,
                                            amount)
        if success:
            message = {
                'message': 'Successfully added transaction',
                'transaction': {
                    'sender': seller,
                    'recipient': recipient,
                    'amount': amount,
                    'signature': signature
                },
                'cleared_funds': blockchain.get_balance(recipient)
            }
            response = jsonify(message)
            response.status_code = 201
            return response
        else:
            response = jsonify({'message': 'Creating a transaction failed'})
            response.status_code = 500
            return response



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


@app.route('/add_like', methods=['GET'])
def add_like_to_database():
    response, status = add_like()
    return jsonify(response), status

@app.route('/get_counts', methods=['POST'])
def get_counts():
    body = request.get_json()
    response, status = table_counts(body['table'])
    return jsonify(response), status

@app.route('/get_value', methods=['GET'])
def get_coin_value():
    response, status = get_value()
    return jsonify(response), status

@app.route('/set_value', methods=['POST'])
def set_coin_value():
    body = request.get_json()
    response, status = set_value(body['new_value'])
    return jsonify(response), status


@app.route('/sell', methods=['POST'])
def sell_coins():
    body = request.get_json()
    return {'message': 'Working on this'}



if __name__ == '__main__':

    app.run(host='0.0.0.0', port=port)