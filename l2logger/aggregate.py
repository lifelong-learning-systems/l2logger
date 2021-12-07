"""
Copyright © 2021 The Johns Hopkins University Applied Physics Laboratory LLC

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the “Software”), to 
deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR 
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

"""
This Python module is a utility for exporting an aggregated data table from an
L2Logger directory as either a Feather file or CSV.
"""

import argparse
import traceback
from pathlib import Path

from l2logger import util


def run():
    # Instantiate parser
    parser = argparse.ArgumentParser(
        description='Aggregate data within a log directory from the command line')

    # Log directories can be absolute paths, relative paths, or paths found in $L2DATA/logs
    parser.add_argument('log_dir', type=str, help='Log directory of scenario')

    # Output format
    parser.add_argument('-f', '--format', type=str, default='csv',
                        choices=['csv', 'feather'], help='Output format of data table')

    # Output filename
    parser.add_argument('-o', '--output', type=str,
                        default='data', help='Output filename')

    # Parse arguments
    args = parser.parse_args()
    log_dir = Path(args.log_dir)

    # Attempt to read log data
    log_data = util.read_log_data(log_dir)

    # Filter data by completed experiences
    log_data = log_data[log_data['exp_status'] == 'complete']

    # Fill in regime number and sort
    log_data = util.fill_regime_num(log_data)
    log_data = log_data.sort_values(
        by=['regime_num', 'exp_num']).set_index("regime_num", drop=False)

    # Save log data to file
    if args.format == 'csv':
        log_data.to_csv(Path(args.output + '.csv'), index=False)
    elif args.format == 'feather':
        log_data.reset_index(drop=True).to_feather(str(Path(args.output + '.feather')))


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print(f'Error with validating logs: {e}')
        traceback.print_exc()
