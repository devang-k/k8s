from sivista_db.models.permutation_model import Permutation
from sivista_db.repository.base_repository import BaseRepository
class PermutationRepository(BaseRepository):
    def __init__(self):
        super().__init__(Permutation)
        
    def insert_in_bulk(self, data):       
        try:
            self.session.bulk_save_objects(data)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def fetch_records_cell_name(self, cell_name):
       
        try:
            like_pattern = f'{cell_name}%'
            permutations = self.session.query(Permutation).filter(Permutation.file_name.like(like_pattern)).all()
            return permutations
        finally:
            self.session.close()


    def close(self):
        if self.data_list:
            self.final_write()
        
        self.db_manager.close()
