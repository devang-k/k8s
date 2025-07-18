from sivista_db.models.permutation_model import Permutation
logger = logging.getLogger('sivista_app')
class PermutationHandler():
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.permutation_data_list = []

    def write(self, permutation):
        self.permutation_data_list.append(permutation)
        if len(self.permutation_data_list) >= 4500:
            self.bulk_insert_permutations()
            self.permutation_data_list.clear() # Reset the list after insert

    def final_insert(self):
        if self.permutation_data_list:  # Check if the list is not empty
            self.bulk_insert_permutations()
            logger.debug(f"Final insert of {len(self.permutation_data_list)} records.")
            self.permutation_data_list = []  # Reset for safety

    def bulk_insert_permutations(self):
        # Open a session for bulk insert
        session = self.db_manager.get_session()
        try:
            session.bulk_save_objects(self.permutation_data_list)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def read(self, cell_name):
        session = self.db_manager.get_session()
        try:
            like_pattern = f'{cell_name}%'
            permutations = session.query(Permutation).filter(Permutation.file_name.like(like_pattern)).all()
            return permutations
        finally:
            session.close()