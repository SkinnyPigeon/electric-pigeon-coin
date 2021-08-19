import os
from dotenv import load_dotenv
load_dotenv() 
# PGUSER=os.getenv("PGUSER")
# PGPASSWORD=os.getenv("PGPASSWORD")
# DATABASE_URL = os.getenv('DATABASE_URL')
# DATABASE=os.getenv('DATABASE')

PGUSER=os.environ["PGUSER"]
PGPASSWORD=os.environ["PGPASSWORD"]
# DATABASE=os.environ["DATABASE"]
# DATABASE_URL=os.environ["DATABASE_URL"]

from sqlalchemy import Column, String, BigInteger, Integer, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')
# engine = create_engine(f'{DATABASE}')

class BCWallet(Base):
    __tablename__ = 'wallets'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_key=Column(String, primary_key=True)
    private_key=Column(String)
    port = Column(Integer)

class BCLikes(Base):
    __tablename__ = 'likes'
    id = Column(BigInteger, primary_key=True, autoincrement=True)


Base.metadata.create_all(engine)
engine.dispose()

def initialise_db():
    return {'message': 'Database initialised'}, 200
