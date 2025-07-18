from sivista_db.repository.base_repository import BaseRepository
from sqlalchemy.dialects.sqlite import insert
from sivista_db.models.capacitance_model import CapacitanceMetrics

class CapacitanceRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(CapacitanceMetrics)
    
    def upsert(self,data_dict):
        """
        Generic upsert function for SQLAlchemy models.
        :param session: SQLAlchemy Session instance.
        :param model: SQLAlchemy model class.
        :param data: Dictionary of data to upsert.
        :param index_elements: List of column names that constitute the unique constraint.
        """
        for data in data_dict:
        # Construct the on_conflict_do_update statement based on the provided index_elements
            upsert_stmt = insert(CapacitanceMetrics.__table__ ).values(**data).on_conflict_do_update(
                    index_elements = ["permutation_id"],  # Adjust based on your unique constraint
                    set_={key: insert(CapacitanceMetrics.__table__ ).excluded[key] for key in data}
                )
            # Execute the upsert statement
            self.session.execute(upsert_stmt)
            self.session.commit() 
    
