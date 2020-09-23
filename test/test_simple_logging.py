import os
import unittest
import tempfile
import importlib
import json

# if importlib.util.find_spec('pandas'):
#     import pandas as pd

from l2logger import l2logger
from test_utils import FakeApplication


#@unittest.skipUnless(importlib.util.find_spec('pandas'), 'Requires pandas library')
class TestSimpleScenarios(unittest.TestCase):

    def test_one_block(self):
        print('\ntest_one_block')
        # TODO: reduce code re-use here
        with tempfile.TemporaryDirectory() as logging_dir:
            logger = l2logger.RLPerformanceLogger(logging_dir)
            extra_cols = {'reward': 1.5, 'rand_seed': 'September 2020'}
            app = FakeApplication(logger, train_test_cycles=1,
                                  tasks=1, regimes_per_task=1,
                                  exp_per_regime=100, extra_cols=extra_cols)
            app.consume_experiences()
            # TODO: validate logger output

    def test_meta_files_default(self):
        print('\ntest_meta_files_default')
        self.meta_files_helper(None, None, {'metrics_columns': []}, {})


    def test_meta_files(self):
        print('\ntest_meta_files')
        # make sure order is retained
        cols = {'metrics_columns': ['temp1', 'reward', 'temp2']}
        info = {
            'author': 'JHU APL',
            'list_test': [1, 2, 4, 3],
            'dict': {
                'nested_dict': {'a': 2, 'field': False},
                'nested_list': [[1, 2], [2, 3], [3, 1]]
            }
        }
        self.meta_files_helper(cols, info, cols, info)
        
    def meta_files_helper(self, cols, info, expected_cols, expected_info):
        print('\tmeta_files_helper')
        with tempfile.TemporaryDirectory() as logging_dir:
            logger = l2logger.RLPerformanceLogger(logging_dir, cols, info)
            self.assertEqual(logger.toplevel_dir, logging_dir)
            scenario = 'unit_test_meta'
            # create directory structure; should also create meta info files
            _ = self.create_and_validate_structure(logger, scenario, 1, 1, 1)
            col_path = os.path.join(logging_dir, scenario, 'column_info.json')
            info_path = os.path.join(logging_dir, scenario, 'scenario_info.json')
            self.assertTrue(os.path.exists(col_path))
            self.assertTrue(os.path.exists(info_path))
            with open(col_path) as f:
                data = json.load(f)
                self.assertDictEqual(data, expected_cols)
            with open(info_path) as f:
                data = json.load(f)
                self.assertDictEqual(data, expected_info)
            print('\tmeta files (column_info.json and scenario_info.json) correct')

    def test_single_directory(self):
        print('\ntest_single_directory')
        with tempfile.TemporaryDirectory() as logging_dir:
            logger = l2logger.RLPerformanceLogger(
                logging_dir
            )
            self.assertEqual(logger.toplevel_dir, logging_dir)
            _ = self.create_and_validate_structure(
                logger=logger, scenario_name='unit_scenario',
                num_workers=1, num_blocks=1, num_tasks=1
            )

    def test_stress_directory(self):
        print('\ntest_stress_directory')
        with tempfile.TemporaryDirectory() as logging_dir:
            logger = l2logger.RLPerformanceLogger(
                logging_dir
            )
            self.assertEqual(logger.toplevel_dir, logging_dir)
            _ = self.create_and_validate_structure(
                logger=logger, scenario_name='unit_scenario',
                num_workers=17, num_blocks=23, num_tasks=19
            )


    # tests creating directory structure via the "update_context_only" flag
    # only checks the directories; does NOT examine log or meta-data files
    def create_and_validate_structure(self, logger, scenario_name, num_workers, num_blocks, num_tasks):
        print('\tcreate_and_validate_structure')
        contexts=[]
        for w in range(0, num_workers):
            worker = f'worker{w}'
            for b in range(0, num_blocks):
                block_type = 'test' if b % 2 else 'train'
                block =f'{b}-{block_type}'
                for t in range(0, num_tasks):
                    task=f'task{t}'
                    contexts.append((worker, block, task))
        expected_dirs = set('.')
        for worker_name, block_name, task_name in contexts:
            cur_path = worker_name
            expected_dirs.add(cur_path)
            cur_path = os.path.join(cur_path, block_name)
            expected_dirs.add(cur_path)
            cur_path = os.path.join(cur_path, task_name)
            expected_dirs.add(cur_path)

            block_num, block_type = block_name.split('-')
            block_num = int(block_num)
            record = {
                'worker': worker_name,
                'task_name': task_name,
                'block_num': block_num,
                'block_type': block_type
            }
            logger.write_new_regime(record, scenario_name, True)
        scenario_dir = os.path.join(logger.toplevel_dir, scenario_name)
        dirs = TestSimpleScenarios.walk_directory_tree_relative(scenario_dir)
        expected_num = 1 + num_workers + num_workers*num_blocks + num_workers*num_blocks*num_tasks
        # sanity check first
        self.assertEqual(expected_num, len(expected_dirs))
        self.assertEqual(expected_num, len(dirs))
        # ignore list order; check if contents are the same ignoring order
        self.assertCountEqual(expected_dirs, dirs)
        print(f'\t{expected_num} dirs created correctly')
        return contexts

    # Adapted from learnkit/utils.py
    @classmethod
    def walk_directory_tree_relative(cls, dirname):
        found_dirs = []
        for (dirpath, _, _) in os.walk(dirname, topdown=True):
            relative_path = os.path.relpath(dirpath, dirname)
            found_dirs.append(relative_path)
        return found_dirs

if __name__ == "__main__":
    unittest.main()