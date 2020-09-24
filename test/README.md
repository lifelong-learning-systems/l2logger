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
- test_meta_files_default
    - ensures that the `colummn_metric_list.json` and `scenario_info.json`
      meta files are created and populated correctly in the scenario
      directory when using the default parameters
- test_single_directory
    - performs a single `write_new_regime`, to test that the 
      directory structure is created appropriately
- test_stress_directory
    - performs many invocations of `write_new_regime`, to test that the 
      directory structure is created appropriately
- test_one_block
    - tests a single `write_new_regime` and several `write_to_data_log`,
    ensuring the `data-log.tsv` and `block-info.tsv` files are created, with
    the correct content
- test_many_blocks
    - same as `test_one_block`, but 80 regimes and 100 experiences per regime
- test_stress_blocks
    - same as `test_one_block`, but 20,000 regimes and 5 experiences per
    regime
- test_stress_data
    - same as `test_one_block`, but 200 regimes and 500 experiences per
    regime; distributed among 100 "workers" (copies of logger object)