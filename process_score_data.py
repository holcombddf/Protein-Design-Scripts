#!/usr/bin/python
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels

import sys
import os
import threading
import score_data_extractor
import csv_sorter_and_top_10

def run_scripts(subdir, labels=None):
  if labels is not None:
    score_data_extractor.main([subdir, labels])
  else:
    score_data_extractor.main([subdir])
  csv_sorter_and_top_10.main([subdir])

if len(sys.argv) > 1:
  directory = sys.argv[1]
else:
  directory = os.getcwd()
#run scripts in each subdirectory
for subdir in [x[0] for x in os.walk(directory)]:
    subdir.strip()
    os.path.join(subdir, "")
    if os.path.isdir(subdir) and os.path.normpath(subdir) != os.path.normpath(directory):
      if len(sys.argv) <= 2:
	t = threading.Thread(target=run_scripts, args=(subdir,))
      elif len(sys.argv) > 2:
	t = threading.Thread(target=run_scripts, args=(subdir, sys.argv[2],))
      t.start()