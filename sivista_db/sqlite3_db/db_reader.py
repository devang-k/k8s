from utils.reader.reader import Reader
from sqlalchemy import and_
from sivista_db.sqlite3_db.db_manager import SqlDbManager
import logging
logger = logging.getLogger('sivista_app')
class DbReader(Reader):
        def __init__(self):
             self.db_manager = SqlDbManager.get_instance()
             self.session = self.db_manager.start_session()

        def read(self, model_class, like_pattern):
              try:
                query = self.session.query(model_class)
                if like_pattern:
                    query = query.filter(model_class.file_name.like(like_pattern))
                return query.all()
              except Exception as e:
                        logger.error(f"Error during read operation: {e}")
                        # Handle or log the error as needed
                        raise
              
        def close(self):
              self.session.close()
              self.db_manager.close()

    