#!/usr/bin/env python

import subprocess
import sys
import time

from subprocess import CalledProcessError

strOutHeader = "test/tmp"

if len(sys.argv) > 3 or (len(sys.argv) == 2 and sys.argv[1] == "-help"):
  print " Usage:", sys.argv[0], "OPTIONS\n"
  print """
  Parses the raw data from input file and puts it in the database.

  Options:
   -l - Last test only
   -help - This content
   -t n - Run only the nth test, 0-based indexing.
"""
  sys.exit(0)

bLastTest = False
bSpecificTest = False

iTest = -1
if len(sys.argv) == 2:
  bLastTest = 'l' in sys.argv[1]
elif len(sys.argv) == 3:
  bSpecificTest = 't' in sys.argv[1]
  iTest = int(sys.argv[2])

aryAllTests = [
  {
    "name": "generate_json.py: Simple",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/simple_course_struct.json",
      "test/input/genJson_simple.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_simple.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Simple and event with different verb",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/simple_course_struct.json",
      "test/input/genJson_simple_diffVerb.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_simple.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Simple and events with bad timestamp",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/simple_course_struct.json",
      "test/input/genJson_simple_badTimestamp.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_simple.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Simple and event with too many cells",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/simple_course_struct.json",
      "test/input/genJson_simple_tooManyCells.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_simple.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Simple and event with too many cells",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/simple_course_struct.json",
      "test/input/genJson_simple_tooFewCells.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_simple.txt",
    "noDB": True,
  },
  #05
  {
    "name": "generate_json.py: Complex",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/complex_course_struct.json",
      "test/input/genJson_complex.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_complex.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Complex with duplicate attempt for a student problem",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/complex_course_struct.json",
      "test/input/genJson_complex_dupStuProb.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_complex.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Complex with missing attempt for a student problem",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/complex_course_struct.json",
      "test/input/genJson_complex_missingStuProb.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_complex.txt",
    "noDB": True,
  },
  {
    "name": "generate_json.py: Complex with out of order attempt for a student problem",
    "cmd": "./generate_json.py {} {} {}".format(
      "test/input/complex_course_struct.json",
      "test/input/genJson_complex_outOfOrderStuProb.csv",
      strOutHeader),
    "outputForDiff": strOutHeader+".json",
    "expectedOut": "test/output/gj_complex.txt",
    "noDB": True,
  },
]

i=0
for test in aryAllTests:
  test["i"] = i
  i+=1

aryTests = []

if bLastTest:
  aryTests.append(aryAllTests[-1])
elif bSpecificTest:
  aryTests.append(aryAllTests[iTest])
else:
  aryTests = aryAllTests


for test in aryTests:
  print "Testing #{:02d}: {}".format(test["i"], test["name"])

  ## Run test ##
  #print "  Run: {}".format(test["cmd"])
  returncode = subprocess.call(test["cmd"], shell=True)
  if returncode != 0:
    print "BAD RETURN CODE {} WHEN RUN SCRIPT {}".format(returncode, test["cmd"])
    sys.exit(1)
    
  ## Test if expected file matches dumped database ##
  outputForDiff = test["outputForDiff"]

  cmd = "diff {} {}".format(outputForDiff, test["expectedOut"])
  returncode = subprocess.call(cmd, shell=True)

  if returncode == 0:
    print "  PASS"
  else:
    print "  FAIL"
    print "    Return code: {} ({})".format(returncode, "Files don't match" if returncode == 1 else "ERROR")
    print "    {}".format(test["cmd"])
    print "    {}".format(cmd)
    sys.exit(-1)

if bLastTest:
  print "LAST TEST PASSES! NOW TEST THEM ALL."
elif bSpecificTest:
  print "TEST #{} PASSES! NOW TEST THEM ALL.".format(iTest)
else:
  print "ALL TESTS PASS!"
