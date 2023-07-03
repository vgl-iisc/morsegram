from enum import Enum
import pickle
from settings import Config
import os
import logging

class Label(Enum):
    NO_LABEL = 0
    CORRECT_SEGMENTATION = 1
    INCORRECT_SEGMENTATION = 2

    @staticmethod
    def get_label(value):
        for l in Label:
            if l.value == value:
                return l


class LabelList:
    '''
    This class is used to store the labels of the particles
    Initially, the label is set to NO_LABEL for all particles
    If a particle is correctly segmented, the label is set to CORRECT_SEGMENTATION
    else, the label is set to INCORRECT_SEGMENTATION
    labels are stored in a dictionary with particle_id as key and label as value
    and saved to a file using pickle
    '''
    def __init__(self):
        '''
        Initialize the label list
        '''
        if os.path.exists(Config.LABEL_LIST_FILE):
            self.load()
        else:
            self.particle_label_dict = {}
            self.save()
        
    def add_particle(self, label, particle_id):
        '''
        Add a particle to the label list
        @param label: label of the particle
        @param particle_id: id of the particle
        '''
        self.particle_label_dict[particle_id] = label

        # checkpoint - to avoid data loss in case of crash
        if self.particle_label_dict.keys().__len__() % 10 == 0:
            self.save()
            logging.info("Saved label list to file")
        
    def get_particles(self, label):
        '''
        Get the list of particles with the given label
        @param label: label of the particles
        @return: list of particles
        '''
        return [particle_id for particle_id in self.particle_label_dict.keys()
                     if self.particle_label_dict[particle_id] == label]

    def get_particle_label(self, particle_id):
        '''
        Get the label of the particle
        @param particle_id: id of the particle
        @return: label of the particle
        '''
        try:
            return self.particle_label_dict[particle_id]
        except KeyError:
            return None
    
    def save(self):
        '''
        Save the label list to a file
        '''
        with open(Config.LABEL_LIST_FILE, 'wb') as f:
            pickle.dump(self.particle_label_dict, f)
            
    def load(self):
        '''
        Load the label list from a file
        '''
        with open(Config.LABEL_LIST_FILE, 'rb') as f:
            self.particle_label_dict = pickle.load(f)



