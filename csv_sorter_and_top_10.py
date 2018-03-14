#!/usr/bin/python
#Script should have an argument containing the path to a directory containing a csv (.csv) of all collected score data
#Otherwise, it uses the current directory
#Script is designed to be used after score_data_extrator.py

import sys
import os

#the column to sort the lines on
COL = 1
#the number of rows in the output
NUM = 10

path = ""
directory = ""
if len(sys.argv) > 1:
  path = sys.argv[1]
  directory = os.path.basename(os.path.dirname(sys.argv[1]))

infile = open(path + directory + "_collected_scores.csv", "r")
outfile = open(path + "sorted_" + directory + "_collected_scores.csv", "w")

file_lines = infile.readlines()

#write the first row, the labels
outfile.write(file_lines[0])
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
  max_lines.append(file_lines[max_index]) 
  del file_lines[max_index]
  
#write the lines
for line in max_lines:
  outfile.write(line)
infile.close()
outfile.close()