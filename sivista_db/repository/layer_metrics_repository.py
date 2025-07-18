
from sivista_db.repository.base_repository import BaseRepository
from sivista_db.models.layer_metrics_model import LayerMetrics
from sivista_db.models.permutation_model import Permutation
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select
import pandas as pd

class LayerMetricsRepository(BaseRepository):
    def __init__(self):
        super().__init__(LayerMetrics)

    def upsert(self, data):
        """
        Generic upsert function for SQLAlchemy models.

        :param session: SQLAlchemy Session instance.
        :param model: SQLAlchemy model class.
        :param data: Dictionary of data to upsert.
        :param index_elements: List of column names that constitute the unique constraint.
        """        
        # Construct the on_conflict_do_update statement based on the provided index_elements   
        upsert_stmt = insert(LayerMetrics.__table__).values(**data).on_conflict_do_update(
                index_elements = ['permutation_id', 'Layer','Adjacent Layer'] ,  # Adjust based on your unique constraint
                set_={key: insert(LayerMetrics.__table__).excluded[key] for key in data}
            )
        # Execute the upsert statement
        self.session.execute(upsert_stmt)
        self.session.commit()  

    def read_by_permutation_id_cell_name(self, cell_name):
        subquery = select(Permutation.permutation_id).where(Permutation.file_name.like(f'{cell_name}%')).subquery()
        query = select(LayerMetrics).where(LayerMetrics.permutation_id.in_(subquery))
        df = pd.read_sql(query, self.db_manager.engine.raw_connection)
         #results = self.session.execute(query).scalars().all()
        return df
    
    # subquery = select(Permutation.permutation_id).where(Permutation.file_name.like(f'{cell_name}%')).subquery()
    
    # # Construct the main query to select from LayerMetrics where permutation_id is in the subquery
    # query = select(LayerMetrics).where(LayerMetrics.permutation_id.in_(subquery))
    
    # # Convert the query to a DataFrame directly using read_sql()
    # 