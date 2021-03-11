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

import json
import os
import platform
import re
import warnings
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd


def get_l2data_root(warn: bool = True) -> str:
    """Get the root directory where L2 data and logs are saved.

    Args:
        warn (bool, optional): Flag for enabling/disabling warning message. Defaults to True.

    Returns:
        str: The L2Data root directory path.
    """

    try:
        root_dir = os.environ['L2DATA']
    except KeyError:
        if warn:
            msg = "L2DATA directory not specified. Using ~/l2data as default.\n\n" \
                "This module requires the environment variable 'L2DATA' be set to the top level folder under which\n" \
                "all data is, or will be, stored. For example, consider the following commands:\n" \
                "\t(bash) export L2DATA=/path/to/data/l2data\n" \
                "\t(Windows) set L2DATA=C:\\\\path\\\\to\\\\data\\\\l2data\n"
            warnings.warn(msg)
        root_dir = 'l2data'
        if platform.system().lower() == 'windows':
            root_dir = os.path.join(os.environ['APPDATA'], root_dir)
        else:
            root_dir = os.path.join(os.path.expanduser('~'), root_dir)

    if not os.path.exists(root_dir):
        os.makedirs(root_dir, exist_ok=True)

    return root_dir


def get_l2root_base_dirs(directory_to_append: str, sub_to_get: str = None) -> str:
    """Get the base L2DATA path and go one level down with the option to return the path string for
    the directory or the file underneath.

    e.g. $L2DATA/logs/some_log_directory or $L2DATA/taskinfo/info.json

    Args:
        directory_to_append (str): The L2Data subdirectory.
        sub_to_get (str, optional): The further subdirectory or file to append. Defaults to None.

    Returns:
        str: The path of the L2Data subdirectory or file.
    """

    file_info_to_return = os.path.join(get_l2data_root(), directory_to_append)

    if sub_to_get:
        base_dir = file_info_to_return
        file_info_to_return = os.path.join(base_dir, sub_to_get)

    return file_info_to_return


def get_fully_qualified_name(log_dir: str) -> str:
    """Get fully qualified path of log directory.

    Checks if the log directory exists in L2Data/logs first. If not, then this function will check
    the current working directory.

    Args:
        log_dir (str): The log directory name.

    Raises:
        NotADirectoryError: If the directory is not found.

    Returns:
        str: The full path to the log directory.
    """

    if os.path.dirname(log_dir.strip('/\\')) == '':
        return get_l2root_base_dirs('logs', log_dir)
    else:
        if os.path.isdir(log_dir):
            return log_dir
        else:
            raise NotADirectoryError


def read_log_data(input_dir: str, analysis_variables: List[str] = None) -> pd.DataFrame:
    """Parse input directory for data log files and aggregate into Pandas DataFrame.

    Args:
        input_dir (str): The top-level log directory.
        analysis_variables (List[str], optional): Filtered column names to import. Defaults to None.

    Raises:
        FileNotFoundError: If log directory is not found.

    Returns:
        pd.DataFrame: The aggregated log data.
    """

    logs = None

    fully_qualified_dir = Path(get_fully_qualified_name(input_dir))

    if not fully_qualified_dir.is_dir():
        raise FileNotFoundError(f"Log directory not found!")

    for data_file in fully_qualified_dir.rglob('data-log.tsv'):
        if analysis_variables is not None:
            default_cols = ['block_num', 'exp_num', 'block_type', 'worker_id',
                            'task_name', 'task_params', 'exp_status', 'timestamp']
            df = pd.read_csv(data_file, sep='\t')[default_cols + analysis_variables]
        else:
            df = pd.read_csv(data_file, sep='\t')
        if logs is None:
            logs = df
        else:
            logs = pd.concat([logs, df])

    logs = logs.sort_values(['exp_num', 'block_num'], ignore_index=True)
    logs['task_name'] = np.char.lower(list(logs['task_name']))
    return logs


def fill_regime_num(data: pd.DataFrame) -> pd.DataFrame:
    """Add regime number information to the log data based on block and task parameters.

    Args:
        data (pd.DataFrame): Log data.

    Returns:
        pd.DataFrame: The log data with regime numbers filled in.
    """

    block_nums = data.block_num.values
    block_types = data.block_type.values
    task_names = data.task_name.values
    task_params = data.task_params.fillna('').values

    # Get indices where a regime change has occurred
    changes = (block_nums[:-1] != block_nums[1:]) + (block_types[:-1] != block_types[1:]) + \
        (task_names[:-1] != task_names[1:]) + \
        (task_params[:-1] != task_params[1:])

    # Number the regime changes
    regimes = [np.count_nonzero(changes[:i]) for i, _ in enumerate(changes)]
    regimes.append(regimes[-1] + 1)

    # Set regime numbers in data
    data['regime_num'] = regimes

    return data


def parse_blocks(data: pd.DataFrame) -> Tuple[List[int], pd.DataFrame]:
    """Parse full DataFrame and create summary DataFrame of high-level block information.

    Args:
        data (pd.DataFrame): Log data.

    Raises:
        Exception: If unsupported block type is encountered.
        Exception: If parameter set is invalid.

    Returns:
        Tuple[List[int], pd.DataFrame]: List of test regime numbers and block info DataFrame.
    """

    # Want to get the unique blocks, split out training/testing info, and return the split info
    block_list = []
    test_task_nums = []
    all_regime_nums = []

    blocks_from_logs = data.loc[:, ['block_num', 'block_type']].drop_duplicates()

    for _, block in blocks_from_logs.iterrows():
        block_num = block['block_num']
        block_type = block['block_type']

        if str.lower(block_type) not in ["train", "test"]:
            raise Exception(f'Unsupported block type: {block_type}! Supported block types are "train" and "test"')

        # Now must account for the multiple tasks, parameters
        d1 = data[(data["block_num"] == block_num) & (data["block_type"] == block_type)]
        regimes_within_blocks = d1.loc[:, 'regime_num'].unique()
        param_set = d1.loc[:, 'task_params'].unique()

        # Save the regime_num numbers involved in testing for subsequent metrics
        if block_type == 'test':
            test_task_nums.extend(regimes_within_blocks)

        for regime_num in regimes_within_blocks:
            all_regime_nums.append(regime_num)
            d2 = d1[d1['regime_num'] == regime_num]
            task_name = d2.loc[:, 'task_name'].unique()[0]

            block_info = {'block_num': block_num, 'block_type': block_type, 'task_name': task_name,
                          'regime_num': regime_num}

            if len(param_set) > 1:
                # There is parameter variation exercised in the syllabus and we need to record it
                task_specific_param_set = d2.loc[:, 'task_params'].unique()[0]
                block_info['task_params'] = task_specific_param_set
            elif len(param_set) == 1:
                # Every task in this block has the same parameter set
                block_info['task_params'] = param_set[0]
            else:
                raise Exception(f"Error parsing the parameter set for this task: {param_set}")

            block_list.append(block_info)

    # Convenient for future dev to have the block id be the same as the index of the dataframe
    blocks_df = pd.DataFrame(block_list).sort_values(by=['regime_num']).set_index("regime_num", drop=False)

    # Quick check to make sure the regime numbers (zero indexed) aren't a mismatch on the length of the regime nums array
    if (max(all_regime_nums)+1)/len(all_regime_nums) != 1:
        warnings.warn(f"Block number: {max(all_regime_nums)} and length {len(all_regime_nums)} mismatch!")

    return test_task_nums, blocks_df


def read_logger_info(input_dir: str) -> List[str]:
    """Parse logger info file for valid metric columns.

    Args:
        input_dir (str): The top-level log directory.

    Raises:
        FileNotFoundError: If logger info file is not found.

    Returns:
        List[str]: The application-specific metrics columns that the metrics framework can compute
            metrics on.
    """

    # This function reads the logger info JSON file in the input directory and returns the list of
    # metrics columns that can be used for computing LL metrics

    fully_qualified_dir = Path(get_fully_qualified_name(input_dir))

    if not (fully_qualified_dir / 'logger_info.json').exists():
        raise FileNotFoundError(f"Logger info file not found!")

    with open(fully_qualified_dir / 'logger_info.json') as json_file:
        logger_info = json.load(json_file)
        return logger_info['metrics_columns']


def validate_scenario_info(input_dir: str) -> None:
    """Validate scenario information file with complexity and difficulty.

    Args:
        input_dir (str): The top-level log directory.

    Raises:
        FileNotFoundError: If scenario info file is not found.
        RuntimeError: If invalid scenario complexity specified.
        RuntimeError: If invalid scenario difficulty specified.
    """

    # This function reads the scenario info JSON file in the input directory and validates the contents

    fully_qualified_dir = Path(get_fully_qualified_name(input_dir))
    scenario_dir = fully_qualified_dir.name

    if not (fully_qualified_dir / 'scenario_info.json').exists():
        raise FileNotFoundError(f"Scenario info file not found!")

    with open(fully_qualified_dir / 'scenario_info.json') as json_file:
        scenario_info = json.load(json_file)
        
        if 'complexity' in scenario_info.keys():
            if scenario_info['complexity'] not in ['1-low', '2-intermediate', '3-high']:
                raise RuntimeError(f"Invalid complexity for {scenario_dir}: {scenario_info['complexity']}")
        else:
            warnings.warn(f"Complexity not defined in scenario: {scenario_dir}")

        if 'difficulty' in scenario_info.keys():
            if scenario_info['difficulty'] not in ['1-easy', '2-medium', '3-hard']:
                raise RuntimeError(f"Invalid difficulty for {scenario_dir}: {scenario_info['difficulty']}")
        else:
            warnings.warn(f"Difficulty not defined in scenario: {scenario_dir}")


def validate_log(data: pd.DataFrame, metric_fields: List[str]) -> None:
    """Validate log data format.

    Args:
        data (pd.DataFrame): Log data.
        metric_fields (List[str]): The application-specific metrics columns defined in logger info.

    Raises:
        RuntimeError: If the standard columns are missing.
        RuntimeError: If the data does not contain the specified metrics columns.
        RuntimeError: If the block number is negative or non-integer.
        RuntimeError: If the block number is decreasing.
        RuntimeError: If experience number is negative or non-integer.
        RuntimeError: If experience number is decreasing.
        RuntimeError: If block type is invalid.
        RuntimeError: If experience status is invalid.
        RuntimeError: If worker ID is invalid.
        RuntimeError: If task parameters is an invalid JSON.
    """

    # Initialize values
    # last_block_num = None
    # last_exp_num = None
    valid_block_types = ['train', 'test']
    valid_exp_statuses = ['complete', 'incomplete']
    worker_pattern = re.compile(r'[0-9a-zA-Z_\-.]+')
    standard_fields = ['block_num', 'exp_num', 'block_type',
                       'worker_id', 'task_name', 'task_params', 'exp_status', 'timestamp']

    # Validate columns
    if not set(data.columns).issuperset(standard_fields):
        raise RuntimeError(f'standard fields missing: expected at least '
                           f'{standard_fields}, got {set(data.columns)}')
    if not set(data.columns).issuperset(metric_fields):
        raise RuntimeError(f'metric record fields missing: expected at least '
                           f'{metric_fields}, got {set(data.columns)}')

    block_nums = data.block_num.values
    exp_nums = data.exp_num.values
    block_types = data.block_type.values
    exp_statuses = data.exp_status.values
    worker_ids = data.worker_id.values
    task_params = data.task_params.fillna('').values

    # Validate block number
    if not np.all(block_nums >= 0):
        raise RuntimeError(f'block_num must be non-negative integer')
    elif np.any(block_nums[:-1] > block_nums[1:]):
        raise RuntimeError('block_num must be non-decreasing')

    # Validate exp number
    if not np.all(exp_nums >= 0):
        raise RuntimeError(f'exp_num must be non-negative integer')
    elif np.any(exp_nums[:-1] > exp_nums[1:]):
        raise RuntimeError('exp_num must be non-decreasing')

    # Validate block type
    if not np.all(np.isin(block_types, valid_block_types)):
        raise RuntimeError(f'block_type must be one of {block_types}')

    # Validate exp status
    if not np.all(np.isin(exp_statuses, valid_exp_statuses)):
        raise RuntimeError(f'exp_status must be one of {exp_statuses}')   

    # Validate worker ID string pattern
    if None in [re.fullmatch(worker_pattern, str(worker_id)) for worker_id in worker_ids]:
        raise RuntimeError(f'worker_id can only contain alphanumeric characters, hyphens, dashes, or periods')

    # Validate task parameters is valid JSON
    try:
        [json.loads(task_param) for task_param in task_params if task_param != '']
    except:
        raise RuntimeError('task_params must be valid json')
