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

import argparse
import traceback

from l2logger import util
from tabulate import tabulate


def run():
    # Instantiate parser
    parser = argparse.ArgumentParser(description='Validate log format from the command line')

    # Log directories can be absolute paths, relative paths, or paths found in $L2DATA/logs
    parser.add_argument('log_dir', type=str, help='Log directory of scenario')

    # Parse arguments
    args = parser.parse_args()

    # Attempt to read log data
    log_data = util.read_log_data(args.log_dir)

    # Get metric fields
    metric_fields = util.read_logger_info(args.log_dir)

    # Validate scenario info
    util.validate_scenario_info(args.log_dir)

    # Validate log format
    util.validate_log(log_data, metric_fields)
    print('\nLog format validation passed!\n')

    # Fill in regime number and sort
    log_data = util.fill_regime_num(log_data)
    log_data = log_data.sort_values(by=['regime_num', 'exp_num']).set_index("regime_num", drop=False)

    # Print log summary
    _, log_summary = util.parse_blocks(log_data)
    if log_summary['task_params'].dropna().size:
        log_summary['task_params'] = log_summary['task_params'].apply(lambda x: x[:25] + '...' if len(x) > 25 else x)
    else:
        log_summary = log_summary.dropna(axis=1)

    print('Log summary:')
    print(tabulate(log_summary, headers='keys', tablefmt='psql'))


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print(f'Error with validating logs: {e}')
        traceback.print_exc()
