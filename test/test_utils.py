import json
import unittest
import os
import csv
from collections import deque
from l2logger import l2logger
from copy import deepcopy


DEFAULT_REGIME_ROWS = ['block_num', 'regime_num', 'block_type',
                       'worker', 'task_name', 'params']
DEFAULT_DATA_ROWS = ['block_num', 'regime_num', 'exp_num',
                     'status', 'timestamp']
REGIME_FILENAME = 'block-info.tsv'
DATA_FILENAME = 'data-log.tsv'
SCENARIO_FILENAME = 'scenario_info.json'
COLUMN_FILENAME = 'column_info.json'

class FakeExpectedLog:
    def __init__(self):
        # more lazy initialization
        self._headers = []
        self._rows = []

    # hard asserts since this is in the creation of the data structure
    # compare the written log to
    def add_row(self, record, headers):
        if not(len(self._headers)):
            self._headers = deepcopy(headers)
            self._rows = [self._headers]
        assert(len(self._headers) == len(list(record.keys())))
        row = []
        for col_header in self._headers:
            assert(col_header in record)
            row.append(str(record[col_header]))
        self._rows.append(row)
    
    def validate_file(self, test: unittest.TestCase, filepath):
        test.assertTrue(os.path.exists(filepath))
        with open(filepath) as f:
            csv_rows = list(csv.reader(f, delimiter='\t'))
            test.assertListEqual(self._rows, csv_rows)

class FakeRegime:
    def __init__(self, block_num, block_type, regime_num,
                 task_num, exp_count, params):
        self._block_num = block_num
        self._block_type = block_type
        self._regime_num = regime_num
        self._task_num = task_num
        self._exp_count = exp_count
        self._params = params
        # assumed format
        self._block_name = f'{block_num}-{block_type}'
        self._task_name = f'task{task_num}'
    
    def _to_debug_string(self):
        return f'{self._block_name}, regime {self._regime_num}: '\
               f'{self._exp_count} exps of {self._task_name}'
class FakeExp:
    def __init__(self, regime: FakeRegime, exp_num, extra_cols):
        self._regime = regime
        self._exp_num = exp_num
        self._extra_cols = extra_cols
    
    def get_regime_record(self, worker_num):
        worker = f'worker{worker_num}'
        record = {
            'block_num': self._regime._block_num,
            'regime_num': self._regime._regime_num,
            'block_type': self._regime._block_type,
            'worker': worker,
            'task_name': self._regime._task_name,
            'params': self._regime._params
        }
        return record
    
    def get_data_record(self):
        record = {
            'block_num': self._regime._block_num,
            'regime_num': self._regime._regime_num,
            'exp_num': self._exp_num,
            'status': 'Done',
            'timestamp': l2logger.PerformanceLogger.get_readable_timestamp()
        }
        record.update(self._extra_cols)
        return record

class FakeApplication:
    def __init__(self, logger_base, scenario_name='fake_scenario',
                train_test_cycles=1, workers=1, tasks=1,
                regimes_per_task=1, exp_per_regime=1,
                extra_cols={}):
        self._logger_base = logger_base
        self._scenario_name = scenario_name
        self._train_test_cycles = train_test_cycles
        self._workers = workers
        self._tasks = tasks
        self._regimes_per_task = regimes_per_task
        self._exp_per_regime = exp_per_regime
        self._extra_cols = extra_cols
        # Custom for this fake app
        self._init_regimes()
        self._init_exps()
        self._data_row_headers = []
        self._regime_row_headers = []
        self._expected_logs = {}

    def _init_regimes(self):
        self._regimes = []
        regime_num = -1
        params = json.dumps({'param_int': 20, 'param_str': 'ok', 'param_list': [2, 3, 1]})
        for block_num in range(0, 2 * self._train_test_cycles):
            # alternate between training and testing
            block_type = 'test' if block_num % 2 else 'train'
            # alternate tasks within a block
            for _ in range(0, self._regimes_per_task):
                for task_num in range(0, self._tasks):
                    regime_num += 1
                    self._regimes.append(FakeRegime(block_num, block_type, regime_num,
                                              task_num, self._exp_per_regime, params))
    def _init_exps(self):
        self._exp_queue = deque()
        exp_num = -1
        for regime in self._regimes:
            for _ in range(0, regime._exp_count):
                exp_num += 1
                self._exp_queue.append(FakeExp(regime, exp_num, self._extra_cols))
    
    def consume_experiences(self):
        total_exp = len(self._exp_queue)
        worker_str = 'workers' if self._workers > 1 else 'worker'
        print(f'\tConsuming {total_exp} experiences with '\
              f'{self._workers} {worker_str}')
        # lazy initialization of row headers; needs to be init'd 
        # in this function, can't be ahead of time
        assert(not(len(self._data_row_headers)))
        assert(not(len(self._regime_row_headers)))
        # copies of logger to imitate workers in different memory spaces
        loggers = [deepcopy(self._logger_base) for _ in range(0, self._workers)]
        last_regimes = {logger: -1 for logger in loggers}
        while len(self._exp_queue):
            exp = self._exp_queue.popleft()
            if not(exp._exp_num % 10000):
                print(f'\t\tprocessing exp {exp._exp_num}/{total_exp}...')
            worker_num = exp._exp_num % len(loggers)
            logger = loggers[worker_num]
            if exp._regime._regime_num != last_regimes[logger]:
                last_regimes[logger] = exp._regime._regime_num
                # write new regime
                regime_record = exp.get_regime_record(worker_num)
                logger.write_new_regime(regime_record, self._scenario_name)
                self.init_header_if_needed(regime_record, DEFAULT_REGIME_ROWS,
                                           self._regime_row_headers)
                self.init_log_if_needed(exp._regime, regime_record)
                
            data_record = exp.get_data_record()
            logger.write_to_data_log(data_record)
            self.init_header_if_needed(data_record, DEFAULT_DATA_ROWS,
                                        self._data_row_headers)
            worker = f'worker{worker_num}'
            block = exp._regime._block_name
            task = exp._regime._task_name
            data_log = self._expected_logs[worker][block][task][DATA_FILENAME]
            data_log.add_row(data_record, self._data_row_headers)
        print('\t\tdone processing all experiences!')
        for logger in loggers:
            logger.close_logs()
    
    def init_log_if_needed(self, regime, regime_record):
        worker = regime_record['worker']
        block = regime._block_name
        task = regime_record['task_name']

        worker_entry = self._expected_logs.setdefault(worker, {})
        block_entry = worker_entry.setdefault(block, {})
        task_entry = block_entry.setdefault(task, {})
        regime_log = task_entry.setdefault(REGIME_FILENAME, FakeExpectedLog())
        task_entry.setdefault(DATA_FILENAME, FakeExpectedLog())

        regime_log.add_row(regime_record, self._regime_row_headers)

    def init_header_if_needed(self, record, default_headers, attribute):
        if not(len(attribute)):
            attribute.extend(self.order_header(record, default_headers))
    
    def order_header(self, record, default_headers):
        record_headers = list(record.keys())
        record_set = set(record_headers)
        default_set = set(default_headers)
        assert(record_set.issuperset(default_set))
        # as a list, make sure to copy since global whoops
        ordered_headers = deepcopy(default_headers)
        ordered_headers.extend(list(record_set - default_set))
        return ordered_headers

    def validate_logs(self, test_case: unittest.TestCase, logging_dir):
        print('\tValidating logger output')
        scenario_dir = os.path.join(logging_dir, self._scenario_name)
        file_paths = []
        dir_paths = []
        for (dirpath, dirs, files) in os.walk(scenario_dir, topdown=True):
            for d in dirs:
                dir_paths.append(os.path.join(dirpath, d))
            for f in files:
                file_paths.append(os.path.join(dirpath, f))

        expected_dir_paths = []
        expected_files = {}
        expected_files[os.path.join(scenario_dir, 'column_info.json')] = None 
        expected_files[os.path.join(scenario_dir, 'scenario_info.json')] = None

        for worker_dir, block_dirs in self._expected_logs.items():
            worker_path = os.path.join(scenario_dir, worker_dir)
            expected_dir_paths.append(worker_path)
            for block_dir, task_dirs in block_dirs.items():
                block_path = os.path.join(worker_path, block_dir)
                expected_dir_paths.append(block_path)
                for task_dir, log_files in task_dirs.items():
                    task_path = os.path.join(block_path, task_dir)
                    expected_dir_paths.append(task_path)
                    for log_file, expected_log in log_files.items():
                        log_path = os.path.join(task_path, log_file)
                        expected_files[log_path] = expected_log

        # ensures all the files match as expected 1:1, with no excess or missing
        test_case.assertCountEqual(expected_dir_paths, dir_paths)
        test_case.assertCountEqual(expected_files.keys(), file_paths)
        for file_path in file_paths:
            expected_log = expected_files[file_path]
            # TODO: check contents of column_info.json and scenario_info.json as well?
            # there's already a test-case for that though
            if expected_log is None:
                continue
            # at this point, we know that it's a FakeExpectedLog object
            expected_log.validate_file(test_case, file_path)
        print(f'\t\tall {len(dir_paths)} directories were correctly created/structured')
        print(f'\t\tall {len(file_paths) - 2} log files have correct content')