import os

from isambard_dev.add_ons.filesystem import obsolete_codes_from_pdb, local_pdb_codes, current_codes_from_pdb, \
    make_code_obsolete
from isocket_settings import global_settings
from isocket_app.populate_models import add_pdb_code, remove_pdb_code, datasets_are_valid

structural_database = global_settings["structural_database"]["path"]
log_folder = os.path.join(structural_database, 'isocket_logs')


class CodeList:
    def __init__(self, data_dir=structural_database):
        self.data_dir = data_dir

    @property
    def local_codes(self):
        return local_pdb_codes(data_dir=self.data_dir)

    @property
    def to_add(self):
        current_codes = current_codes_from_pdb()
        return set(current_codes) - set(self.local_codes)

    @property
    def to_remove(self):
        obsolete_codes = obsolete_codes_from_pdb()
        return set(self.local_codes).intersection(set(obsolete_codes))


class UpdateSet:
    def __init__(self, add_codes=None, remove_codes=None):
        #TODO configure logging
        self.add_codes = add_codes
        self.remove_codes = remove_codes


# TODO Add code for checking db integrity. As a test? in here, or populate_models? Best way to do this?

class UpdateCode:
    def __init__(self, code, log=None, log_shelf=None):
        self.code = code
        self.log = log
        self.log_shelf = log_shelf

    def add(self):
        try:
            add_pdb_code(code=self.code)
            # validate database
            if not datasets_are_valid():
                remove_pdb_code(code=self.code)
        except Exception as e:
            if self.log is not None:
                # process log message
                pass
            if self.log_shelf is not None:
                # add code and error to shelf
                pass
            else:
                raise e
        return




