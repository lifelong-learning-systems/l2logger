import os
import unittest
import tempfile
from unittest.mock import patch
import pprint
import importlib

import learnkit
from learnkit.utils import module_relative_file
from .utils import *

if importlib.util.find_spec('pandas'):
    import pandas as pd

# TODO: Remove learnkit dependencies

class TestClassifTaskLoggingDisable(unittest.TestCase):

    def test_episode_sequence_default_logging(self):
        print("\ntest_episode_sequence_default_logging")
        self._process_syllabus(logging_val=None)

    def test_episode_sequence_no_logging(self):
        print("\ntest_episode_sequence_no_logging")        
        self._process_syllabus(logging_val=False)

    def _process_syllabus(self, logging_val):
        # check that the default value (logging_val == None indicates use default)
        # and explicit disabling (logging_val == False) both result in no logs
        tempdir = tempfile.TemporaryDirectory(prefix="learnkit_test_")
        with patch.dict('os.environ', {'L2DATA': tempdir.name}):
            classroom = learnkit.Classroom()
            syllabus_file = module_relative_file(__file__, 'syllabi/datasyllabus-w-phases')
            _ = run_data_syllabus(classroom, syllabus_file, logging=logging_val)
            classroom.close()
        found_dirs = walk_directory_tree(tempdir.name)
        self.assertListEqual(found_dirs['logs'], [])



class TestClassifTaskLoggingPhases(unittest.TestCase):

    def test_log_directory_structure(self):
        print("\ntest_log_directory_structure")
        tempdir = tempfile.TemporaryDirectory(prefix="learnkit_test_")
        with patch.dict('os.environ', {'L2DATA': tempdir.name}):
            classroom = learnkit.Classroom()
            syllabus_file = module_relative_file(__file__, 'syllabi/datasyllabus-w-phases')
            (full_results, syllabus_log_dir) = run_data_syllabus(classroom, syllabus_file, logging=True)
            classroom.close()

        results = dict_list_to_tuple_list(full_results, 
                ["task_name", "num_batches", "batch_sizes", "block", "phase_name", "enable_updates"])

        # check the sequence of datasets that were generated
        expected_results = [
            #  task_name                num_batches  batch_sizes   block phase  enable_updates
            ('learnkit.sample_classification_tasks.NumberData', 8, 8*[50],        0, "1.train", True),
            ('learnkit.sample_classification_tasks.NumberData', 6, 5*[75] + [25], 1, "1.train", True),

            ('learnkit.sample_classification_tasks.NumberData', 40, 40*[10],      2, "1.test", False),
            ('learnkit.sample_classification_tasks.NumberData2', 40, 40*[10],     3, "1.test", False),

            ('learnkit.sample_classification_tasks.NumberData2', 4, 4*[100],         4, "2.train", True),
            ('learnkit.sample_classification_tasks.NumberData2', 3, 2*[150] + [100], 5, "2.train", True),

            ('learnkit.sample_classification_tasks.NumberData', 40, 40*[10],      6, "2.test", False),
            ('learnkit.sample_classification_tasks.NumberData2', 40, 40*[10],     7, "2.test", False)
        ]

        self.assertSequenceEqual(results, expected_results)

        # check the log directories that were generated
        found_dirs = walk_directory_tree(syllabus_log_dir)

        expected_dirs = {
            'worker-primary':  ['1-1_train', 
                                '2-1_test', 
                                '3-2_train', 
                                '4-2_test'],
            '1-1_train': ['learnkit_sample_classification_tasks_numberdata'],
            '2-1_test': ['learnkit_sample_classification_tasks_numberdata',
                         'learnkit_sample_classification_tasks_numberdata2'],
            '3-2_train': ['learnkit_sample_classification_tasks_numberdata2'],
            '4-2_test': ['learnkit_sample_classification_tasks_numberdata',
                         'learnkit_sample_classification_tasks_numberdata2'],
            'learnkit_sample_classification_tasks_numberdata': [],
            'learnkit_sample_classification_tasks_numberdata2': []
        }
 
        for (parent_dir, child_dirs) in expected_dirs.items():
            self.assertSetEqual(set(child_dirs), set(found_dirs[parent_dir]))

        tempdir.cleanup()


    def test_log_directory_contents(self):
        print("\ntest_log_directory_contents")
        tempdir = tempfile.TemporaryDirectory(prefix="learnkit_test_")
        with patch.dict('os.environ', {'L2DATA': tempdir.name}):
            classroom = learnkit.Classroom()
            syllabus_file = module_relative_file(__file__, 'syllabi/datasyllabus-w-phases2')
            (full_results, syllabus_log_dir) = run_data_syllabus(classroom, syllabus_file, logging=True)
            classroom.close()

        results = dict_list_to_tuple_list(full_results, 
                ["task_name", "num_batches", "batch_sizes", "batch_ids", "block", "phase_name", "enable_updates"])

        # check the sequence of datasets that were generated
        expected_results = [
            # task_name                             num_batches     batch_sizes           batch_ids, block   phase enable_updates
            ('learnkit.sample_classification_tasks.NumberData',  4, [100, 100, 100, 100],   [0,1,2,3],  0, "1.train", True),
            ('learnkit.sample_classification_tasks.NumberData',  3, [150, 150, 100],        [0,1,2],    1, "1.train", True),
            ('learnkit.sample_classification_tasks.NumberData',  3, [175, 175, 50],         [0,1,2],    2, "1.test", False),
            ('learnkit.sample_classification_tasks.NumberData2', 3, [195, 195, 10],         [0,1,2],    3, "1.test", False),
            ('learnkit.sample_classification_tasks.NumberData2', 4, [100, 100, 100, 100],   [0,1,2,3],  4, "2.train", True),
            ('learnkit.sample_classification_tasks.NumberData2', 3, [150, 150, 100],        [0,1,2],    5, "2.train", True),
            ('learnkit.sample_classification_tasks.NumberData',  2, [250, 150],             [0,1],      6, "2.test", False),
            ('learnkit.sample_classification_tasks.NumberData2', 2, [300, 100],             [0,1],      7, "2.test", False)
        ]

        self.assertSequenceEqual(results, expected_results)
    
        df = read_log_data(syllabus_log_dir)
        print(df)

        columns=['phase', 'task_name', 'block', 'task', 'batch_id', 'batch_size', 'source']
        expected_logs_df = pd.DataFrame([
            # phase     class        block  task  batch_id batch_size source
            ['1.train',  'numberdata',   0,    0,      0,   100,     'NEXT_BATCH'],
            ['1.train',  'numberdata',   0,    0,      1,   100,     'NEXT_BATCH'],
            ['1.train',  'numberdata',   0,    0,      2,   100,     'NEXT_BATCH'],
            ['1.train',  'numberdata',   0,    0,      3,   100,     'NEXT_BATCH'],

            ['1.train',  'numberdata',   1,    1,      0,   150,     'NEXT_BATCH'],
            ['1.train',  'numberdata',   1,    1,      1,   150,     'NEXT_BATCH'],
            ['1.train',  'numberdata',   1,    1,      2,   100,     'NEXT_BATCH'],

            ['1.test',  'numberdata',   2,    2,      0,   175,     'NEXT_BATCH'],
            ['1.test',  'numberdata',   2,    2,      1,   175,     'NEXT_BATCH'],
            ['1.test',  'numberdata',   2,    2,      2,    50,     'NEXT_BATCH'],

            ['1.test',  'numberdata2',   3,    3,     0,   195,     'NEXT_BATCH'],
            ['1.test',  'numberdata2',   3,    3,     1,   195,     'NEXT_BATCH'],
            ['1.test',  'numberdata2',   3,    3,     2,    10,     'NEXT_BATCH'],

            ['2.train',  'numberdata2',   4,    4,    0,   100,     'NEXT_BATCH'],
            ['2.train',  'numberdata2',   4,    4,    1,   100,     'NEXT_BATCH'],
            ['2.train',  'numberdata2',   4,    4,    2,   100,     'NEXT_BATCH'],
            ['2.train',  'numberdata2',   4,    4,    3,   100,     'NEXT_BATCH'],

            ['2.train',  'numberdata2',   5,    5,    0,   150,     'NEXT_BATCH'],
            ['2.train',  'numberdata2',   5,    5,    1,   150,     'NEXT_BATCH'],
            ['2.train',  'numberdata2',   5,    5,    2,   100,     'NEXT_BATCH'],

            ['2.test',  'numberdata',     6,    6,      0,   250,     'NEXT_BATCH'],
            ['2.test',  'numberdata',     6,    6,      1,   150,     'NEXT_BATCH'],
            
            ['2.test',  'numberdata2',   7,     7,     0,   300,     'NEXT_BATCH'],
            ['2.test',  'numberdata2',   7,     7,     1,   100,     'NEXT_BATCH']
            ], columns=columns)

        expected_logs_df.task_name = 'learnkit_sample_classification_tasks_' + expected_logs_df.task_name
        expected_logs_df.task_name = expected_logs_df.task_name.str.lower()

        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_logs_df,
                        classes=None,
                        task_name=False,
                        sort_by=['block', 'task', 'batch_id'],
                        columns=columns, blocks=None))

        tempdir.cleanup()
