# Multithreaded, call logger functions, etc.
import os
import sys
import json
import time
import shutil
import parallel_helper
from parallel_helper import LoggerInfo, RegimeInfo
import multiprocessing
from multiprocessing import Process, Value, Lock, Queue
from l2logger import l2logger

class Task:
    def __init__(self, logger_info, regime_info):
        self._logger_info = logger_info
        self._regime_info = regime_info

    def run(self, exp_num, worker_index):
        name = f'{self._regime_info.to_string()}, exp_num {exp_num}'\
              f'(worker-{worker_index})'
        print(f'{name} starting...')
        time.sleep(0.01)
        self._logger_info.write_data(self._regime_info, exp_num)
        print(f'{name} Done!')

def regime_worker(logger_info, regime_info, exp_num_queue, worker_index):
    logger_info.write_regime(regime_info, worker_index)
    while True:
        try:
            exp_num = exp_num_queue.get(block=True, timeout=0.1)
        except:
            # try again, basically elongating timeout
            if not exp_num_queue.empty():
                continue
            else:
                break
        task = Task(logger_info, regime_info)
        task.run(exp_num, worker_index)
        
def spawn_workers(logger_info, regime_info, exp_num_queue):
    # all args get copied except for exp_num_queue, which remains shared
    workers = [Process(target=regime_worker,
                       args=(logger_info, regime_info, exp_num_queue, i,) )
               for i in range(0, logger_info.workers)]
    # start up workers
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    
    #print(f'Block {block_num} Regime {regime_num}: Done!')

def start(logger_info):
    regime_num = 0
    exp_num_queue = Queue()
    regime_exp_start = 0
    for block_num, block in enumerate(logger_info.data['blocks']):
        block_type = block['type']
        #print(f'Starting block {block_num} with type: {block_type}'):
        # increment regime globally across blocks
        for regime in block['regimes']:
            n = regime['length']
            for i in range(0, n):
                exp_num_queue.put(i + regime_exp_start)
            regime_exp_start += n
            regime_info = RegimeInfo(block_num, block_type, regime_num, regime)
            spawn_workers(logger_info, regime_info, exp_num_queue)

            regime_num += 1


if __name__ == '__main__':
    multiprocessing.set_start_method('fork')
    if len(sys.argv) != 2:
        print('Missing argument!')
        print(f'Usage: python {sys.argv[0]} <json_input_file>')
        sys.exit(1)
    input_file_name = sys.argv[1]

    logger_info = LoggerInfo(input_file_name)
    start(logger_info)
