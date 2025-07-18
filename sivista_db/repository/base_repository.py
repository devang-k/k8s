import logging
from sivista_db.db_manager import SqlDbManager
from sqlalchemy.dialects.sqlite import insert

logger = logging.getLogger('sivista_app')
class BaseRepository:
    def __init__(self, model):
        self.db_manager = SqlDbManager.get_instance()
        self.session =  self.db_manager.start_session()
        self.model = model
        self.data_list =[]

    def add(self, entity):
        self.session.add(entity)

    def get_by_id(self, id):
        return self.session.query(self.model).filter_by(id=id).first()
    
    def write(self,data_row):
        # logging.info("calling write..")
        self.data_list.append(data_row)
        if len(self.data_list) >= 4500:
            self.bulk_insert()       
            self.data_list.clear()

    def final_write(self):      
        if self.data_list:  
            self.bulk_insert()
            print(f"Final insert of {len(self.data_list)} records.")
            # Reset for safety
            self.data_list.clear()  

    def bulk_insert(self):        
        try:
            self.session.bulk_save_objects(self.data_list)
            self.session.commit()                  
            logging.info(f"{len(self.data_list)} records of type {type(self.data_list[0])} inserted......")
        except Exception as e:
            logging.error(f" Bulk insert failed :{e}")
            self.session.rollback()
            raise e
   
    def close(self):
        self.db_manager.close()
        
        


