from dataclasses import dataclass
import pickle
from settings import Config
import os

@dataclass
class CleanData():
    '''
    CleanData class is used to store the particles that are
    having volume less than the threshold value.
    (list of cp_ids and volume threshold)
    '''

    vol_threshold: int = 0
    cp_ids: list = None

    # save to pickle file
    def save(self):
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)
        with open(Config.CLEAN_DATA_FILE, 'wb') as f:
            pickle.dump(self, f)

    # load from pickle file
    def load(self):
        try:
            with open(Config.CLEAN_DATA_FILE, 'rb') as f:
                data_obj = pickle.load(f)
                self.vol_threshold = data_obj.vol_threshold
                self.cp_ids = data_obj.cp_ids
        except:
            print("Error loading clean data file / file not found")
            self.cp_ids = []
