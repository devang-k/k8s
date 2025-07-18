from utils.writer.writer import Writer
from gdsast import gds_write
import logging
from json import dump

logger = logging.getLogger('sivista_app')

class GDSWriter(Writer):
    def __init__(self):
        super().__init__()

    def write(self, data: dict, oname: str):
        with open(oname, "wb") as f:
            gds_write(f, data)
        logger.info(f"GDS file {oname} written successfully.")
        with open(oname.replace('.gds', '.json'), "w") as f:
            dump(data, f, indent=2)

    def close(self):
        pass