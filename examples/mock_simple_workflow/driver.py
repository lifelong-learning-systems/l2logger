# Demonstrates simple usage of the logging API
import json
import time
import os
from l2logger import l2logger 

from mock_agent import MockAgent, SequenceNums

time_str = str(time.time()).replace('.', '-')
SCENARIO_DIR = f'simple-{time_str}'
SCENARIO_INFO = {
    'author': 'JHU APL'
}
METRIC_COLUMNS = ['reward']

def log_block(performance_logger, exp):
    seq = exp.sequence_nums
    block_type = exp.block_type
    worker = f'{os.path.basename(__file__)}-0'
    directory_info = {
        'scenario_dirname': SCENARIO_DIR,
        'worker_dirname': worker,
        'block_dirname': f'{seq.block_num}-{block_type}'
    }
    record = {
        'block_num': seq.block_num,
        'regime_num': seq.regime_num,
        'block_type': block_type,
        'worker': worker,
        'task_name': exp.task_name,
        'params': exp.param_string
    }
    performance_logger.write_to_blocks_log(record, directory_info)

def log_data(performance_logger, exp, results, status='Done'):
    seq = exp.sequence_nums
    record = {
        'block_num': seq.block_num,
        'regime_num': seq.regime_num,
        'exp_num': seq.exp_num,
        'status': status,
        'timestamp': l2logger.PerformanceLogger.get_readable_timestamp()
    }
    record.update(results)
    performance_logger.write_to_data_log(record)


def run_scenario(agent, performance_logger):
    last_seq = SequenceNums(-1, -1, -1)
    while not agent.complete():
        exp = agent.next_experience()
        cur_seq = exp.sequence_nums
        # check for new block
        if last_seq.block_num != cur_seq.block_num:
            print("new block:", cur_seq.block_num)
        # check for new regime
        if last_seq.regime_num != cur_seq.regime_num:
            print("new regime:", cur_seq.regime_num)
            log_block(performance_logger, exp)

        print("consuming experience:", cur_seq.exp_num)
        results = exp.run()
        log_data(performance_logger, exp, results)

        last_seq = cur_seq

if __name__ == "__main__":
    with open('simple_scenario.json') as f:
        data = json.load(f)
    agent = MockAgent(data['scenario']) 
    performance_logger = l2logger.RLPerformanceLogger(
        data['logging_base_dir'], METRIC_COLUMNS, SCENARIO_INFO)
    run_scenario(agent, performance_logger)
