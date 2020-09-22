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
        return json.dumps(self._regime['args'])

    def to_string(self):
        return f'{self._block_num}-{self._block_type}: regime '\
               f'{self._regime_num}, task \'{self.task_name}\''


# This gets ***copied*** into a new process's memory space
# Hence, don't have to worry about locking around calls to
# write_to_data_log or write_to_blocks_log
class LoggerInfo:
    def __init__(self, input_file_name):
        self._seed = datetime.now()
        random.seed(self._seed)
        # load input data
        with open(sys.argv[1]) as f:
            self._data = json.load(f)
        self._logs_base = os.path.join(os.getcwd(), self._data['logging_base'])
        self._logger = self._create_logger(self._logs_base)
        self._workers = self._data['threads']

        # Create output directory wihin the logs base (i.e. the syllabus-timestamp folder)
        input_name = sys.argv[1].split(os.path.sep)[-1]
        timestamp = l2logger.PerformanceLogger.get_readable_timestamp()
        self._scenario_dirname = f'{input_name}-{timestamp}'
        scenario_path = os.path.join(self._logs_base, self._scenario_dirname)
        os.makedirs(scenario_path, exist_ok=True)

        # Copy this input file into the output directory
        copy_path = os.path.join(scenario_path, input_name)
        shutil.copy(sys.argv[1], copy_path)

    @property
    def data(self): 
        return self._data
    @property
    def workers(self):
        return self._workers
    @property
    def logger(self):
        return self._logger

    def get_scenario_info(self, regime_info, worker_name):
        return {
            'scenario_dirname': self._scenario_dirname,
            'worker_dirname': worker_name,
            'block_dirname': '-'.join((str(regime_info.block_num), regime_info.block_type))
        }

    def write_regime(self, regime_info, worker_index):
        worker_name = f'worker-{worker_index}'
        regime_record = {
            'block_num': regime_info.block_num,
            'regime_num': regime_info.regime_num,
            'block_type': regime_info.block_type,
            'worker': worker_name,
            'task_name': regime_info.task_name,
            'params': regime_info.params
        }
        scenario_info = self.get_scenario_info(regime_info, worker_name)
        self.logger.write_to_blocks_log(regime_record, scenario_info)

    def write_data(self, regime_info, exp_num, reward=1, status='Done'):
        timestamp = l2logger.PerformanceLogger.get_readable_timestamp()
        data_record = {
            'block_num': regime_info.block_num,
            'regime_num': regime_info.regime_num,
            'exp_num': exp_num,
            'status': status,
            'timestamp': timestamp,
            'reward': reward,
            'rand-seed': self._seed
        }
        self.logger.write_to_data_log(data_record)

    def _create_logger(self, logs_base):
        if not os.path.exists(logs_base):
            print(f'Creating logging directory: {logs_base}')
            os.makedirs(logs_base)
        else:
            print(f'Using existing logging directory: {logs_base}')
        # log root in current directory
        syllabus_info = {
            'author': 'Ben Stoler',
            'script': __file__
        }
        cols = ['reward']
        return l2logger.RLPerformanceLogger(logs_base, cols, syllabus_info)
