import os
import shelve
import datetime
import logging

from isambard_dev.add_ons.filesystem import obsolete_codes_from_pdb, local_pdb_codes, current_codes_from_pdb, \
    make_code_obsolete
from isocket_settings import global_settings
from isocket_app.populate_models import add_pdb_code, remove_pdb_code, datasets_are_valid

structural_database = global_settings["structural_database"]["path"]
log_folder = os.path.join(structural_database, 'isocket_logs')
problem_code_shelf = os.path.join(global_settings['package_path'], 'isocket_app', 'problem_codes')

class CodeList:
    def __init__(self, data_dir=structural_database):
        self.data_dir = data_dir

    @property
    def local_codes(self):
        return local_pdb_codes(data_dir=self.data_dir)

    @property
    def to_add(self):
        current_codes = current_codes_from_pdb()
        return set(current_codes) - set(self.local_codes) - self.problem_codes()

    @property
    def to_remove(self):
        obsolete_codes = obsolete_codes_from_pdb()
        return set(self.local_codes).intersection(set(obsolete_codes))

    def problem_codes(self):
        with shelve.open(problem_code_shelf) as shelf:
            codes = list(shelf.keys())
        return codes


def set_up_logger():
    today = datetime.date.today()
    year_folder = os.path.join(log_folder, today.year)
    if not os.path.exists(year_folder):
        os.mkdir(year_folder)
    log_file = os.path.join(year_folder, '{}.log'.format(today.isoformat()))
    logger = logging.getLogger(name=__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger



class UpdateSet:
    def __init__(self, add_codes=None, remove_codes=None):
        self.logger = set_up_logger()
        self.add_codes = add_codes
        self.remove_codes = remove_codes


# TODO Add code for checking db integrity. As a test? in here, or populate_models? Best way to do this?

class UpdateCode:
    def __init__(self, code, logger=None, log_shelf=problem_code_shelf):
        self.code = code
        self.logger = logger
        self.log_shelf = log_shelf

    def add(self):
        try:
            add_pdb_code(code=self.code)
            if self.logger is not None:
                self.logger.info('Added code {0}'.format(self.code))
        except Exception as e:
            if self.logger is not None:
                self.logger.debug('Error adding code {0}\n{1}'.format(self.code, e))
            if self.log_shelf is not None:
                with shelve.open(self.log_shelf) as shelf:
                    shelf[self.code] = e
            else:
                raise e
        return

    def remove(self):
        try:
            remove_pdb_code(code=self.code)
            if self.logger is not None:
                self.logger.info('Removed code {0}'.format(self.code))
        except Exception as e:
            if self.logger is not None:
                self.logger.debug('Error removing code {0}\n{1}'.format(self.code, e))
            else:
                raise e
        return



