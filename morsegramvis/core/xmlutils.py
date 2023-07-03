import xml.etree.ElementTree as ET
from settings import Config
import os
import logging


def save_settings(parent):
    '''
    Save the settings
    @param parent: the parent
    '''
    # get the value
    lighting = {k: v.value() for k, v in parent.lighting.items()}
    ao = {k: int(v.text()) for k, v in parent.ao.items()}
    rgb = {k: v.value() for k, v in parent.rgb.items()}

    # base folder
    base_folder = parent.lineEdit.text()

    # dictionary of tag and value
    tag_value_dict = {"lighting": lighting,
                      "ao"      : ao,
                      "rgb"     : rgb,
                      "base_folder": base_folder}

    setting_tag = {"settings": tag_value_dict}

    # create a root tag
    root = ET.Element("root")

    # iterate through the settings
    for k, v in setting_tag.items():
        # create a settings tag
        settings = ET.SubElement(root, k)
        # iterate through the settings
        for k, v in v.items():
            # create a tag
            ET.SubElement(settings, k).text = str(v)
    
    # write the xml file
    tree = ET.ElementTree(root)

    # write the xml file
    tree.write(base_folder + "/settings.xml")


    # read the xml file Config.APP_DATA_DIR + "/settings.xml"
    if not os.path.exists(Config.APP_DATA_DIR + "/settings.xml"):
        tree.write(Config.APP_DATA_DIR + "/settings.xml")

    # read the xml file
    xml = ET.parse(Config.APP_DATA_DIR + "/settings.xml").getroot()

    check_settings = False # check if the settings already exist

    # iterate through the xml file
    for settings in xml:
        # check if the settings already exist
        if settings.find("base_folder").text == base_folder:
            check_settings = True
            break
    
    # if the settings already exist
    if check_settings == True:
        # iterate through the settings
        for k, v in setting_tag.items():
            # iterate through the settings
            for k, v in v.items():
                # update the value
                settings.find(k).text = str(v)
    else:
        # create a settings tag
        settings = ET.SubElement(xml, "settings")
        # iterate through the settings
        for k, v in setting_tag.items():
            # iterate through the settings
            for k, v in v.items():
                # create a tag
                ET.SubElement(settings, k).text = str(v)
    
    # write the xml file
    tree = ET.ElementTree(xml)
    tree.write(Config.APP_DATA_DIR + "/settings.xml")

    Config.set_base_folder(setting_tag)

    # close the window
    parent.close()


def get_settings():
    '''
    Get the settings from the xml file
    @return: the settings
    '''
    list_settings = []

    try:
    # read the xml file
        xml = ET.parse(Config.APP_DATA_DIR + "/settings.xml").getroot()

        # iterate through the xml file
        for settings in xml:
            # create a dictionary
            dict_settings = {}
            # iterate through the settings
            for setting in settings:
                # add the tag and value to the dictionary
                dict_settings[setting.tag] = setting.text
            # add the dictionary to the list
            list_settings.append({settings.tag: dict_settings})
    except:
        logging.getLogger().warning("No settings file found")
    
    return list_settings


def remove_settings(base_folder):
    '''
    Remove the settings from the xml file
    for the given base folder(Dataset)
    @param base_folder: the base folder
    '''

    # read the xml file
    xml = ET.parse(Config.APP_DATA_DIR + "/settings.xml").getroot()

    # iterate through the xml file
    for settings in xml:
        # check if the settings already exist
        if settings.find("base_folder").text == base_folder:
            # remove the settings
            xml.remove(settings)
            break
    
    # write the xml file
    tree = ET.ElementTree(xml)
    tree.write(Config.APP_DATA_DIR + "/settings.xml")



