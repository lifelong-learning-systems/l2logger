# (c) 2019 The Johns Hopkins University Applied Physics Laboratory LLC (JHU/APL).
# All Rights Reserved. This material may be only be used, modified, or reproduced
# by or for the U.S. Government pursuant to the license rights granted under the
# clauses at DFARS 252.227-7013/7014 or FAR 52.227-14. For any other permission,
# please contact the Office of Technology Transfer at JHU/APL.

# NO WARRANTY, NO LIABILITY. THIS MATERIAL IS PROVIDED "AS IS." JHU/APL MAKES NO
# REPRESENTATION OR WARRANTY WITH RESPECT TO THE PERFORMANCE OF THE MATERIALS,
# INCLUDING THEIR SAFETY, EFFECTIVENESS, OR COMMERCIAL VIABILITY, AND DISCLAIMS
# ALL WARRANTIES IN THE MATERIAL, WHETHER EXPRESS OR IMPLIED, INCLUDING (BUT NOT
# LIMITED TO) ANY AND ALL IMPLIED WARRANTIES OF PERFORMANCE, MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT OF INTELLECTUAL PROPERTY
# OR OTHER THIRD PARTY RIGHTS. ANY USER OF THE MATERIAL ASSUMES THE ENTIRE RISK
# AND LIABILITY FOR USING THE MATERIAL. IN NO EVENT SHALL JHU/APL BE LIABLE TO ANY
# USER OF THE MATERIAL FOR ANY ACTUAL, INDIRECT, CONSEQUENTIAL, SPECIAL OR OTHER
# DAMAGES ARISING FROM THE USE OF, OR INABILITY TO USE, THE MATERIAL, INCLUDING,
# BUT NOT LIMITED TO, ANY DAMAGES FOR LOST PROFITS.

import os
import re
from functools import partial
import csv
import time
import json
from datetime import datetime

def get_log_foldername(path, format_str="{scenario}-{timestamp}"):
    scenario_name = os.path.basename(os.path.basename(path)).split('.')[0]
    # int(round(time.time() * 1000))
    timestamp = re.sub('[.]', '-', str(time.time()))
    return format_str.format(scenario=scenario_name, timestamp=timestamp)


class TSVLogFile():
    def __init__(self, log_file_name, fieldnames):
        self._log_file_name = log_file_name
        self._initialized = False
        # actual file handle, result of calling open
        self._tsv_log_file = None
        # csv DictWriter object
        self._tsv_log = None
        # ordered list of fieldnames
        self._fieldnames = fieldnames

    def _initialize(self):
        if os.path.exists(self._log_file_name):
            mode, write_header = "a", False
        else:
            mode, write_header = "w", True
        self._tsv_log_file = open(self._log_file_name, mode)
        self._tsv_log = csv.DictWriter(self._tsv_log_file, fieldnames=self._fieldnames,
                                       delimiter='\t', quotechar='"', lineterminator='\n')
        if write_header:
            self._tsv_log.writeheader()
        self._initialized = True
    
    def __del__(self, *args):
        self.close()

    # validation handled in caller
    def add_row(self, record):
        if not self._initialized:
            self._initialize()
        self._tsv_log.writerow(record)
        self._tsv_log_file.flush()

    def close(self):
        if self._tsv_log_file and not self._tsv_log_file.closed:
            self._tsv_log_file.close()
            self._initialized = False

class DataLogger():
    def __init__(self, toplevel_dir, scenario_name, column_info=None, scenario_info=None):
        self._standard_fields = [
            'block_num', 'exp_num', 'worker_id', 'block_type', 'task_name', 
            'task_params', 'exp_status', 'timestamp'
        ]
        self._toplevel_dir = toplevel_dir
        # should be toplevel/scenario-TIMESTAMP
        self._scenario_dir = os.path.join(self._toplevel_dir, get_log_foldername(scenario_name))
        col_key = 'metrics_columns'
        self._column_info = column_info or {col_key: []}
        if not col_key in self._column_info:
            raise RuntimeError(f'column_info missing required key \'{col_key}\'')
        self._metric_fields = self._column_info[col_key]
        if not type(self._metric_fields) is list or any(type(s) is not str for s in self._metric_fields):
            raise RuntimeError(f'column_info[\'{col_key}\'] must be a list of strings')

        self._scenario_info = scenario_info or {}
        self.write_info_files()

        self._tsv_logger = None
        self._logging_dir = None
        # state for validation
        self._all_fields_ordered = None
        self._last_exp_num = None
        self._last_block_num = None
        self._default_exp_status = 'complete'
        self._default_worker_id = 'worker-default'
        self._block_types = ['train', 'test']
        self._exp_statuses = ['complete', 'incomplete']
        self._worker_pattern = re.compile(r'[0-9a-zA-Z_\-.]+')

    @property
    def scenario_dir(self):
        return self._scenario_dir
    
    @property
    def column_info(self):
        return self._column_info
    
    @property
    def scenario_info(self):
        return self._scenario_info

    def write_info_files(self):
        os.makedirs(self._scenario_dir, exist_ok=True)
        column_info_path = os.path.join(self._scenario_dir, 'column_info.json')
        scenario_info_path = os.path.join(self._scenario_dir, 'scenario_info.json')
        with open(column_info_path, 'w+') as column_file:
            column_file.write(json.dumps(self._column_info, indent=2))
        with open(scenario_info_path, 'w+') as scenario_file:
            scenario_file.write(json.dumps(self._scenario_info, indent=2))


    def log_record(self, record_in):
        record = self._augment_fields(record_in)
        self._validate_record(record)
        self._update_state(record)

        record['task_params'] = json.dumps(record['task_params'])
        self._tsv_logger.add_row(record)
    
    def close(self):
        if self._tsv_logger:
            self._tsv_logger.close()

    # ensure all record fields are valid
    def _validate_record(self, record):
        self._validate_fields(record)
        self._validate_block_type(record['block_type'])
        self._validate_exp_status(record['exp_status'])
        self._validate_worker_id(record['worker_id'])
        self._validate_task_params(record['task_params'])
        self._validate_block_num(record['block_num'])
        self._validate_exp_num(record['exp_num'])

    # adds any automated fields to record (i.e. timestamp)
    def _augment_fields(self, record):
        if not type(record) is dict:
            raise RuntimeError('record must be dict')
        new_record = record.copy()
        if 'timestamp' in new_record:
            raise RuntimeError('timestamp column cannot be overwritten')
        else:
            new_record['timestamp'] = datetime.now().strftime('%Y%m%dT%H%M%S.%f')
        if not 'exp_status' in new_record:
            new_record['exp_status'] = self._default_exp_status
        if not 'worker_id' in new_record:
            new_record['worker_id'] = self._default_worker_id
        return new_record

    def _update_state(self, record):
        if not self._all_fields_ordered:
            self._init_fields(record)
        self._last_block_num = record['block_num']
        self._last_exp_num = record['exp_num']

        old_logging_dir = self._logging_dir
        self._logging_dir = os.path.join(self._scenario_dir, record['worker_id'], str(record['block_num']))
        if old_logging_dir != self._logging_dir:
            os.makedirs(self._logging_dir, exist_ok=True)
            if self._tsv_logger:
                self._tsv_logger.close()
            log_file_name = os.path.join(self._logging_dir, 'data-log.tsv')
            self._tsv_logger = TSVLogFile(log_file_name, self._all_fields_ordered)
        
    def _init_fields(self, record):
        standard_set = set(self._standard_fields)
        record_set = set(record.keys())
        extra_fields = list(record_set - standard_set)
        extra_fields.sort()
        self._all_fields_ordered = self._standard_fields.copy()
        self._all_fields_ordered.extend(extra_fields)

    def _validate_fields(self, record):
        if not self._all_fields_ordered:
            standard_set = set(self._standard_fields)
            metric_set = set(self._metric_fields)
            record_set = set(record.keys())
            if not record_set.issuperset(standard_set):
                raise RuntimeError(f'standard record fields missing: expected at least ' \
                                f'{standard_set}, got {record_set}')
            if not record_set.issuperset(metric_set):
                raise RuntimeError(f'metric record fields missing: expected at least ' \
                                f'{metric_set}, got {record_set}')
        elif set(self._all_fields_ordered) != set(record.keys()):
            raise RuntimeError(f'record field mismatch: expected ' \
                               f'{set(self._all_fields_ordered)}, got ' \
                               f'{set(record.keys())}')

    def _validate_block_num(self, block_num):
        if (not type(block_num) is int) or block_num < 0:
            raise RuntimeError(f'block_num must be non-negative integer')
        elif (not self._last_block_num is None) and block_num < self._last_block_num:
            raise RuntimeError('block_num must be non-decreasing')

    def _validate_exp_num(self, exp_num):
        if (not type(exp_num) is int) or exp_num < 0:
            raise RuntimeError(f'exp_num must be non-negative integer')
        elif (not self._last_exp_num is None) and exp_num < self._last_exp_num:
            raise RuntimeError('exp_num must be non-decreasing')
    
    def _validate_block_type(self, block_type):
        if not block_type in self._block_types:
            raise RuntimeError(f'block_type must be one of {self._block_types}')
    
    def _validate_exp_status(self, exp_status):
        if not exp_status in self._exp_statuses:
            raise RuntimeError(f'exp_status must be one of {self._exp_statuses}')
    
    def _validate_worker_id(self, worker_id):
        if re.fullmatch(self._worker_pattern, worker_id) is None:
            raise RuntimeError(f'worker_id can only contain alphanumeric characters, hyphens, dashes, or periods')
    
    def _validate_task_params(self, task_params):
        if type(task_params) is not dict:
            raise RuntimeError('task_params must be dict')
        try:
            json.dumps(task_params)
        except:
            raise RuntimeError('task_params must be valid json')
