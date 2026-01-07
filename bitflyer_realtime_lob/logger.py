import os

from logging import (
    Logger as _Logger,
    DEBUG,
    FileHandler,
    Formatter
)


class Logger(_Logger):
    def __init__(self,
                 output_directory: str):
        super().__init__(__name__, level=DEBUG)
        
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        file_handler = FileHandler(filename=os.path.join(output_directory, "bitflyer_realtime_lob.log"))
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)