import os
import pickle
import datetime
import logging
import signal

from isambard_dev.add_ons.filesystem import obsolete_codes_from_pdb, local_pdb_codes, current_codes_from_pdb
from isocket_settings import global_settings
from isocket.populate_models import add_pdb_code, remove_pdb_code, datasets_are_valid, process_holding_pickle

structural_database = global_settings["structural_database"]["path"]
log_folder = os.path.join(structural_database, 'isocket_logs')
problem_codes = os.path.join(global_settings['package_path'], 'isocket', 'problem_codes.p')


class TimeoutException(Exception):   # Custom exception class
    pass


def timeout_handler(signum, frame):   # Custom signal handler
    raise TimeoutException

# Change the behavior of SIGALRM
signal.signal(signal.SIGALRM, timeout_handler)


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
        with open(problem_codes, 'rb') as foo:
            codes = {x[0] for x in pickle.load(foo)}
        return codes


def set_up_logger():
    today = datetime.date.today()
    year_folder = os.path.join(log_folder, str(today.year))
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
    def __init__(self, add_codes=None, remove_codes=None, mode='production'):
        assert(datasets_are_valid())
        self.logger = set_up_logger()
        self.add_codes = add_codes
        self.remove_codes = remove_codes
        self.mode = mode
        self.errors = []

    def run_update(self, timeout=120):
        if self.add_codes is not None:
            for code in self.add_codes:
                try:
                    UpdateCode(code=code, logger=self.logger).add(timeout=timeout, mode=self.mode)
                except Exception as e:
                    self.errors.append((code, e))
        if self.remove_codes is not None:
            for code in self.remove_codes:
                UpdateCode(code=code, logger=self.logger).remove()
        self.clear_up_and_assert()
        return

    def clear_up_and_assert(self, error_report=problem_codes):
        process_holding_pickle(mode=self.mode)
        try:
            errors = pickle.load(open(error_report, 'rb'))
        except (FileNotFoundError, EOFError):
            errors = []
        errors += self.errors
        pickle.dump(errors, open(error_report, 'wb'))
        # assertions to be added!


class UpdateCode:
    def __init__(self, code, logger=None):
        self.code = code
        self.logger = logger

    def add(self, timeout=None, mode='production'):
        try:
            if timeout is not None:
                signal.alarm(timeout)
            add_pdb_code(code=self.code, mode=mode)
            if self.logger is not None:
                self.logger.info('Added code {0}'.format(self.code))
        except Exception as e:
            if self.logger is not None:
                self.logger.debug('Error adding code {0}\n{1}'.format(self.code, e))
            raise e
        else:
            if timeout is not None:
                signal.alarm(0)
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



