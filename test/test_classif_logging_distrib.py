"""
Test RL Logging in a distributed setting
"""
import os
import unittest
import tempfile
from unittest.mock import patch
import pprint
import importlib
import threading
import queue
import learnkit
import time
import itertools

from learnkit.utils import module_relative_file
from .utils import *

if importlib.util.find_spec('pandas'):
    import pandas as pd


"""
General approach for testing distributed logging
* Use threads for different workers
* The master allocates the episodes to workers in a deterministic manner (round robin)
* The workers convey their resuls back to the master
* The master assembles and organizes the results for comparison with expected results
"""

# TODO: Remove learnkit dependencies

class QueueWorker(threading.Thread):
    def __init__(self, name, work_queue, results_queue):
        super().__init__(target=self, name=name)
        self.classroom = learnkit.DynamicClassroom(name=name)
        self.work_queue = work_queue
        self.results_queue = results_queue
        self.classroom.performance_logging = True

    def run(self):
        while True:
            time.sleep(0.01)
            try:
                fragments = self.work_queue.get(block=False)
            except queue.Empty:
                break
            self.classroom.add([fragments])
            with self.classroom.load("datasets") as syllabus:
                for dataset in syllabus.datasets():
                    results = run_single_dataset_till_done(dataset)
                    self.results_queue.put((self.name, results['task_name'], dataset.info.phase_name,
                                            dataset.info.block_number, dataset.count, results['num_batches'], 
                                            results['batch_sizes'],
                                            tuple(dataset.info.custom.keys()), dataset.info.enable_updates ))
            self.work_queue.task_done()


def run_classroom_with_workers(classroom, syllabus_file, num_workers=3):
    if not isinstance(classroom, learnkit.MasterClassroom):
        raise ValueError("Expecting a MasterClassroom")
    classroom.performance_logging = True
    with classroom.load(syllabus_file) as syllabus:
        work_queues = [queue.Queue() for _ in range(num_workers)]
        results_queue = queue.Queue()

        workers = []
        for (index, work_queue) in enumerate(work_queues):
            worker = QueueWorker("w{0}".format(index), work_queue, results_queue)
            workers.append(worker)

        # populate the work queues
        workqueue_gen = itertools.cycle(work_queues)
        for dataset in syllabus.datasets():
            jsonstr = dataset.to_json()
            work_queue = next(workqueue_gen)
            work_queue.put(jsonstr)

        # start the workers & wait the work to be done
        for worker in workers:
            worker.start()

        for work_queue in work_queues:
            work_queue.join()

        for worker in workers:
            worker.join()

        # retrieve all the results from the results_queue
        results = []
        while not results_queue.empty():
            results.append(list(results_queue.get(False)))

        df = pd.DataFrame(results, columns=["worker", "task_name", "phase", "block", "task", 
                                            "num_batches", "batch_sizes", "custom_info", "enable_updates"])
        df = df.sort_values(by="task").reset_index(drop=True)
        logdir = syllabus.log_dir

    return (df, logdir)


@unittest.skipUnless(importlib.util.find_spec('pandas'), "Requires pandas library")
class TestDistributedLogging(unittest.TestCase):

    def test_dataset_sequence_with_phases(self):
        """
        This test exercises both what the workers produce (i.e., what values they result
        via the episode API), and the resulting logs.
        Note that the syllabus includes 
          * phases 
          * phase enable_updates attribute
          * multiple tasks (with $repeat's)
          * uses of $info (rendered as episode.info.custom)
        """
        print("\ntest_dataset_sequence_with_phases")
        classroom = learnkit.MasterClassroom()
        syllabus_file = module_relative_file(__file__, 'syllabi/datasyllabus-w-phases-distrib')
        (results_df, syllabus_log_dir) = run_classroom_with_workers(classroom, syllabus_file, num_workers=3)
        classroom.close()

        print(results_df)

        columns = ["worker", "task_name", "phase", "block", "task", "num_batches", "batch_sizes", "custom_info", "enable_updates"]
        expected_df = pd.DataFrame([
            # "worker", "class",   "phase", "block", "task", "num_batches", batch_sizes, "custom_info", "enable_updates"
            # phase 1.train
            ['w0', 'NumberData',  '1.train',  0, 0,  2,  [200,200],       ('infofoo',), True],
            ['w1', 'NumberData',  '1.train',  0, 1,  2,  [200,200],       ('infofoo',), True],
            ['w2', 'NumberData2', '1.train',  1, 2,  3,  [150, 150, 100], ('infofoo',), True],
            ['w0', 'NumberData2', '1.train',  1, 3,  3,  [150, 150, 100], ('infofoo',), True],
            # phase 1.test
            ['w1', 'NumberData',  '1.test',   2, 4,  2,  [200,200],      ('infofoo', 'infobar'), False],
            ['w2', 'NumberData2', '1.test',   3, 5,  2,  [200,200],      ('infofoo', 'infobar'), False],
            # phase 2.train
            ['w0', 'NumberData',  '2.train',  4, 6,  2,  [300,100],      ('infobar',), True],
            ['w1', 'NumberData',  '2.train',  4, 7,  2,  [300,100],      ('infobar',), True],
            ['w2', 'NumberData2', '2.train',  5, 8,  2,  [250,150],      ('infobar',), True],
            ['w0', 'NumberData2', '2.train',  5, 9,  2,  [250,150],      ('infobar',), True],
            # phase 2.test
            ['w1', 'NumberData',  '2.test',   6, 10, 3,  [150, 150, 100], (), False],
            ['w2', 'NumberData2', '2.test',   7, 11, 2,  [225, 175],      (), False]
        ], columns=columns)

        expected_df.task_name = 'learnkit.sample_classification_tasks.' + expected_df.task_name

        if not results_df.equals(expected_df):
            print("------- expected results")
            print(expected_df)
            print("------- actual results")
            print(results_df)
            self.fail("dataframes mismatch")

        columns = ["worker", "task_name", "phase", "block", "task", "batch_id", "batch_size"]
        expected_logs_df = pd.DataFrame([
            # "worker", "class",   "phase", "block", "task", "batch_id", batch_size
            # phase 1.train -----------------------
            ['w0', 'NumberData',  '1.train',  0,      0,      0,         200],
            ['w0', 'NumberData',  '1.train',  0,      0,      1,         200],

            ['w1', 'NumberData',  '1.train',  0,      1,      0,         200],
            ['w1', 'NumberData',  '1.train',  0,      1,      1,         200],

            ['w2', 'NumberData2', '1.train',  1,      2,      0,         150],
            ['w2', 'NumberData2', '1.train',  1,      2,      1,         150],
            ['w2', 'NumberData2', '1.train',  1,      2,      2,         100],

            ['w0', 'NumberData2', '1.train',  1,      3,      0,         150],
            ['w0', 'NumberData2', '1.train',  1,      3,      1,         150],
            ['w0', 'NumberData2', '1.train',  1,      3,      2,         100],
            # phase 1.test  -----------------------
            ['w1', 'NumberData',  '1.test',   2,      4,      0,         200],
            ['w1', 'NumberData',  '1.test',   2,      4,      1,         200],

            ['w2', 'NumberData2', '1.test',   3,      5,      0,         200],
            ['w2', 'NumberData2', '1.test',   3,      5,      1,         200],
            # phase 2.train  -----------------------
            ['w0', 'NumberData',  '2.train',  4,      6,      0,         300],
            ['w0', 'NumberData',  '2.train',  4,      6,      1,         100],

            ['w1', 'NumberData',  '2.train',  4,      7,      0,         300],
            ['w1', 'NumberData',  '2.train',  4,      7,      1,         100],

            ['w2', 'NumberData2', '2.train',  5,      8,      0,         250],
            ['w2', 'NumberData2', '2.train',  5,      8,      1,         150],

            ['w0', 'NumberData2', '2.train',  5,      9,      0,         250],
            ['w0', 'NumberData2', '2.train',  5,      9,      1,         150],
            # phase 2.test  -----------------------
            ['w1', 'NumberData',  '2.test',   6,     10,      0,         150],
            ['w1', 'NumberData',  '2.test',   6,     10,      1,         150],
            ['w1', 'NumberData',  '2.test',   6,     10,      2,         100],

            ['w2', 'NumberData2', '2.test',   7,     11,      0,         225],
            ['w2', 'NumberData2', '2.test',   7,     11,      1,         175]
        ], columns=columns)

        expected_logs_df.task_name = 'learnkit_sample_classification_tasks_' + expected_logs_df.task_name
        expected_logs_df.task_name = expected_logs_df.task_name.str.lower()
        print(syllabus_log_dir)
        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_logs_df,
                        columns=columns, classes=None,
                        simplify_class_name=False,
                        sort_by=['block', 'task']))
