import os
from dotenv import load_dotenv
load_dotenv() 
PGUSER=os.getenv("PGUSER")
PGPASSWORD=os.getenv("PGPASSWORD")
DATABASE_URL = os.getenv['DATABASE_URL']


from sqlalchemy import Column, String, BigInteger, Integer, create_engine
from sqlalchemy.orm import declarative_base
Base = declarative_base()

engine = create_engine(f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{DATABASE_URL}')

class BCWallet(Base):
    __tablename__ = 'wallets'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_key=Column(String, primary_key=True)
    private_key=Column(String)
    port = Column(Integer)


def initialise_db():
    try:
        Base.metadata.create_all(engine)
        engine.dispose()
        return {'message': 'Database initialised'}, 200
    except:
        engine.dispose()
        return {'message': 'Database initialisation failed'}, 500