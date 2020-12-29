# (c) 2019 The Johns Hopkins University Applied Physics Laboratory LLC (JHU/APL).
# All Rights Reserved. This material may be only be used, modified, or reproduced
# by or for the U.S. Government pursuant to the license rights granted under the
# clauses at DFARS 252.227-7013/7014 or FAR 52.227-14. For any other permission,
# please contact the Office of Technology Transfer at JHU/APL.

# NO WARRANTY, NO LIABILITY. THIS MATERIAL IS PROVIDED “AS IS.” JHU/APL MAKES NO
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
import tempfile
import unittest

from l2logger import l2logger


class TestSimpleScenarios(unittest.TestCase):
    def testErrorInit(self):
        with tempfile.TemporaryDirectory() as base_dir:
            self.helperErrorInit(base_dir, 'test_scenario', True)
            self.helperErrorInit(base_dir, 'test_scenario', {'metrics_columns': {}})
            self.helperErrorInit(base_dir, 'test_scenario', {'metrics_columns': ['test', 1]})
            self.helperErrorInit(base_dir, 'test_scenario', {'metrics_columns': []})
            self.helperErrorInit(base_dir, 'test_scenario', ['metrics_columns'])
            self.helperErrorInit(base_dir, 'test_scenario', {'col1': {}})
    
    def helperErrorInit(self, top_dir, scenario, logger_info=None, scenario_info=None):
        self.assertRaises(Exception, l2logger.DataLogger,
            top_dir, scenario, logger_info, scenario_info)

    def testValidRecord(self):
        with tempfile.TemporaryDirectory() as base_dir:
            metric_cols = ['reward']
            valid_standard = {
                'block_num': 4, 'exp_num': 4, 'worker_id': 'worker0',
                'block_type': 'train', 'task_name': 'taskA',
                'task_params': {'param1': 1}, 'exp_status': 'complete'
            }
            valid_metrics = {'reward': 123}
            valid_full = valid_standard.copy()
            valid_full.update(valid_metrics.copy())
            validHelper = lambda records: self.helperValidRecord(base_dir, metric_cols, records)

            validHelper([valid_full])
            validHelper([valid_full, valid_full])
            validHelper([valid_full, self.helperUpdate(valid_full, {'exp_num': 20})])
            validHelper([valid_full, self.helperUpdate(valid_full, {'block_num': 10})])
            validHelper([self.helperUpdate(valid_full, {'exp_status': 'incomplete'})])
            validHelper([self.helperUpdate(valid_full, {'block_type': 'test'})])

    def testErrorRecord(self):
        with tempfile.TemporaryDirectory() as base_dir:
            metric_cols = ['reward2', 'reward1', 'reward1']
            valid_standard = {
                'block_num': 4, 'exp_num': 4, 'worker_id': 'worker0',
                'block_type': 'train', 'task_name': 'taskA',
                'task_params': {'param1': 1}, 'exp_status': 'complete'
            }
            valid_metrics = {'reward1': 123, 'reward2': 456}
            valid_full = valid_standard.copy()
            valid_full.update(valid_metrics.copy())

            errHelper = lambda records: self.helperErrorRecord(base_dir, metric_cols, records)
            # missing cols
            errHelper([valid_standard])
            errHelper([valid_metrics])
            errHelper([{}])
            errHelper([['not even a dict']])
            # timestamp overwriting
            errHelper([self.helperUpdate(valid_full, {'timestamp': 2})])
            # increasing and decreasing col count
            errHelper([valid_full, self.helperUpdate(valid_full, {'extra': 2})])
            errHelper([self.helperUpdate(valid_full, {'extra': 2}), valid_full])
            # invalid block_nums: string, then negative, then decreasing
            errHelper([self.helperUpdate(valid_full, {'block_num': 'temp'})])
            errHelper([self.helperUpdate(valid_full, {'block_num': -1})])
            errHelper([valid_full, self.helperUpdate(valid_full, {'block_num': 2})])
            # invalid exp_nums: string, then negative, then decreasing
            errHelper([self.helperUpdate(valid_full, {'exp_num': 'temp'})])
            errHelper([self.helperUpdate(valid_full, {'exp_num': -1})])
            errHelper([valid_full, self.helperUpdate(valid_full, {'exp_num': 3})])
            # invalid block_type
            errHelper([self.helperUpdate(valid_full, {'block_type': 'temp'})])
            # invalid exp_status
            errHelper([self.helperUpdate(valid_full, {'exp_status': 'Done'})])
            # invalid worker_id
            errHelper([self.helperUpdate(valid_full, {'worker_id': 'a+b'})])
            # invalid task_params
            errHelper([self.helperUpdate(valid_full, {'task_params': True})])
            errHelper([self.helperUpdate(valid_full, {'task_params': {'temp': os}})])

    def helperErrorRecord(self, top_dir, cols, records):
        logger = l2logger.DataLogger(top_dir, 'test', {'metrics_columns': cols})
        temp_func = lambda logger, records: [logger.log_record(r) for r in records]
        self.assertRaises(RuntimeError, temp_func, logger, records)
        #temp_func(logger, records)
    
    def helperValidRecord(self, top_dir, cols, records):
        logger = l2logger.DataLogger(top_dir, 'test', {'metrics_columns': cols})
        temp_func = lambda logger, records: [logger.log_record(r) for r in records]
        try:
            temp_func(logger, records)
        except RuntimeError:
            self.fail('Record failed validity checks in log_record')
    
    def helperUpdate(self, record, fields):
        new_record = record.copy()
        new_record.update(fields)
        return new_record

if __name__ == "__main__":
    unittest.main()
