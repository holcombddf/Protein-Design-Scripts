#!/usr/bin/python
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels
#Script can be given a third argument which is a column label to sort the values on

import sys
import os
import util
import threading
import score_data_extractor
import csv_sorter_and_top_10

def run_scripts(subdir, labels=None, sort_label=None):
  if labels is not None: #path to a list of labels is given by user
    score_data_extractor.main([subdir, labels])
  else:
    score_data_extractor.main([subdir])
  if sort_label is not None: #the column label to sort on is given by user
    csv_sorter_and_top_10.main([subdir, sort_label])
  else:
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
      elif len(sys.argv) == 3:
	t = threading.Thread(target=run_scripts, args=(subdir, sys.argv[2],))
      elif len(sys.argv) > 3:
	t = threading.Thread(target=run_scripts, args=(subdir, sys.argv[2], sys.argv[3]))
      t.start()