import os
from dotenv import load_dotenv
from sqlalchemy.sql.sqltypes import NUMERIC
load_dotenv() 

PGUSER=os.environ["PGUSER"]
PGPASSWORD=os.environ["PGPASSWORD"]

from sqlalchemy import Column, String, BigInteger, Integer, create_engine, NUMERIC
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@localhost:5432/blockchain')

class BCWallet(Base):
    __tablename__ = 'wallets'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_key=Column(String, primary_key=True)
    private_key=Column(String)
    port = Column(Integer)

class BCLikes(Base):
    __tablename__ = 'likes'
    id = Column(BigInteger, primary_key=True, autoincrement=True)

class BCElonUp(Base):
    __tablename__ = 'elon_up'
    id = Column(Integer, primary_key=True, autoincrement=True)

class BCElonDown(Base):
    __tablename__ = 'elon_down'
    id = Column(Integer, primary_key=True, autoincrement=True)

class BCValue(Base):
    __tablename__ = 'value'
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(NUMERIC(20, 10))

class BCStatus(Base):
    __tablename__ = "status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer)

class BCStolen(Base):
    __tablename__ = "stolen"
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer)

def initialise_db():
    try:
        Base.metadata.create_all(engine)
        engine.dispose()
        return {"message": "Database initialised"}, 200

    except:
        engine.dispose()
        return {"message": "Failed to initialise database"}, 500