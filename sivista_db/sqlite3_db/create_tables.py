from sqlalchemy.ext.declarative import declarative_base
from db_manager import SqlDbManager

Base = declarative_base()

def create_tables():
    sql_manager = SqlDbManager()
    engine = sql_manager.engine
    #NOTE : IF MODEL changes - cannot migrate by just changing the model..
    Base.metadata.create_all(engine)
    sql_manager.close()

if __name__ == "__main__":
    create_tables()