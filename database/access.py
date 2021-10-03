from json import load
import os
from dotenv import load_dotenv
from requests.sessions import session
load_dotenv() 
# DATABASE = os.getenv('DATABASE')

PGUSER=os.environ["PGUSER"]
PGPASSWORD=os.environ["PGPASSWORD"]

from sqlalchemy import MetaData, create_engine, exc, insert, select, update
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.session import sessionmaker

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
    # engine = create_engine(f'{DATABASE}')
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        wallets = metadata.tables['wallets']
        stmt = (select (wallets).where(wallets.c.port == port))
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        return result
    except:
        engine.dispose()
        return False

def add_like():
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        like_table = metadata.tables['likes']
        stmt = (insert(like_table).values())
        engine.execute(stmt)
        engine.dispose()
        return {"message": "like added, thank you"}, 200
    except:
        engine.dispose()
        return {"message": "Like failed to add, please try again later"}, 500

def add_elon(elon_table):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        table = metadata.tables[elon_table]
        stmt = (insert(table).values())
        engine.execute(stmt)
        engine.dispose()
        return {"message": "Elon said something, I hope it's ok"}, 200
    except:
        engine.dispose()
        return {"message": "Looks like Elon's Twitter is broken, please try again later"}, 500

def table_counts(table):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        table_to_count = metadata.tables[table]
        rows = session.query(table_to_count).count()
        engine.dispose()
        return {"message": rows}, 200
    except:
        engine.dispose()
        return {"message": "User count unavailable"}, 500

def get_value():
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        value_table = metadata.tables['value']
        stmt = (select(value_table).where(value_table.c.id == 1))
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        value = float(result[1])
        return {"message": value}, 200
    except:
        engine.dispose()
        return {"message": "Unable to acertain value"}, 500

def set_value(new_value):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        value = metadata.tables['value']
        stmt = (update(value).where(value.c.id == 1).values(value = new_value))
        engine.execute(stmt)
        engine.dispose()
        return {"message": "Value successfully updated"}, 200
    except:
        engine.dispose()
        return {"message": "Failed to update the value"}, 500

def get_status():
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        status_table = metadata.tables['status']
        stmt = (select(status_table).where(status_table.c.id == 1))
        result = engine.execute(stmt).fetchone()
        engine.dispose()
        status = result[1]
        return {'status': status}, 200
    except:
        engine.dispose()
        return {'message': 'Failed to fetch the status'}, 500

def set_status(new_status):
    engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
    metadata = MetaData(bind=engine)
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    try:
        status_table = metadata.tables['status']
        stmt = (update(status_table).where(status_table.c.id == 1).values(status = new_status))
        engine.execute(stmt)
        engine.dispose()
        if new_status == 1:
            status = 'ready'
        else:
            status = 'offline'
        return {'message': f'exchange is {status}'}, 200
    except:
        engine.dispose()
        return {'message': "Failed to update the value"}, 500