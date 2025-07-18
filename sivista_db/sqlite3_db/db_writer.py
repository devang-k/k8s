from utils.writer.writer import *

from sqlalchemy.dialects.sqlite import insert
import logging
from sivista_db.sqlite3_db.db_manager import SqlDbManager
logger = logging.getLogger('sivista_app')

class DbWriter(Writer):

    def __init__(self):
        self.db_manager = SqlDbManager.get_instance()
        self.session = self.db_manager.start_session()
        self.data_list = []

    def write(self,data_row):
        self.data_list.append(data_row)
        if len(self.data_list) >= 4500:
            self.bulk_insert()       
            self.data_list.clear()

    def final_write(self):      
        if self.data_list:  
            self.bulk_insert()
            logger.debug(f"Final insert of {len(self.data_list)} records.")
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
        
    def upsert(self, model_table, data, index_elements):
        """
        Generic upsert function for SQLAlchemy models.

        :param session: SQLAlchemy Session instance.
        :param model: SQLAlchemy model class.
        :param data: Dictionary of data to upsert.
        :param index_elements: List of column names that constitute the unique constraint.
        """
           
        # Construct the on_conflict_do_update statement based on the provided index_elements
        upsert_stmt = insert(model_table).values(**data).on_conflict_do_update(
                index_elements = index_elements,  # Adjust based on your unique constraint
                set_={key: insert(model_table).excluded[key] for key in data}
            )
        # Execute the upsert statement
        self.session.execute(upsert_stmt)
        self.session.commit()   
        # Execute the upsert statement
      

    def close(self):
        self.final_write()
        # close session
        self.session.close()
        self.db_manager.close()
      