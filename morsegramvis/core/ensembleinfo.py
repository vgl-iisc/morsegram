import xml.etree.ElementTree as ET
from settings import Config
import os


class EnsembleInfo:
    """
    This class contains the information about the ensemble
    like length, width, height, name, persistence value, etc.
    """
    
    def __init__(self):
        '''
        Initialize the ensemble info
        '''
        self.length = 0
        self.width = 0
        self.height = 0
        self.pers_val = 0
        self.pers_curve = None
        self.num_particles = 0
        self.dataset_name = None

    def save(self):
        """
        Save the ensemble info to the xml file
        :return: None
        """
        root = ET.Element('ensembleinfo')

        for k, v in self.__dict__.items():
            ET.SubElement(root, k).text = str(v)

        tree = ET.ElementTree(root)
        tree.write(Config.ENSEMBLE_INFO_FILE)

    @staticmethod
    def load():
        """
        Load the ensemble info from the xml file
        :return: ensemble info
        """
        
        ensemble_info = EnsembleInfo()

        if os.path.exists(Config.ENSEMBLE_INFO_FILE):
            tree = ET.parse(Config.ENSEMBLE_INFO_FILE)
        
            root = tree.getroot()

            for child in root:
                ensemble_info.__setattr__(child.tag, child.text)

        else:
            ensemble_info.save()

        return ensemble_info


