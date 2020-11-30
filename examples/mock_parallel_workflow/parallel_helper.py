# This is a helper file for the parallel_example.py script.
# It consists of two helper classes, LoggerInfo and RegimeInfo
# used to store/output relevant data to the main script.

import json
import random
import shutil
from datetime import datetime
import os
import sys

from l2logger import l2logger

class RegimeInfo:
    def __init__(self, block_num, block_type, regime_num, regime):
        self._block_num = block_num
        self._block_type = block_type
        self._regime_num = regime_num
        self._regime = regime
    
    @property
    def block_num(self):
        return self._block_num
    @property
    def block_type(self):
        return self._block_type
    @property
    def regime_num(self):
        return self._regime_num
    @property
    def task_name(self):
        return self._regime['task']
    @property
    def params(self):
        return self._regime['args']

    def to_string(self):
        return f'{self._block_num}-{self._block_type}: regime '\
               f'{self._regime_num}, task \'{self.task_name}\''


# This gets ***copied*** into a new process's memory space
# Hence, don't have to worry about locking around calls to
# write_to_data_log or write_new_regime
class LoggerInfo:
    def __init__(self, input_file_name):
        self._seed = datetime.now()
        random.seed(self._seed)
        # load input data
        with open(sys.argv[1]) as f:
            self._data = json.load(f)
        self._logs_base = os.path.join(os.getcwd(), self._data['logging_base'])
        input_name = sys.argv[1].split(os.path.sep)[-1]
        print(input_name)
        self._scenario_dirname = input_name
        self._logger = self._create_logger(self._logs_base)
        self._workers = self._data['threads']

    @property
    def data(self): 
        return self._data
    @property
    def workers(self):
        return self._workers
    @property
    def logger(self):
        return self._logger

    def write_data(self, regime_info, exp_num, worker_id):
        data_record = {
            'block_num': regime_info.block_num,
            'worker_id': worker_id,
            'block_type': regime_info.block_type,
            'task_name': regime_info.task_name,
            'task_params': regime_info.params,
            'exp_num': exp_num,
            'reward': 1
        }
        self.logger.log_record(data_record)

    def _create_logger(self, logs_base):
        if not os.path.exists(logs_base):
            print(f'Creating logging directory: {logs_base}')
            os.makedirs(logs_base)
        else:
            print(f'Using existing logging directory: {logs_base}')
        # log root in current directory
        scenario_info = {
            'author': 'JHU APL',
            'complexity': '1-low',
            'difficulty': '2-medium',
            'script': __file__
        }
        logger_info = {'metrics_columns': ['reward'],
                       'log_format_version': '1.0'}
        return l2logger.DataLogger(logs_base, self._scenario_dirname, logger_info, scenario_info)
