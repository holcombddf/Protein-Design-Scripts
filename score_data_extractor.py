#!/usr/bin/python
#Script should have an argument containing the path to a directory containing score (.sc) files
#Script can be given a second argument, which is a file containing a list of column labels

import sys
import re
import os
import util

def main(sysargv=[]):
  #list of indices of the columns we want to store
  INDICES = [0,1,4,5,36]
  col_labels = []

  labels = "name, " #first line to be constructed later, contains the labels

  #get the path and directory to work in
  if os.path.isdir(sysargv[0]):
    path = os.path.join(sysargv[0], "")
    directory = os.path.basename(os.path.dirname(path))
  else: 
    raise Exception("Directory containing score files not given.")
  
  #if user gives a list of column labels, read them
  try:
    if len(sysargv) == 2:
      indices_file = util.openfile(sysargv[1], "r")
      col_labels = indices_file.readlines()
      indices_file.close()
    if len(sysargv) > 2:
      col_labels = sysargv[1:]
  except Exception as e:
    print str(e)
    print "Error opening column index list. Reverting to default column indices."
    col_labels = []

  #create array of files
  filelist = []	
  filelist = os.popen("ls " + path + "*.sc", "r")

  outfile = open(path + directory + "_collected_scores.csv", 'w')

  #read each file
  util.extract_score_data(filelist, outfile, INDICES, col_labels, labels)

if __name__ == "__main__":
  main(sys.argv[1:])