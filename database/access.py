import os
from dotenv import load_dotenv
load_dotenv() 
PGUSER=os.getenv("PGUSER")
PGPASSWORD=os.getenv("PGPASSWORD")

from sqlalchemy import MetaData, create_engine, insert, select
from sqlalchemy.ext.automap import automap_base

def save_user_to_db(public_key, private_key):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()

    wallets = metadata.tables['wallets']
    try:
        stmt = (
            insert(wallets).
            values(public_key=public_key, private_key=private_key) 
        )
        result = engine.execute(stmt)
        engine.dispose()
        return result.inserted_primary_key[0]
    except:
        engine.dispose()
        return False

def load_user_from_db(id):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        wallets = metadata.tables['wallets']

        stmt = (select (wallets).where(wallets.c.id == id))
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        return result
    except:
        engine.dispose()
        return False


def load_user_from_db(id):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        wallets = metadata.tables['wallets']

        stmt = (select (wallets).where(wallets.c.id == id))
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        return result
    except:
        engine.dispose()
        return False