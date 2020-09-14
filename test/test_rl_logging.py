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

@unittest.skipUnless(importlib.util.find_spec('pandas'), "Requires pandas library")
class TestRLTaskLoggingSubepisodes(unittest.TestCase):

    def test_syllabus_with_subepisodes(self):
        print("\test_syllabus_with_subepisodes")
        # The syllabus has TestRLTask episodes with steps=5, i.e., each episode
        # will return done=True after 5 steps (the episode can be restarted with a
        # call to reset). Choose total_steps so that it doesn't divide this evenly, i.e.
        # so that an episode will bail out halfway through a sub-episode.
        total_steps = 12
        classroom = learnkit.Classroom()
        syllabus_file = module_relative_file(__file__, 'syllabi/rlsyllabus1-w-phases3')
        (_, syllabus_log_dir) = run_syllabus(classroom, syllabus_file, folder_tag="totalsteps",
            fcn=lambda episode: run_single_episode_till_totalsteps(episode, total_steps=total_steps))

        # only looking at tasks (episode numbers) 0, 1, 4, 5, 36, 37
        columns=['phase', 'class_name', 'block', 'task', 'sub_task', 'steps', 'termination_status']
        expected_df = pd.DataFrame([
            # phase     class       block  task  sub_task steps status
            ['train',  'testrltask', 0,      0,      0,     5,  'DONE'],
            ['train',  'testrltask', 0,      0,      1,    10,  'DONE'],
            ['train',  'testrltask', 0,      0,      2,    12,  'NOT_DONE'],
            #
            ['train',  'testrltask', 0,      1,      0,     5,  'DONE'],
            ['train',  'testrltask', 0,      1,      1,    10,  'DONE'],
            ['train',  'testrltask', 0,      1,      2,    12,  'NOT_DONE'],
            #
            ['train',  'testrltask2', 2,     4,      0,     5,  'DONE'],
            ['train',  'testrltask2', 2,     4,      1,    10,  'DONE'],
            ['train',  'testrltask2', 2,     4,      2,    12,  'NOT_DONE'],
            #
            ['train',  'testrltask2', 2,     5,      0,     5,  'DONE'],
            ['train',  'testrltask2', 2,     5,      1,    10,  'DONE'],
            ['train',  'testrltask2', 2,     5,      2,    12,  'NOT_DONE'],
            #
            ['final',  'testrltask',  12,    36,     0,     5,  'DONE'],
            ['final',  'testrltask',  12,    36,     1,    10,  'DONE'],
            ['final',  'testrltask',  12,    36,     2,    12,  'NOT_DONE'],
            #
            ['final',  'testrltask2', 13,    37,     0,     5,  'DONE'],
            ['final',  'testrltask2', 13,    37,     1,    10,  'DONE'],
            ['final',  'testrltask2', 13,    37,     2,    12,  'NOT_DONE']
            ], columns=columns)

        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_df,
                            classes=['testrltask', 'testrltask2'],
                            columns=columns, blocks=None, tasks=[0, 1, 4, 5, 36, 37]))



@unittest.skipUnless(importlib.util.find_spec('pandas'), "Requires pandas library")
class TestRLTaskLoggingEdgeCases(unittest.TestCase):

    def setUp(self):
        self.classroom = learnkit.Classroom()
        self.syllabus_file = module_relative_file(__file__, 'syllabi/testrltasks_simple')
        self.columns = ['block', 'task', 'sub_task', 'steps', 'termination_status']

    def test_resetsonly_episodes(self):
        print("\ntest_resetsonly_episodes")
        (_, syllabus_log_dir) = run_syllabus(self.classroom, self.syllabus_file, folder_tag="resetsonly",
            fcn=lambda episode: run_single_episode_resets_only(episode, num_resets=3))
        expected_df = pd.DataFrame([
            # block  task  sub_task steps status
            [0,      0,      2,     0,  'NOT_DONE'],
            [0,      1,      2,     0,  'NOT_DONE'],
            [0,      2,      2,     0,  'NOT_DONE']
            ], columns=self.columns)

        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_df,
                        columns=self.columns, classes=["testrltask"], blocks=[0]))


    def test_noop_episodes(self):
        print("\ntest_noop_episodes")
        (_, syllabus_log_dir) = run_syllabus(self.classroom, self.syllabus_file, folder_tag="noop",
                    fcn=run_single_episode_noop)
        expected_df = pd.DataFrame([
            # block  task  sub_task steps status
            [0,      0,      -1,     0,  'NOT_DONE'],
            [0,      1,      -1,     0,  'NOT_DONE'],
            [0,      2,      -1,     0,  'NOT_DONE']
            ], columns=self.columns)

        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_df,
                        columns=self.columns, classes=["testrltask"], blocks=[0]))


    def test_incomplete_episodes(self):
        print("\ntest_incomplete_episodes")
        (_, syllabus_log_dir) = run_syllabus(self.classroom, self.syllabus_file, folder_tag="incomplete",
            fcn=lambda episode: run_single_episode_incomplete_subepisodes(episode, num_resets=3, num_steps=3))
        expected_df = pd.DataFrame([
            # block  task  sub_task steps status
            [0,      0,      0,     3,  'NOT_DONE'],
            [0,      0,      1,     6,  'NOT_DONE'],
            [0,      0,      2,     9,  'NOT_DONE'],
            #
            [0,      1,      0,     3,  'NOT_DONE'],
            [0,      1,      1,     6,  'NOT_DONE'],
            [0,      1,      2,     9,  'NOT_DONE'],
            #
            [0,      2,      0,     3,  'NOT_DONE'],
            [0,      2,      1,     6,  'NOT_DONE'],
            [0,      2,      2,     9,  'NOT_DONE']
            ], columns=self.columns)

        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_df,
                        columns=self.columns, classes=["testrltask"], blocks=[0]))


    def test_extralong_episodes(self):
        print("\ntest_extralong_episodes")
        (_, syllabus_log_dir) = run_syllabus(self.classroom, self.syllabus_file, folder_tag="extralong",
            fcn=lambda episode: run_single_episode_extralong_subepisodes(episode, num_resets=3, num_extra_steps=3))
        expected_df = pd.DataFrame([
            # block  task  sub_task steps status
            [0,      0,      0,     8,  'DONE'],
            [0,      0,      1,    16,  'DONE'],
            [0,      0,      2,    24,  'DONE'],
            #
            [0,      1,      0,     8,  'DONE'],
            [0,      1,      1,    16,  'DONE'],
            [0,      1,      2,    24,  'DONE'],
            #
            [0,      2,      0,     8,  'DONE'],
            [0,      2,      1,    16,  'DONE'],
            [0,      2,      2,    24,  'DONE']
            ], columns=self.columns)

        self.assertTrue(compare_dataframes(syllabus_log_dir, expected_df,
                        columns=self.columns, classes=["testrltask"], blocks=[0]))


class TestRLTaskLoggingDisable(unittest.TestCase):

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
            syllabus_file = module_relative_file(__file__, 'syllabi/rlsyllabus1-w-phases2')
            (_, syllabus_log_dir) = run_syllabus(classroom, syllabus_file, logging=logging_val)
            classroom.close()
        found_dirs = walk_directory_tree(tempdir.name)
        self.assertListEqual(found_dirs['logs'], [])


@unittest.skipUnless(importlib.util.find_spec('pandas'), "Requires pandas library")
class TestRLTaskLoggingPhases(unittest.TestCase):

    def test_episode_sequence_with_phases(self):
        print("\ntest_simple_episode_sequence_with_phases2")
        tempdir = tempfile.TemporaryDirectory(prefix="learnkit_test_")
        with patch.dict('os.environ', {'L2DATA': tempdir.name}):
            classroom = learnkit.Classroom()
            syllabus_file = module_relative_file(__file__, 'syllabi/rlsyllabus1-w-phases2')
            (full_results, syllabus_log_dir) = run_syllabus(classroom, syllabus_file)
            classroom.close()

        # check the sequence of episodes that were generated
        results = dict_list_to_tuple_list(full_results, ["class_name", "num_steps"])
        expected_results = [('learnkit.sample_rl_tasks.HillClimber', 2),
                            ('learnkit.sample_rl_tasks.HillClimber', 6),
                            ('learnkit.sample_rl_tasks.HillClimber', 3),
                            ('learnkit.sample_rl_tasks.HillClimber', 5),
                            ('learnkit.sample_rl_tasks.HillClimber2', 3),
                            ('learnkit.sample_rl_tasks.HillClimber2', 5),
                            ('learnkit.sample_rl_tasks.HillClimber3', 3),
                            ('learnkit.sample_rl_tasks.HillClimber3', 5),
                            #
                            ('learnkit.sample_rl_tasks.HillClimber2', 2),
                            ('learnkit.sample_rl_tasks.HillClimber2', 6),
                            ('learnkit.sample_rl_tasks.HillClimber', 3),
                            ('learnkit.sample_rl_tasks.HillClimber', 5),
                            ('learnkit.sample_rl_tasks.HillClimber2', 3),
                            ('learnkit.sample_rl_tasks.HillClimber2', 5),
                            ('learnkit.sample_rl_tasks.HillClimber3', 3),
                            ('learnkit.sample_rl_tasks.HillClimber3', 5),
                            #
                            ('learnkit.sample_rl_tasks.HillClimber3', 2),
                            ('learnkit.sample_rl_tasks.HillClimber3', 6),
                            ('learnkit.sample_rl_tasks.HillClimber', 2),
                            ('learnkit.sample_rl_tasks.HillClimber2', 2),
                            ('learnkit.sample_rl_tasks.HillClimber3', 2),
                            #
                            ('learnkit.sample_rl_tasks.HillClimber', 2),
                            ('learnkit.sample_rl_tasks.HillClimber2', 4),
                            ('learnkit.sample_rl_tasks.HillClimber3', 6)]
        self.assertSequenceEqual(results, expected_results)

        # check the log directories that were generated
        found_dirs = walk_directory_tree(tempdir.name)

        expected_dirs = {
            'worker-primary': ['1-1_train',
                         '2-1_test_hillclimber',
                         '3-2_test_hillclimber2',
                         '4-2_test_hillclimber3',
                         '5-2_train',
                         '6-2_test_hillclimber',
                         '7-2_test_hillclimber2',
                         '8-2_test_hillclimber3',
                         '9-3_train',
                         '10-3_test',
                         '11-weirdname_1_foobar-abcd1234_asdfads',
                         ],
            '1-1_train': [
                        'learnkit_sample_rl_tasks_hillclimber'],
            '2-1_test_hillclimber': [
                        'learnkit_sample_rl_tasks_hillclimber'],
            '3-2_test_hillclimber2': [
                        'learnkit_sample_rl_tasks_hillclimber2'],
            '4-2_test_hillclimber3': [
                        'learnkit_sample_rl_tasks_hillclimber3'],
            '5-2_train': [
                        'learnkit_sample_rl_tasks_hillclimber2'],
            '6-2_test_hillclimber': [
                        'learnkit_sample_rl_tasks_hillclimber'],
            '7-2_test_hillclimber2': [
                        'learnkit_sample_rl_tasks_hillclimber2'],
            '8-2_test_hillclimber3': [
                        'learnkit_sample_rl_tasks_hillclimber3'],
            '9-3_train': [
                        'learnkit_sample_rl_tasks_hillclimber3'],
            '10-3_test': [
                        'learnkit_sample_rl_tasks_hillclimber',
                        'learnkit_sample_rl_tasks_hillclimber2',
                        'learnkit_sample_rl_tasks_hillclimber3'],
            '11-weirdname_1_foobar-abcd1234_asdfads': [
                    'learnkit_sample_rl_tasks_hillclimber',
                    'learnkit_sample_rl_tasks_hillclimber2',
                    'learnkit_sample_rl_tasks_hillclimber3']
        }

        # pprint.pprint(dirinfo, indent=3)
        for (parent_dir, child_dirs) in expected_dirs.items():
            self.assertSetEqual(set(child_dirs), set(found_dirs[parent_dir]))

        tempdir.cleanup()
