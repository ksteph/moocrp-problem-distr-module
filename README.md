# moocrp-problem-distr-module
MoocRP module for displaying each edX MOOC problem's max attempt, grade, and normalized grade distribution.

# Preprocessing
If preprocessing is not done this module will simply show the test.js data seen in the main directory.

In the preprocess folder there are two scripts and a folder.
* `generate_json.py` - Generates the json for the graphs, from the MOOC's `course_structure.json` and log file.
* `run_tests.py` - This tests `generate_json.py`
* `test` - Contains all the files `run_tests.py` needs

## generate_json.py
Just running this script will print out help information.

Usage: `./preprocess/generate_json.py edX_course_structure.json edX_log_file output_header`

Parses through `edX_log_file` to generate the json needed to render three graphs per problem: attempt distribution, grade distribution count, grade distribution fraction.

Needs `edX_course_structure.json` so the problems are ordered by how they appear in the content.

This script takes three parameters:

1. `edX_course_structure.json` - edX json that gives the course structure
2. `edX_log_file` - edX csv log file
3. `output_header` - used for output files

This script outputs two files:

1. `output_header.log` - script prints progress and errors to this file along with summary info at the bottom
2. `output_header.json` - json file holding all data needed to render the graphs

### Example
Let's assume your course structure json was named TEST_structure_original.json and the log file was TEST.csv. And the javascript code one folder up expects the file containing the data to be data.json you would run:

`./generate_json.py TEST_structure_original.json TEST.csv ../data`

## run_tests.py
This is the current set of tests for `generate_json.py` as bugs are found or functionally changed, this will also be updated.

To get help information run `./run_tests.py -help`