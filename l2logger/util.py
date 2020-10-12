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

import glob
import json
import logging
import os
import platform

import pandas as pd


def get_l2data_root(warn=True):
    """Get the root directory where L2 data and logs are saved"""
    try:
        root_dir = os.environ['L2DATA']
    except KeyError:
        if warn:
            msg = "L2DATA directory not specified. Using ~/l2data as default.\n\n" \
                "This module requires the environment variable 'L2DATA' be set to the top level folder under which\n" \
                "all data is, or will be, stored. For example, consider the following commands:\n" \
                "\t(bash) export L2DATA=/path/to/data/l2data\n" \
                "\t(Windows) set L2DATA=C:\\\\path\\\\to\\\\data\\\\l2data\n"
            logging.warning(msg)
        root_dir = 'l2data'
        if platform.system().lower() == 'windows':
            root_dir = os.path.join(os.environ['APPDATA'], root_dir)
        else:
            root_dir = os.path.join(os.path.expanduser('~'), root_dir)

    if not os.path.exists(root_dir):
        os.makedirs(root_dir, exist_ok=True)

    return root_dir


def get_l2root_base_dirs(directory_to_append, sub_to_get=None):
    # This function uses a utility function to get the base $L2DATA path and goes one level down
    # with the option to return the path string for the directory or the file underneath:
    # e.g. $L2DATA/logs/some_log_directory
    # or   $L2DATA/taskinfo/info.json
    file_info_to_return = os.path.join(get_l2data_root(), directory_to_append)

    if sub_to_get:
        base_dir = file_info_to_return
        file_info_to_return = os.path.join(base_dir, sub_to_get)

    return file_info_to_return


def get_fully_qualified_name(log_dir):
    if os.path.dirname(log_dir) == '':
        return get_l2root_base_dirs('logs', log_dir)
    else:
        if os.path.isdir(log_dir):
            return log_dir
        else:
            raise NotADirectoryError


def read_log_data(input_dir, analysis_variables=None):
    # This function scrapes the TSV files containing syllabus metadata and system performance log data and returns a
    # pandas dataframe with the merged data
    logs = None
    blocks = None

    fully_qualified_dir = get_fully_qualified_name(input_dir)

    for root, _, files in os.walk(fully_qualified_dir):
        for file in files:
            if file == 'data-log.tsv':
                if analysis_variables is not None:
                    df = pd.read_csv(os.path.join(root, file), sep='\t')[
                        ['timestamp', 'block_num', 'regime_num', 'exp_num'] + analysis_variables]
                else:
                    df = pd.read_csv(os.path.join(root, file), sep='\t')
                if logs is None:
                    logs = df
                else:
                    logs = pd.concat([logs, df])
            if file == 'block-info.tsv':
                df = pd.read_csv(os.path.join(root, file), sep='\t')
                if blocks is None:
                    blocks = df
                else:
                    blocks = pd.concat([blocks, df])

    return logs.merge(blocks, on=['block_num', 'regime_num'])


def read_column_info(input_dir):
    # This function reads the column info JSON file in the input directory returns the contents

    fully_qualified_dir = get_fully_qualified_name(input_dir)

    with open(fully_qualified_dir + '/column_info.json') as json_file:
        column_info = json.load(json_file)
        return column_info['metrics_columns']
