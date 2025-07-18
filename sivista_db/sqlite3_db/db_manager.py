
import builtins
from sqlalchemy import create_engine,inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sivista_db.models.data_model import *
from sqlalchemy.dialects.sqlite import insert
import os
import sqlite3
from configparser import ConfigParser
import logging

println = builtins.print

class SqlDbManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):  
            return     
        db_path = "/home/ubuntu/Siclarity_dev.db" 
        sqlite_path = f"sqlite:///{db_path}" 
        if not os.path.exists(db_path):
            self.create_database(db_path)
        self.engine = create_engine(sqlite_path)
        self.Session = sessionmaker(bind=self.engine)
        self.current_session = None       
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        if table_names:
            print(f"{table_names} table names already exist")    
        self.create_tables()
      
    def start_session(self):
        if self.current_session is None:
            self.current_session = self.Session()
        return self.current_session
   
    def create_database(self,db_path):
        db_dir = os.path.dirname(db_path)
         # If the directory doesn't exist, create it      
        if not os.path.exists(db_dir):      
            os.makedirs(db_dir)
        try:
        # Connect to the SQLite database (this will create the file if it doesn't exist)
            conn = sqlite3.connect(db_path)
            conn.close()
            print("SQLite database file created successfully at:", db_path)
        except sqlite3.Error as e:
            print("Error creating SQLite database:", e)

    def create_tables(self):
        #NOTE : IF MODEL changes - cannot migrate by just changing the model..      
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()
    
    def close(self):
        self.engine.dispose()
    
if __name__ == "__main__":
    db_manager = SqlDbManager.get_instance()









