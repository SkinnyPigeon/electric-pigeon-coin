from json import load
import os
from dotenv import load_dotenv
load_dotenv() 
PGUSER=os.getenv("PGUSER")
PGPASSWORD=os.getenv("PGPASSWORD")
# DATABASE = os.getenv('DATABASE')

# PGUSER=os.environ["PGUSER"]
# PGPASSWORD=os.environ["PGPASSWORD"]
# DATABASE=os.environ["DATABASE"]

from sqlalchemy import MetaData, create_engine, insert, select
from sqlalchemy.ext.automap import automap_base

def save_user_to_db(public_key, private_key, port):
    # engine = create_engine(f'{DATABASE}')
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()

    wallets = metadata.tables['wallets']
    try:
        stmt = (
            insert(wallets).
            values(public_key=public_key, private_key=private_key, port=port) 
        )
        result = engine.execute(stmt)
        engine.dispose()

        return result.inserted_primary_key[0]
    except:
        engine.dispose()
        return False

def load_user_from_db(public_key):
    # engine = create_engine(f'{DATABASE}')
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        wallets = metadata.tables['wallets']

        stmt = (select (wallets).where(wallets.c.public_key == public_key))
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        return result
    except:
        engine.dispose()
        return False


def load_node_from_db(port):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    # engine = create_engine(f'{DATABASE}')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        wallets = metadata.tables['wallets']
        # print(wallets)
        stmt = (select (wallets).where(wallets.c.port == port))
        # print(stmt)
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        return result
    except:
        engine.dispose()
        return False