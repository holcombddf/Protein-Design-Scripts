#!/usr/bin/python
import sys
import os
import thread
import score_data_extractor
import csv_sorter_and_top_10

def run_scripts(subdir):
    os.system("python score_data_extractor.py " + subdir)
    os.system("python csv_sorter_and_top_10.py " + subdir)

if len(sys.argv) > 1:
  directory = sys.argv[1]
else:
  directory = os.getcwd()

#run scripts in each subdirectory
for subdir in os.listdir(directory):
    if os.path.isdir(subdir):
      thread.start_new_thread(run_scripts, subdir)
      