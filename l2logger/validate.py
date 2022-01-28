"""
Copyright © 2021-2022 The Johns Hopkins University Applied Physics Laboratory LLC

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

import argparse
import logging
from pathlib import Path

from tabulate import tabulate

from l2logger import util

logger = logging.getLogger("l2logger.validate")


def run():
    # Instantiate parser
    parser = argparse.ArgumentParser(
        description="Validate log format from the command line"
    )

    # Log directories can be absolute paths, relative paths, or paths found in $L2DATA/logs
    parser.add_argument("log_dir", type=str, help="Log directory of scenario")

    # Parse arguments
    args = parser.parse_args()
    log_dir = Path(args.log_dir)

    # Attempt to read log data
    log_data = util.read_log_data(log_dir)

    # Get metric fields
    logger_info = util.read_logger_info(log_dir)

    # Validate scenario info
    util.read_scenario_info(log_dir)

    # Validate log format
    util.validate_log(log_data, logger_info["metrics_columns"])
    print("\nLog format validation passed!\n")

    # Filter data by completed experiences
    log_data = log_data[log_data["exp_status"] == "complete"]

    # Fill in regime number and sort
    log_data = util.fill_regime_num(log_data)
    log_data = log_data.sort_values(by=["regime_num", "exp_num"]).set_index(
        "regime_num", drop=False
    )

    # Print log summary
    log_summary = util.parse_blocks(log_data)
    if log_summary["task_params"].dropna().size:
        log_summary["task_params"] = log_summary["task_params"].apply(
            lambda x: x[:25] + "..." if len(x) > 25 else x
        )
    else:
        log_summary = log_summary.dropna(axis=1)

    print("Log summary:")
    print(
        tabulate(
            log_summary.set_index("regime_num", drop=True),
            headers="keys",
            tablefmt="psql",
        )
    )


if __name__ == "__main__":
    # Configure logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        run()
    except (RuntimeError, KeyError) as e:
        logger.exception(f"Error with validating logs: {e}")
