from os import remove
from flask import Flask, json, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_restplus import Api, Resource, fields
import requests

from wallet import Wallet
from blockchain import Blockchain
from database.access import get_value, save_user_to_db, add_like, table_counts, get_value, set_value, get_status, set_status
from database.setup import initialise_db

# port = 5000
# wallet = Wallet(port)
# blockchain = Blockchain(wallet.public_key, port, 'blockchain-5000.txt')
app = Flask(__name__)
app.config['ERROR_404_HELP'] = False
CORS(app)
api = Api(
    app,
    version='0.3.0',
    title='Electric Pigeon Coin',
    description="""The hottest new meme coin on the block 🚀
    To begin, you must first either create a set of keys for this node via the POST request at /nodes/new-wallet or load existing keys for the node from the GET request at /nodes/load-wallet
    """
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
        """Get the balance of a wallet from the public key"""
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
wallet_fields = api.model('The port and filename for saving and loading the blockchain with', {
    'port': fields.Integer(required=True, description='The port the blockchain will run on', example=5000),
    'filename': fields.String(required=True, description='The filename underwhich the blockchain will be phsyically stored in the S3 bucket', example='blockchain-5000.txt')
})

@node_space.route('/new-wallet')
class NewNodeWallet(Resource):
    @api.expect(wallet_fields)
    def post(self):
        """Generate new keys for the node. `CAUTION!!! If you aleady have a node you may lose it's balance`"""
        body = request.get_json()
        port = body['port']
        filename = body['filename']
        wallet.create_keys()
        if wallet.save_keys():
            global blockchain
            blockchain = Blockchain(wallet.public_key, port, filename)
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

@node_space.route('/load-wallet')
class LoadNodeWallet(Resource):
    @api.expect(wallet_fields)
    def post(self):
        """Load the keys for the current node"""
        if wallet.load_keys():
            body = request.get_json()
            port = body['port']
            filename = body['filename']
            global blockchain
            blockchain = Blockchain(wallet.public_key, port, filename)
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
                response = requests.get('http://localhost:5000/nodes/load-wallet')
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

@node_space.route('/resolve-conflicts')
class ResolveConflicts(Resource):
    def post(self):
        """Resolve conflicts on the blockchain"""
        replaced = blockchain.resolve()
        if replaced:
            response = jsonify({'message': 'Chain was replaced'})
        else:
            response = jsonify({'message': 'Local chain kept'})
        response.status_code = 200
        return response

add_node_fields = api.model('Add a new peer node to transmit to and receive from', {
    'node': fields.String(required=True, description='The new peer node to add to the network', example='localhost:5002')
})

@node_space.route('/node')
class AddNodePeer(Resource):
    @api.expect(add_node_fields)
    def post(self):
        """Add new peer node to transmit to and receive from"""
        body = request.get_json()
        if not body:
            response = jsonify({'message': 'No data attached'})
            response.statud_code = 400
            return response
        if 'node' not in body:
            response = jsonify({'message': 'No node data found'})
            response.status_code = 400
            return response
        node = body['node']
        blockchain.add_peer_node(node)
        message = {
            'message': 'Node added succesfully',
            'all_nodes': blockchain.get_peer_nodes()
        }
        response = jsonify(message)
        response.status_code = 201
        return response


remove_node_fields = api.model('Remove an existing peer node from the network', {
    'node': fields.String(required=True, description='The new peer node to remove from the network', example='localhost:5002')
})

@node_space.route('/node/<node_url>')
class DeletePeerNode(Resource):
    @api.expect(remove_node_fields)
    def delete(self, node_url):
        """Remove peer node"""
        if node_url == '' or node_url is None:
            response = jsonify({'message': 'No node found'})
            response.status_code = 400
            return response
        blockchain.remove_peer_node(node_url)
        message = {
            'message': 'Node removed',
            'all_nodes': blockchain.get_peer_nodes()
        }
        response = jsonify(message)
        response.status_code = 200
        return response


@node_space.route('/nodes')
class AllPeerNodes(Resource):
    def get(self):
        """Get list of all available peer nodes"""
        nodes = blockchain.get_peer_nodes()
        response = jsonify({'all_nodes': nodes})
        response.status_code = 200
        return response


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
        """Allows user to buy coins from available wallets"""
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


node_to_recipient_fields = api.model('Allows the node to tranfer funds to another wallet', {
    'recipient': fields.String(required=True, description='The public key of the wallet to send funds to', example="30819f300d06092a864886f70d010101050003818d0030818902818100a3807aad16a2fbfcd743ec77e121a299823fbcf159cfe56af886cc576f34f386c34b2fd05dd629f7bfd3a725249dc0778dbad45995d580e9f513fdcc0351613caf24ce374e8f9781871fe3d784e9e024f78685015756a23b71e39a070f94493142588526dc6143a29f64e3aa90a519a640bbc5806786b248e434cad23e8a8d0f0203010001"),
    'amount': fields.Float(required=True, description='The amount of coins to transfer, can be float type', example=201.7263)
})

@transaction_space.route('/node-transfer')
class AddTransaction(Resource):
    @api.expect(node_to_recipient_fields)
    def post(self):
        """Allow's the node to transfer funds to another wallet"""
        if wallet.public_key is None:
            response = jsonify({'message': 'No wallet set up'})
            response.status_code = 400
            return response
        body = request.get_json()
        if not body:
            response = jsonify({'message': 'No data found in request body'})
            response.status_code = 400
            return response
        required_fields = ['recipient', 'amount']
        if not all(field in body for field in required_fields):
            response = jsonify({'message': 'Required data is missing from request'})
            response.status_code = 400
            return response
        recipient = body['recipient']
        amount = body['amount']
        signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
        success = blockchain.add_transaction(recipient,
                                            wallet.public_key,
                                            signature,
                                            amount)
        if success:
            message = {
                'message': 'Successfully added transaction',
                'transaction': {
                    'sender': wallet.public_key,
                    'recipient': recipient,
                    'amount': amount,
                    'signature': signature
                },
                'funds': blockchain.get_balance()
            }
            response = jsonify(message)
            response.status_code = 201
            return response
        else:
            response = jsonify({'message': 'Creating a transaction failed'})
            response.status_code = 500
            return response

@transaction_space.route('/open-transactions')
class OpenTransactions(Resource):
    def get(self):
        """Get list of open transactions on network"""
        transactions = blockchain.get_open_transactions()
        dict_transactions = [tx.__dict__ for tx in transactions]
        response = jsonify(dict_transactions)
        response.status_code = 200
        return response


@app.route('/sell', methods=['POST'])
def sell_coins():
    body = request.get_json()
    return {'message': 'Working on this'}


# Broadcast transactions and blocks

broadcast_space = api.namespace('broadcast', description="Broadcast transactions and blocks")

add_transaction_fields = api.model('Broadcast an open transaction to other peer nodes', {
    'id': fields.Integer(required=True, description="An autogenerated ID made during the key generation", example=201),
    'buyer': fields.String(required=True, description="The public key of the buyer's wallet", example="30819f300d06092a864886f70d010101050003818d0030818902818100a3807aad16a2fbfcd743ec77e121a299823fbcf159cfe56af886cc576f34f386c34b2fd05dd629f7bfd3a725249dc0778dbad45995d580e9f513fdcc0351613caf24ce374e8f9781871fe3d784e9e024f78685015756a23b71e39a070f94493142588526dc6143a29f64e3aa90a519a640bbc5806786b248e434cad23e8a8d0f0203010001"),
    'seller': fields.String(required=True, description="The public key of the seller's wallet", example="30819f300d06092a864886f70d010101050003818d0030818902818100cc848b48e0554b6dd70f37983d9eb6487c1845d13e7b399d5210f04a898539883d0a2760046e5ad2f194210155e8df5d39c2d7295af07e0c843673701211216e098283d10d802ae1a51c88df8481335ec3f841d20b1820da1641aee92a16b40af6dd94aa12456da7f795c3314b71146a85f4676e5e0113aece18916e59281fbd0203010001"),
    'amount': fields.String(required=True, description="The amount of coins the buyer is looking to purchase", example=200)
})

add_block_fields = api.model('Broadcast a newly mined block to the other peer nodes', {
    'block': fields.String(required=True, description='A JSON representation of the newly mined block', example={'index': 39, 'previous_hash': '0610c336d851c78ad75961048ace72e7d3a10d09b25a0be717b67a250d845f54', 'timestamp': 1629465233.6212978, 'transactions': [{'sender': '30819f300d06092a864886f70d010101050003818d0030818902818100cc848b48e0554b6dd70f37983d9eb6487c1845d13e7b399d5210f04a898539883d0a2760046e5ad2f194210155e8df5d39c2d7295af07e0c843673701211216e098283d10d802ae1a51c88df8481335ec3f841d20b1820da1641aee92a16b40af6dd94aa12456da7f795c3314b71146a85f4676e5e0113aece18916e59281fbd0203010001', 'recipient': '30819f300d06092a864886f70d010101050003818d0030818902818100a3807aad16a2fbfcd743ec77e121a299823fbcf159cfe56af886cc576f34f386c34b2fd05dd629f7bfd3a725249dc0778dbad45995d580e9f513fdcc0351613caf24ce374e8f9781871fe3d784e9e024f78685015756a23b71e39a070f94493142588526dc6143a29f64e3aa90a519a640bbc5806786b248e434cad23e8a8d0f0203010001', 'amount': 200, 'signature': '555cdfb8b607d7c0056feda5433ca0d831aa0ce976428f87d54f4e58561f519e15d7da7eb28cd07983aefc4c036c8070fcfd3ddf047420c3c200e276ddb5695d8d89736d01377e953aae01fc8fbca61158e5308e9a0189ac4a26a8fe40fe2c9bfc5b559335c08a58705426bd95e71f4f9bd7e5bf94a74e0e39b5b276b7d73a89'}, {'sender': '30819f300d06092a864886f70d010101050003818d0030818902818100cc848b48e0554b6dd70f37983d9eb6487c1845d13e7b399d5210f04a898539883d0a2760046e5ad2f194210155e8df5d39c2d7295af07e0c843673701211216e098283d10d802ae1a51c88df8481335ec3f841d20b1820da1641aee92a16b40af6dd94aa12456da7f795c3314b71146a85f4676e5e0113aece18916e59281fbd0203010001', 'recipient': '30819f300d06092a864886f70d010101050003818d0030818902818100a3807aad16a2fbfcd743ec77e121a299823fbcf159cfe56af886cc576f34f386c34b2fd05dd629f7bfd3a725249dc0778dbad45995d580e9f513fdcc0351613caf24ce374e8f9781871fe3d784e9e024f78685015756a23b71e39a070f94493142588526dc6143a29f64e3aa90a519a640bbc5806786b248e434cad23e8a8d0f0203010001', 'amount': 350, 'signature': '3819e9f2057110357d91ea122d10554199fef5cb8e595d9502762e03d0ee266c69c00a5d7d500ddd4606644b985ca2c4cfd55d1641a82a2f9973ea16cbe7b0b5f893eb33aa31fa9cabfe63cb4b56e8576d6bc7b264e9ea812786243b8ca6d93416c3473f4b59836af56b693b2e2b58f2db0dd23a366bd7ac4ee55a3182f36c32'}, {'sender': 'MINING', 'recipient': '30819f300d06092a864886f70d010101050003818d0030818902818100cc848b48e0554b6dd70f37983d9eb6487c1845d13e7b399d5210f04a898539883d0a2760046e5ad2f194210155e8df5d39c2d7295af07e0c843673701211216e098283d10d802ae1a51c88df8481335ec3f841d20b1820da1641aee92a16b40af6dd94aa12456da7f795c3314b71146a85f4676e5e0113aece18916e59281fbd0203010001', 'amount': 100000, 'signature': ''}], 'proof': 449})
})

@broadcast_space.route('/transaction')
class BroadcastTransaction(Resource):
    @api.expect(add_transaction_fields)
    def post(self):
        """Sends open transactions to peer nodes on the network"""
        body = request.get_json()
        if not body:
            response = jsonify({'message': 'No data found'})
            response.status_code = 400
            return response
        required = ['sender', 'recipient', 'amount', 'signature']
        if not all(key in body for key in required):
            response = jsonify({'message': 'Some data is missing'})
            response.status_code = 400
            return response

        success = blockchain.add_transaction(body['recipient'],
                                            body['sender'],
                                            body['signature'],
                                            body['amount'],
                                            is_receiving=True)
        if success:
            message = {
                'message': 'Successfully added transaction',
                'transaction': {
                    'sender': body['sender'],
                    'recipient': body['recipient'],
                    'amount': body['amount'],
                    'signature': body['signature']
                },
                'funds': blockchain.get_balance()
            }
            response = jsonify(message)
            response.status_code = 201
            return response
        else:
            response = jsonify({'message': 'Creating a transaction failed'})
            response.status_code = 500
            return response


@broadcast_space.route('/block')
class BroadcastBlock(Resource):
    @api.expect(add_block_fields)
    def post(self):
        """Sends newly mined block to peer nodes on the network"""
        body = request.get_json()
        if not body:
            response = jsonify({'message': 'No data found'})
            response.status_code = 400
            return response
        if 'block' not in body:
            response = jsonify({'message': 'Some data is missing'})
            response.status_code = 400
            return response
        block = body['block']
        if block['index'] == blockchain.chain[-1].index + 1:
            if blockchain.add_block(block):
                response = jsonify({'message': 'Block added'})
                response.status_code = 201
                return response
            else:
                response = jsonify({'message': 'Block seems invalid'})
                response.status_code = 409
                return response
        elif block['index'] > blockchain.chain[-1].index:
            response = jsonify({'message': 'Blockchain seems to differ from local blockchain'})
            response.status_code = 200
            blockchain.resolve_conflicts = True
            return response
        else:
            response = jsonify({'message': 'Blockchain seems to be shorted, block not added'})
            response.status_code = 409
            return response


# Blockchain

blockchain_space = api.namespace('blockchain', description="View the current state of the blockchain")

@blockchain_space.route('/chain')
class GetBlockchain(Resource):
    def get(self):
        """Get snapshot of current blockchain"""
        chain_snapshot = blockchain.chain
        dict_chain = [block.__dict__.copy() for block in chain_snapshot]
        for dict_block in dict_chain:
            dict_block['transactions'] = [tx.__dict__ for tx in
                                        dict_block['transactions']]
        response = jsonify(dict_chain)
        response.status_code = 200
        return response


# Stats

stats_space = api.namespace('stats', description="Handles the interactions with the blockchain")

count_fields = api.model('Get counts of the likes and number of users', {
    'table': fields.String(required=True, description='The table to get the counts from', example="likes")
})
value_fields = api.model('Set the current value of the coin', {
    'new_value': fields.Float(required=True, description='The amount to set the value of the coin to', example=5.412)
})

@stats_space.route('/add_like')
class AddLike(Resource):
    def get(self):
        """Add like to the blockchain stats. Might help the value 🤑"""
        message, status = add_like()
        response = jsonify(message)
        response.status_code = status
        return response

@stats_space.route('/get_counts')
class GetCounts(Resource):
    @api.expect(count_fields)
    def post(self):
        """Get counts of the likes and number of users"""
        body = request.get_json()
        message, status = table_counts(body['table'])
        response = jsonify(message)
        response.status_code = status
        return response

@stats_space.route('/get_value')
class GetValue(Resource):
    def get(self):
        """Get current value of the coin"""
        message, status = get_value()
        response = jsonify(message)
        response.status_code = status
        return response

@stats_space.route('/set_value')
class SetValue(Resource):
    @api.expect(value_fields)
    def post(self):
        """Set the current value of the coin 💰. Could be used for currency manipulation I suppose..."""
        body = request.get_json()
        message, status = set_value(body['new_value'])
        response = jsonify(message)
        response.status_code = status
        return response

@stats_space.route('/status')
class GetStatus(Resource):
    def get(self):
        """Get the current status of the exchange"""
        message, status_code = get_status()
        response = jsonify(message)
        response.staus_code = status_code
        return response

status_fields = api.model('Set the current status of the exchange', {
    'status': fields.Integer(required=True, description='The binary on or off for the exchange', enum=[0, 1], example=1)
})

@stats_space.route('/set_status')
class SetStatus(Resource):
    @api.expect(status_fields)
    def post(self):
        """Set the status of the exchange (online or offline)"""
        body = request.get_json()
        message, status_code = set_status(body['status'])
        response = jsonify(message)
        response.status_code = status_code
        return response

# Elon

elon_space = api.namespace('elon', description="Warning! With great power comes great responsibility")

elon_count_fields = api.model('Get counts of the likes and dislikes by a certain individual', {
    'table': fields.String(required=True, description='The table to get the counts from', example="elon_up")
})

if __name__ == '__main__':
    global wallet
    wallet = Wallet(5000)
    app.run(host='0.0.0.0', port=5000)