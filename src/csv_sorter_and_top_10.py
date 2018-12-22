#!/usr/bin/python
#Script should have an argument containing the path to a directory containing a CSV (.csv) of all collected score data
#Otherwise, it uses the current directory
#Can be given a second argument, which is the label of the column to sort on
#Script is designed to be used after score_data_extrator.py

import sys
import os
import re
import util

def main(sysargv=[]):
  #the column to sort the lines on
  COL = 1
  #the number of rows in the output
  NUM = 10
  #indicator variable which determines whether or not to try to get the index of the column to sort on
  ind_flag = False

  if os.path.isdir(sysargv[0]): #for use after process_score_data.py, which produces [directory]_collected_scores.csv
    path = os.path.join(sysargv[0], "")
    directory = os.path.basename(os.path.dirname(path))
    infile = open(path + directory + "_collected_scores.csv", "r")
    outfile = open(path + "sorted_" + directory + "_collected_scores.csv", "w")
  elif os.path.isfile(sysargv[0]): #for general purpose use, can be used on any CSV-formatted file
    path = os.path.join((os.path.dirname(sysargv[0])), "")
    filename = os.path.basename(sysargv[0])
    infile = open(sysargv[0], "r")
    outfile = open(path + "sorted_" + filename, "w")
  else:
    print("Can't find file or directory to process.")

  #read the file_lines
  file_lines = infile.readlines()
  #write the first row, the labels
  util.double_print((file_lines[0]).rstrip(), outfile)
  
  #search the labels for the index of the given label
  if len(sysargv) > 1:
    values = re.findall ("\S+", file_lines[0])
    for i, value in enumerate(values):
      value = value.rstrip()
      value = value.rstrip(',')
      if (sysargv[1].rstrip()).lower() == value.lower():
	COL = i
    
  #delete the labels, so we can sort on values
  del file_lines[0]

  max_lines = [];
  #find the lines with the NUM largest values in the COL column
  for i in xrange(0, NUM):
    if not file_lines:
      break
    max_val = 0
    max_index = len(file_lines)+1
    #find line with the largest value in the COL column
    for i, line in enumerate(file_lines):
      values = line.split(',')
      if (values[COL] > max_val or max_index > len(file_lines)):
	    max_val = values[COL]
	    max_index = i
    #add line with largest value to return array and remove from search array
    max_lines.append((file_lines[max_index]).rstrip()) 
    del file_lines[max_index]
    
  #write the lines
  for line in max_lines:
    util.double_print(line, outfile)
  infile.close()
  outfile.close()

if __name__ == "__main__":
  main(sys.argv[1:])
