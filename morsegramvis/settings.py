import os
import logging
import time

class Config:
    '''
    This class contains all the configuration variables
    '''

    APP_BANNER = "VGL, IISc"
    APP_NAME = "MorseGramVis"
    APP_FOOTER = "A Visualization and Analysis Tool for Segmented Granular Media"

    # icons folder
    ICONS_DIR = "ui/icons/"
    COLORMAPS_DIR = "colormap"

    APP_DATA_DIR = ".morsegram"
    FILE_EXT = ".vtp"
    BASE_DIR = ""
    PERS_CURVE_FILE = None

    BG_COLOR = (0, 0, 0)
    AMBIENT = 0.5
    DIFFUSE = 0.5
    SPECULAR = 1
    SPECULAR_POWER = 100
    AMBIENT_OCCLUSION_CONSTANT = 0
    AMBIENT_OCCLUSION_KERNEL_SIZE = 128

    def __init__(self):
        pass

    @staticmethod
    def isinit():
        return Config.BASE_DIR != ""

    @staticmethod
    def set_base_folder(data):
        data = data['settings']
        # update lighting
        lighting = data['lighting']

        if isinstance(lighting, str):
        # {'ambient': 50, 'diffuse': 50, 'specular': 100, 'specular power': 100}
        # parse the lighting data
            l_data = lighting.replace("{", "").replace("}", "").replace("'", "").split(",")
            l_data = [i.split(":") for i in l_data]
            l_data = {i[0].strip(): float(i[1].strip()) for i in l_data}
        else:
            l_data = lighting

        Config.AMBIENT = l_data['ambient'] / 100
        Config.DIFFUSE = l_data['diffuse'] / 100
        Config.SPECULAR = l_data['specular'] / 100
        Config.SPECULAR_POWER = l_data['specular power']
        
        # update ambient occlusion
        # {'ambient occlusion factor': 0, 'kernel size': 128}
        # parse the ambient occlusion data
        if isinstance(data['ao'], str):
            ao_data = data['ao'].replace("{", "").replace("}", "").replace("'", "").split(",")
            ao_data = [i.split(":") for i in ao_data]
            ao_data = {i[0].strip(): int(i[1].strip()) for i in ao_data}
        else:
            ao_data = data['ao']

        Config.AMBIENT_OCCLUSION_CONSTANT = ao_data['ambient occlusion factor']
        Config.AMBIENT_OCCLUSION_KERNEL_SIZE = ao_data['kernel size']

        # update rgb
        # {'red': 0, 'green': 0, 'blue': 0}
        # parse the rgb data
        if isinstance(data['rgb'], str):
            rgb_data = data['rgb'].replace("{", "").replace("}", "").replace("'", "").split(",")
            rgb_data = [i.split(":") for i in rgb_data]
            rgb_data = {i[0].strip(): int(i[1].strip()) for i in rgb_data}
        else:
            rgb_data = data['rgb']

        Config.BG_COLOR = (rgb_data['red'], rgb_data['green'], rgb_data['blue'])

        Config.BASE_DIR = data['base_folder']

        # iterate over all files in the folder
        for filename in os.listdir(Config.BASE_DIR):
            if filename.endswith("segmentation" + Config.FILE_EXT):
                Config.SEGMENTATION_FILE   = Config.BASE_DIR + "/" + filename
            elif filename.endswith("contact_regions" + Config.FILE_EXT):
                Config.CONTACT_REGION_FILE = Config.BASE_DIR + "/" + filename
            elif filename.endswith("contacts" + Config.FILE_EXT):
                Config.CONTACT_NET_FILE    = Config.BASE_DIR + "/" + filename
            elif filename.endswith("grain_centres" + Config.FILE_EXT):
                Config.MAXIMAS_FILE        = Config.BASE_DIR + "/" + filename
            elif filename.endswith("contacts_all" + Config.FILE_EXT):
                Config.ALL_CONTACTS_FILE = Config.BASE_DIR + "/" + filename
            elif filename.endswith("_initial.txt"):
                Config.PERS_VAL_FILE = Config.BASE_DIR + "/" + filename
            elif filename.endswith(".svg"):
                Config.PERS_CURVE_FILE = Config.BASE_DIR + "/" + filename

        Config.PARTICLES_MESH_DIR = Config.BASE_DIR + "/ensemble/"
        Config.DEM_DIR = Config.BASE_DIR + "/dem/"
        Config.SURFACE_PC_DIR = Config.BASE_DIR + "/surface_points/"
        Config.CONTACT_REGION_DIR = Config.BASE_DIR + "/contact_regions/"
        Config.UNDER_SEGMENTATION_DIR = Config.BASE_DIR + "/under_segmentations/"
        Config.DATA_DIR = Config.BASE_DIR + "/data/"
        Config.COMM_DIR = Config.DATA_DIR + "communities/"
        Config.INPUT_DIR = Config.BASE_DIR + "/input/"
        Config.CHAMFER_DIR = Config.BASE_DIR + "/chamfer/"
        Config.VOL_DATA = Config.DATA_DIR + "vol_data.txt"
        Config.VOL_BINS = Config.DATA_DIR + "vol_bins.txt"
        Config.PC_DIR = Config.BASE_DIR + "/grains/"

        # remove attribute RAW_IMAGE_FILE
        if hasattr(Config, "RAW_IMAGE_FILE"):
            delattr(Config, "RAW_IMAGE_FILE")

        try:
            for f in os.listdir(Config.CHAMFER_DIR):
                if f.endswith(".mhd"):
                    Config.RAW_IMAGE_FILE = Config.CHAMFER_DIR + f
        except Exception as e:
            logging.getLogger().error("Error while reading raw image file: {}".format(e))

        Config.PARTICLE_STATS_FILE = Config.DATA_DIR + "all_particle_stats.csv"
        Config.ENSEMBLE_FILE = Config.BASE_DIR + "/ensemble.vtu"
        Config.ENSEMBLE_CLEAN_FILE = Config.BASE_DIR + "/ensemble_clean.vtu"
        Config.CP3_FILE = Config.BASE_DIR + "/cps_3.vtp"
        Config.CP2_FILE = Config.BASE_DIR + "/cps_2.vtp"
        Config.CP_PAIR_FILE = Config.BASE_DIR + "/cp_pairs.csv"
        Config.SIMPLIFIED_DIR = Config.BASE_DIR + "/simplified/"

        Config.CURRENT_FILE_LOC = os.path.dirname(os.path.realpath(__file__))
        Config.QUERY_ENGINE_CODE = Config.CURRENT_FILE_LOC + "/core/queryengine_bk.py"

        # pickle file to store the data
        Config.CLEAN_DATA_FILE = Config.DATA_DIR + "clean_data.pkl"

        # =========== Debugging ===========
        Config.LOGS_DIR = Config.BASE_DIR + "/logs/"

        Config.LABEL_LIST_FILE = Config.DATA_DIR + "label_list.pkl"
        Config.ENSEMBLE_INFO_FILE = Config.DATA_DIR + "ensemble_info.xml"

        # create a log file with the current time and date
        # create logs folder if not exists
        if not os.path.exists(Config.LOGS_DIR):
            os.makedirs(Config.LOGS_DIR)
        # check config.data folder exists
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)
        
        logging.basicConfig(filename=Config.LOGS_DIR + time.strftime("%Y%m%d-%H%M%S") + ".log",
                                 level=logging.INFO)