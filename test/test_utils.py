import json
from collections import deque
from l2logger import l2logger
from copy import deepcopy

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
        self._block_name = f'block{block_num}-{block_type}'
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
    
    def get_data_record(self, worker_num):
        record = {
            'block_num': self._regime._block_num,
            'regime_num': self._regime._regime_num,
            'exp_num': self._exp_num,
            'status': 'Done'
        }
        record.update(self._extra_cols)
        return record

class FakeApplication:
    def __init__(self, logger_base, scenario_name='fake_scenario',
                train_test_cycles=1, workers=1, tasks=1,
                regimes_per_task=1, exp_per_regime=1, extra_cols={}):
        self._logger_base = logger_base
        self._scenario_name = scenario_name
        self._train_test_cycles = train_test_cycles
        self._workers = workers
        self._tasks = tasks
        self._regimes_per_task = regimes_per_task
        self._exp_per_regime = exp_per_regime
        self._extra_cols = extra_cols
        self._init_regimes()
        self._init_exps()

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
        # copies of logger to imitate workers in different memory spaces
        loggers = [deepcopy(self._logger_base) for _ in range(0, self._workers)]
        last_regimes = {logger: -1 for logger in loggers}
        while len(self._exp_queue):
            exp = self._exp_queue.popleft()
            worker_num = exp._exp_num % len(loggers)
            logger = loggers[worker_num]
            if exp._regime._regime_num != last_regimes[logger]:
                last_regimes[logger] = exp._regime._regime_num
                # write new regime
                regime_record = exp.get_regime_record(worker_num)
                logger.write_new_regime(regime_record, self._scenario_name)
            data_record = exp.get_data_record(worker_num)
            logger.write_to_data_log(data_record)
        for logger in loggers:
            logger.close_logs()
        