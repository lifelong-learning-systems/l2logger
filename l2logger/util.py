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
from typing import List

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
        raise FileNotFoundError(f'Log directory not found!')

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
        (task_names[:-1] != task_names[1:]) + (task_params[:-1] != task_params[1:])

    # Number the regime changes
    regimes = [np.count_nonzero(changes[:i]) for i, _ in enumerate(changes)]
    regimes.append(regimes[-1] + 1 if changes[-1] else regimes[-1])

    # Set regime numbers in data
    data['regime_num'] = regimes

    return data


def parse_blocks(data: pd.DataFrame) -> pd.DataFrame:
    """Parse full DataFrame and create summary DataFrame of high-level block information.

    Args:
        data (pd.DataFrame): Log data.

    Returns:
        pd.DataFrame: Block info DataFrame.
    """

    blocks_df = data.loc[:, ['regime_num', 'block_num', 'block_type', 'task_name', 'task_params']].drop_duplicates()

    # Quick check to make sure the regime numbers (zero indexed) aren't a mismatch on the length of the regime nums array
    num_regimes = max(data['regime_num'].values) + 1
    if num_regimes != blocks_df.shape[0]:
        warnings.warn(f'Number of regimes: {num_regimes} and parsed blocks {blocks_df.shape[0]} mismatch!')

    return blocks_df


def read_logger_info(input_dir: str) -> dict:
    """Read logger info file with valid metric columns.

    Args:
        input_dir (str): The top-level log directory.

    Raises:
        FileNotFoundError: If logger info file is not found.

    Returns:
        dict: The logger info dictionary.
    """

    # This function reads the logger info JSON file in the input directory and returns the list of
    # metrics columns that can be used for computing LL metrics

    fully_qualified_dir = Path(get_fully_qualified_name(input_dir))

    if not (fully_qualified_dir / 'logger_info.json').exists():
        raise FileNotFoundError(f'Logger info file not found!')

    with open(fully_qualified_dir / 'logger_info.json') as json_file:
        return json.load(json_file)


def read_scenario_info(input_dir: str) -> dict:
    """Read scenario information file with complexity, difficulty, and scenario type.

    Args:
        input_dir (str): The top-level log directory.

    Raises:
        FileNotFoundError: If scenario info file is not found.
        RuntimeError: If invalid scenario complexity specified.
        RuntimeError: If invalid scenario difficulty specified.
        RuntimeError: If invalid scenario type specified.

    Returns:
        dict: The scenario info dictionary.
    """

    # This function reads the scenario info JSON file in the input directory and validates the contents

    fully_qualified_dir = Path(get_fully_qualified_name(input_dir))
    scenario_dir = fully_qualified_dir.name

    if not (fully_qualified_dir / 'scenario_info.json').exists():
        raise FileNotFoundError(f'Scenario info file not found!')

    with open(fully_qualified_dir / 'scenario_info.json') as json_file:
        scenario_info = json.load(json_file)

        if 'complexity' in scenario_info.keys():
            if scenario_info['complexity'] not in ['1-low', '2-intermediate', '3-high']:
                raise RuntimeError(f"Invalid complexity for {scenario_dir}: {scenario_info['complexity']}")
        else:
            scenario_info['complexity'] = ''
            warnings.warn(f'Complexity not defined in scenario: {scenario_dir}')

        if 'difficulty' in scenario_info.keys():
            if scenario_info['difficulty'] not in ['1-easy', '2-medium', '3-hard']:
                raise RuntimeError(f"Invalid difficulty for {scenario_dir}: {scenario_info['difficulty']}")
        else:
            scenario_info['difficulty'] = ''
            warnings.warn(f'Difficulty not defined in scenario: {scenario_dir}')

        if 'scenario_type' in scenario_info.keys():
            if scenario_info['scenario_type'] not in ['permuted', 'alternating', 'custom']:
                raise RuntimeError(f"Invalid scenario type for {scenario_dir}: {scenario_info['scenario_type']}")
        else:
            scenario_info['scenario_type'] = ''
            warnings.warn(f'Scenario type not defined in scenario: {scenario_dir}')

        return scenario_info


def validate_log(data: pd.DataFrame, metric_fields: List[str]) -> None:
    """Validate log data format.

    Args:
        data (pd.DataFrame): Log data.
        metric_fields (List[str]): The application-specific metrics columns defined in logger info.

    Raises:
        RuntimeError: If the standard columns are missing.
        RuntimeError: If the data does not contain the specified metrics columns.
        RuntimeError: If task names are invalid format.
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
    task_name_pattern = re.compile(r'[0-9a-zA-Z]+_[0-9a-zA-Z]+')
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

    task_names = np.unique(data.task_name.values)
    block_nums = data.block_num.values
    exp_nums = data.exp_num.values
    block_types = data.block_type.values
    exp_statuses = data.exp_status.values
    worker_ids = data.worker_id.values
    task_params = data.task_params.fillna('').values

    # Validate task naming convention
    if None in [re.fullmatch(task_name_pattern, str(task_name)) for task_name in task_names]:
        warnings.warn(f'Task names do not follow expected format: <tasklabel>_<variantlabel>')

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
