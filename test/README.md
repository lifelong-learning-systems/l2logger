# Lifelong Learning Logger Tests

There are several unit tests available, in the `test_simple_logging.py` file

Run them simply by ensuring the virtual environment is active, then:
```
cd test
python test_simple_logging.py
```

## Test Summaries
- test_meta_files
    - ensures that the `colummn_metric_list.json` and `scenario_info.json`
      meta files are created and populated correctly in the scenario
      directory
- test_single_directory
    - performs a single `write_new_regime`, to test that the 
      directory structure is created appropriately
- test_stress_directory
    - performs many invocations of `write_new_regime`, to test that the 
      directory structure is created appropriately
- test_one_block
    - tests a single `write_new_regime` and several `write_to_data_log`,
    ensuring the `data-log.tsv` and `block-report.tsv` files are created
    - TODO: ensure the log files have the correct content as well