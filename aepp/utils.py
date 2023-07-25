from configparser import ConfigParser
import os

class Utils:

    global config_path

    def __init__(self):
        self.config_path = os.path.join(os.environ["ADOBE_HOME"], "conf", "config.ini")

    def check_if_exist(self, section, field_name):
        config = ConfigParser()
        config.read(self.config_path)
        exist_field = config.get(section, field_name)
        if exist_field:
            return exist_field
        else:
            return None

    def save_field_in_config(self, section, field_name, value):
        config = ConfigParser()
        config.read(self.config_path)
        config.set(section, field_name, value)
        with open(self.config_path, "w") as configfile:
            config.write(configfile)