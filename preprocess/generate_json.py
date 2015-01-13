#!/usr/bin/env python

###########
# Imports #
###########
import ast
import calendar
import csv
import datetime
import json
import subprocess
import sys
import time

from collections import defaultdict
from collections import namedtuple


####################
# Helper functions #
####################
def logTo(output, strLog):
  if True: #"DEBUG" not in strLog:
    output.write("{0}\t{1}\n".format(time.time(), strLog))

def edxLogConvertTimestamp(strTimestamp):
  timestamp = None
  timestampParts = strTimestamp.partition(".")

  try:
    timestampStruct = time.strptime(timestampParts[0], "%Y-%m-%dT%H:%M:%S")
    decimalStr = timestampParts[2] if (len(timestampParts[2]) > 0) else "0"
    timestamp = calendar.timegm(timestampStruct) + float("." + decimalStr)
  except ValueError as e:
    timestamp = None

  return timestamp


###############################
# Check input and helper text #
###############################
minArgLen = 4
maxArgLen = minArgLen
if minArgLen > len(sys.argv) or len(sys.argv) > maxArgLen:
  print " Usage:", sys.argv[0], "<edX course_structure.json> <edX Log File> <output header>\n"
  print """
  Parses through <edX Log File> to generate the json needed to render three
  graphs per problem: attempt distribution, grade distribution count, grade
  distribution fraction.

  Needs <edX course_structure.json> so the problems are ordered by how they
  appear in the content.

  Files generated, starts with <output header>:
   *.log  - script prints progress and errors to this file along with summary info
           at the bottom
   *.json - json file holding all data needed to render the graphs.
"""
  sys.exit(1)


#################
# Process input #
#################
i = 1
# inputFlags = ""
# if len(sys.argv) == maxArgLen:
#   inputFlags = sys.argv[i]
#   i += 1
inputCourseStructFilename = sys.argv[i]
i += 1
inputLogFilename = sys.argv[i]
i += 1
outputHeader = sys.argv[i]


#############################
# Header of output log file #
#############################
startTime = time.time()
outLog = open(outputHeader + ".log", "w", 0)
logTo(outLog, "COURSE_STRUCTURE_FILENAME: " + inputCourseStructFilename)
logTo(outLog, "LOG_FILENAME: " + inputLogFilename)

cmd = "wc -l {}| awk '{{print $1}}'".format(inputLogFilename)
fileLen = int(subprocess.check_output(cmd, shell=True))
logTo(outLog, "FILE_LENGTH: {}".format(fileLen))


##################
# Main Variables #
##################
StuProb = namedtuple("StuProb", "student problem")
Event = namedtuple("Event", "timestamp attempt score")

dictProb2Data = defaultdict(lambda: {"index": -1, "maxPoints": -1})

dictStuProb2Data = defaultdict(lambda: {
    "aryEvent": [],
    "hasAttempt": defaultdict(lambda: False),
    "isDup": False,
    })

dictProb2MaxAttempt2Count = defaultdict(lambda: defaultdict(lambda: 0))
dictProb2Attempt2GradeCount = defaultdict(lambda: defaultdict(lambda: 0))
dictProb2Attempt2Score2Count = defaultdict(
  lambda: defaultdict(lambda: defaultdict(lambda: 0)))

cStuProbDupAttempt = 0
cStuProbMissingAttempt = 0
cStuProbOutOfOrderAttempt = 0
cStuProbGood = 0


##############################
# Process course_struct.json #
##############################
def traverseCourseTree(currEdxId, dictTree, currProbCount, dictProb2Data):
  currNode = dictTree[currEdxId]
  if currNode["category"] == "problem":
    dictProb2Data[currEdxId]["index"] = currProbCount
    currProbCount += 1
  elif len(currNode["children"]) > 0:
    for child in currNode["children"]:
      currProbCount = traverseCourseTree(
        child, dictTree, currProbCount, dictProb2Data)

  return currProbCount

# Load json #
inputCourseStruct = open(inputCourseStructFilename, 'r')
dictCourseStruct = json.load(inputCourseStruct)
inputCourseStruct.close()

# Find top of the tree "category"=="course" #
edxIdCourse = None
for edxId, data in dictCourseStruct.iteritems():
  if data["category"] == "course":
    edxIdCourse = edxId

if edxIdCourse is None:
  logTo(outLog, "ERROR: Can't find top of course structure tree.")
  print "ERROR: Check log for what happened"
  sys.exit(1)

# Traverse tree to get problem indices #
logTo(outLog, "EDX_ID_COURSE:" + edxIdCourse)
traverseCourseTree(edxIdCourse, dictCourseStruct, 0, dictProb2Data)


####################
# Process CSV file #
####################
cLine = 0
bLastLine = False
inputLogFile = open(inputLogFilename, 'r')
csvReader = csv.reader(inputLogFile)
for row in csvReader:
  cLine += 1

  if cLine % 5000 == 0:
    logTo(outLog, "LINES_PROCESSED:{:d}_({:.2f})%".format(cLine, ((cLine*100.0)/fileLen)))

  if len(row) != 13:
    logTo(outLog, "LINE_NOT_13_CELLS:{}\t{}".format(cLine, row))
  elif row[0] == "time": #Header row
    continue
  else:
    # Clean a Data #
    timestamp = edxLogConvertTimestamp(row[0])
    student = row[2]
    verb = row[3]
    event = ast.literal_eval(row[9])

    if timestamp == None:
      logTo(outLog, "TIME_NOT_PARSE\tLINE_{}\t{}".format(cLine, row[0]))
      continue # not useful if don't have time

    # Only verb we currently care about is the one when student chooses an
    # answer and submits it
    if verb == "problem_check":
      probId = event["problem_id"]
      attempt = event["attempts"]
      answers = event["answers"]

      currStuProb = StuProb(student, probId)
      currStuProbData = dictStuProb2Data[currStuProb]

      # Check if it's a bad StuProb #
      if currStuProbData["isDup"]:
        continue # If it's had a duplicate, don't count data

      if currStuProbData["hasAttempt"][attempt]: # Duplicate!
        currStuProbData["isDup"] = True
        cStuProbDupAttempt += 1
        logTo(outLog,
              "DUPLICATE_ATTEMPT_IGNORE_ALL_EVENTS_OF_STU_PROB:\t{}\t{}".format(
            student, probId))

        # Free up memory, no point in keeping data around
        currStuProbData["hasAttempt"] = None
        currStuProbData["aryEvent"] = None
        continue

      # Get Score #
      score = 0
      for probPartId, probPart in event["correct_map"].iteritems():
        if probPart["correctness"] == "correct":
          score += 1

      currStuProbData["hasAttempt"][attempt] = True
      currStuProbData["aryEvent"].append(Event(timestamp, attempt, score))

    # Close: if verb == "problem_check":
  # Close: if len(row) != 13: else:
# Close: for row in csvReader:
inputLogFile.close()


###########################
# Count things for graphs #
###########################
for currStuProb, currStuProbData in dictStuProb2Data.iteritems():
  if currStuProbData["isDup"]:
    continue

  currProb = currStuProb.problem
  aryAttempt = currStuProbData["hasAttempt"].keys()
  maxAttempt = max(aryAttempt)

  # Check if have missing attempts #
  if maxAttempt != len(aryAttempt):
    # We have missing attempts!
    cStuProbMissingAttempt += 1
    logTo(outLog,
          "MISSING_ATTEMPT_IGNORE_ALL_EVENTS_OF_STU_PROB:\t{}\t{}".format(
        student, probId))
    continue

  # Check if attempts are out of order #
  aryEventOrdered = currStuProbData["aryEvent"]
  aryEventOrdered.sort(cmp=lambda x,y: cmp(x.timestamp, y.timestamp))

  prevAttempt = aryEventOrdered[0].attempt
  isOutOfOrder = False
  for x in range(len(aryEventOrdered)-1):
    i = x+1
    if prevAttempt > aryEventOrdered[i].attempt:
      # Out of order!
      isOutOfOrder = True
      break

  if isOutOfOrder:
    cStuProbOutOfOrderAttempt += 1
    logTo(outLog,
          "OUT_OF_ORDER_ATTEMPT_IGNORE_ALL_EVENTS_OF_STU_PROB:\t{}\t{}".format(
        student, probId))
    continue

  # Made it through the checks, so this StuProb is good, process it #
  cStuProbGood += 1

  dictProb2MaxAttempt2Count[currProb][maxAttempt] += 1

  for event in currStuProbData["aryEvent"]:
    if event.score > dictProb2Data[currProb]["maxPoints"]:
      dictProb2Data[currStuProb.problem]["maxPoints"] = event.score
  
    attempt = event.attempt
    dictProb2Attempt2GradeCount[currProb][attempt] += 1
    dictProb2Attempt2Score2Count[currProb][attempt][event.score] += 1


#####################
# Check the numbers #
#####################
bNumCheckPass = True
def alertNumCheckFail(strOut):
  strLog = "NUM_CHECK_FAIL-{}\n".format(strOut)
  logTo(outLog, strOut)

cStuProbCheck = len(dictStuProb2Data)
totalStuProb = cStuProbDupAttempt + cStuProbMissingAttempt + cStuProbOutOfOrderAttempt + cStuProbGood

if cStuProbCheck != totalStuProb:
  bNumCheckPass = False
  strOut = "STU_PROB_COUNT_NOT_MATCH_TOTAL_STU_PROB:\t{}\t{}".format(
    cStuProbCheck, cStuProbCmd)
  alertNumCheckFail(strOut)

if not bNumCheckPass:
  print "##### A_NUM_CHECK_HAS_FAILED #####"


####################
# Create json file #
####################
aryJsonData = []
aryProbItems = dict(dictProb2Data).items()
aryProbItems.sort(cmp=lambda x,y: cmp(x[1]["index"], y[1]["index"]))

for edxId, probData in aryProbItems:
  aryAttemptData = []
  aryGradeData = []
  aryGradeCountData = []

  # Check if this problem has data, if not just create an empty entry
  if edxId in dictProb2MaxAttempt2Count:
    aryAttempt = dict(dictProb2MaxAttempt2Count[edxId]).keys()
    maxAttempt = max(aryAttempt)

    # Go through all possible attempts, so have zero entries where appropriate
    for i in range(maxAttempt):
      attempt = i + 1 # Attempts not zero based

      # Attempt Distribution #
      cMaxAttempt = dictProb2MaxAttempt2Count[edxId][attempt]
      aryAttemptData.append({
        "stackData": [{
            "color": 0,
            "tooltip": "{} student(s) had {} attempt(s)".format(
              cMaxAttempt, attempt),
            "value": cMaxAttempt,
            }],
        "xValue": attempt,
        })

      # Grade Distribution #
      aryGradeStackData = []
      aryGradeCountStackData = []
      cAttempt = dictProb2Attempt2GradeCount[edxId][attempt]
      maxPoints = dictProb2Data[edxId]["maxPoints"]
      # Do all possible points, so have zero entries where appropriate
      for scoreTmp in range(maxPoints+1):
        score = maxPoints - scoreTmp
        cScore = dictProb2Attempt2Score2Count[edxId][attempt][score]

        percent = 0.0
        if cAttempt > 0:
          percent = (cScore*1.0)/cAttempt

        grade = 0.0
        if maxPoints > 0:
          grade = (score*100.0)/maxPoints

        aryGradeStackData.append({
            "color": grade,
            "tooltip": "[{}/{}] ({:.3f}) student(s) scored [{}/{}] in attempt {}".format(
              cScore, cAttempt, percent, score, maxPoints, attempt),
            "value": percent,
            })

        aryGradeCountStackData.append({
            "color": grade,
            "tooltip": "[{}/{}] ({:.3f}) student(s) scored [{}/{}] in attempt {}".format(
              cScore, cAttempt, percent, score, maxPoints, attempt),
            "value": cScore,
            })
      # Close: for scoreTmp in range(maxPoints+1):

      aryGradeData.append({
          "stackData": aryGradeStackData,
          "xValue": attempt,
          })

      ## Grade Count Distribution ##
      aryGradeCountData.append({
          "stackData": aryGradeCountStackData,
          "xValue": attempt,
          })

    # Close: for i in range(maxAttempt):
  # Close: if edxId in dictProb2MaxAttempt2Count:
  
  aryJsonData.append({
      "problem_id": edxId,
      "attempt_data": aryAttemptData,
      "grade_data": aryGradeData,
      "grade_count_data": aryGradeCountData,
      })

# Close: for edxId, probData in aryProbItems:


outData = open(outputHeader + ".json", "w", 0)
json.dump(aryJsonData, outData, indent=2)
outData.write("\n")
outData.close()


#############################
# Footer of output log file #
#############################
endTime = time.time()
elapseTime = endTime - startTime
strLog = """DONE
==========================
ELAPSE_TIME: {}
==========================
LINES_PROCESSED: {}
==========================
STUDENT_PROBLEMS_WITH_DUPS_ATTEMPTS: {}
STUDENT_PROBLEMS_WITH_MISSING_ATTEMPTS: {}
STUDENT_PROBLEMS_WITH_OUT_OF_ORDER_ATTEMPTS: {}
STUDENT_PROBLEMS_THAT_ARE_GOOD: {}
==========================""".format(
  str(datetime.timedelta(seconds=elapseTime)),

  cLine,
  
  cStuProbDupAttempt,
  cStuProbMissingAttempt,
  cStuProbOutOfOrderAttempt,
  cStuProbGood,
  )
logTo(outLog, strLog)

outLog.close()

if not bNumCheckPass:
  sys.exit(1)
