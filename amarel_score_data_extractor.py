#!/usr/bin/python
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels

import sys
import os
import re
import util

def main(sysargv=[]):
  #list of indices of the columns we want to store
  INDICES = [0,1,4,5,36]
  col_labels = []

  ind_flag = False #indicator variable which determines whether or not to try to get the indices of the column labels
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
    
  #create array of subdirectories
  arr = os.listdir(path)
  dirlist = []
  for subdir in arr:
    if re.match("job\d+", subdir, re.IGNORECASE):
      dirlist.append(subdir)

  #open the file to write to
  outfile = open(path + directory + "_collected_scores.csv", 'w')

  #iterate over subdirectories
  for subdir in dirlist:
    #create array of files
    subdir = os.path.join(subdir, "")
    filelist = []	
    filelist = os.popen("ls " + path + subdir + "*.sc", "r")

    util.extract_score_data(filelist, outfile, INDICES, col_labels, labels)
	
if __name__ == "__main__":
  main(sys.argv[1:])