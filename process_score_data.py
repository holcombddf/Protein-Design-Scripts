#!/usr/bin/python
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
import sys
import os
import threading
import score_data_extractor
import csv_sorter_and_top_10

def run_scripts(subdir):
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
      t = threading.Thread(target=run_scripts, args=(subdir,))
      t.start()