# Demonstrates simple usage of the logging API
import json
import time
import os
from l2logger import l2logger

from mock_agent import MockAgent, SequenceNums

SCENARIO_DIR = "simple"
SCENARIO_INFO = {
    "author": "JHU APL",
    "complexity": "1-low",
    "difficulty": "2-medium",
    "scenario_type": "custom",
}
LOGGER_INFO = {"metrics_columns": ["reward"], "log_format_version": "1.0"}


def log_data(data_logger, exp, results, status="complete"):
    seq = exp.sequence_nums
    worker = f"{os.path.basename(__file__)}_0"
    record = {
        "block_num": seq.block_num,
        "block_type": exp.block_type,
        "task_params": exp.params,
        "task_name": exp.task_name,
        "exp_num": seq.exp_num,
        "exp_status": status,
        "worker_id": worker,
    }

    record.update(results)
    data_logger.log_record(record)


def run_scenario(agent, data_logger):
    last_seq = SequenceNums(-1, -1)
    while not agent.complete():
        exp = agent.next_experience()
        cur_seq = exp.sequence_nums
        # check for new block
        if last_seq.block_num != cur_seq.block_num:
            print("new block:", cur_seq.block_num)
        results = exp.run()
        log_data(data_logger, exp, results)

        last_seq = cur_seq


if __name__ == "__main__":
    with open("simple_scenario.json") as f:
        data = json.load(f)
    agent = MockAgent(data["scenario"])
    SCENARIO_INFO["input_file"] = data
    data_logger = l2logger.DataLogger(
        data["logging_base_dir"], SCENARIO_DIR, LOGGER_INFO, SCENARIO_INFO
    )
    run_scenario(agent, data_logger)
