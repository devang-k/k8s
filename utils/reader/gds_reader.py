from gdsast import gds_read
from utils.reader.reader import Reader
import logging
from json import dumps

logger = logging.getLogger('sivista_app')

class GDSReader(Reader):
    def __init__(self, write_json=False):
        super().__init__()
        self.write_json = write_json

    def read(self, gds_file: str):
        '''
        convert gds file (name) to json format
        '''
        try:
            with open(gds_file, "rb") as f:
                gds_data = gds_read(f)
            if self.write_json:
                json_file = gds_file.replace('.gds', '.json')
                with open(json_file, "w") as f:
                    f.write(dumps(gds_data))
            return gds_data
        except Exception as e:
            logger.error(f"Error in read gds file {gds_file}: {e}")
            return None

    def close(self):
        pass