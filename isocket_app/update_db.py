import os

from isambard_dev.add_ons.filesystem import obsolete_codes_from_pdb, local_pdb_codes, current_codes_from_pdb, \
    make_code_obsolete
from isocket_settings import global_settings

structural_database = global_settings["structural_database"]["path"]
log_folder = os.path.join(structural_database, 'isocket_logs')


class CodeList:
    def __init__(self, data_dir=structural_database):
        self.data_dir = data_dir
        self.to_add = self.get_codes_to_add()
        self.to_remove = self.get_codes_to_remove()

    @property
    def local_codes(self):
        return local_pdb_codes(data_dir=self.data_dir)

    def get_codes_to_add(self):
        current_codes = current_codes_from_pdb()
        return list(set(current_codes) - set(self.local_codes))

    def get_codes_to_remove(self):
        obsolete_codes = obsolete_codes_from_pdb()
        return list(set(self.local_codes).intersection(obsolete_codes))



class UpdateSet:
    def __init__(self, add_codes=None, remove_codes=None):
        #TODO configure logging
        self.add_codes = add_codes
        self.remove_codes = remove_codes



# TODO Add code for checking db integrity. As a test? in here, or populate_models? Best way to do this?

