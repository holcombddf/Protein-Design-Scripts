#!/usr/bin/python
#Script should have an argument containing the path to a directory containing score (.sc) files
#Otherwise, it uses the current directory

import sys
import re
import os

def main(sysargv=[]):
  #list of indices of the columns we want to store
  INDICES = [0,1,4,5,36]

  labels = "name, "

  #get the path and directory to work in
  path = ""
  directory = ""
  if len(sysargv) >= 1:
    path = sysargv[0]
    directory = os.path.basename(os.path.dirname(sysargv[0]))

  #create array of files
  filelist = []	
  filelist = os.popen("ls " + path + "*.sc", "r")

  outfile = open(path + directory + "_collected_scores.csv", 'w')

  #read each file
  for file_name in filelist:
      file_name = file_name.rstrip()
      infile = open(file_name, 'r')
      
      #read through file
      read_score = 0;
      line = infile.readline()
      while line:
	  line.rstrip()
	  if re.match("SCORE:",line):
	    read_score = read_score + 1
	    
	  #read the labels
	  if read_score == 1 and labels == "name, ": #first time reading SCORE and labels
	      values = re.findall ("\S+", line)
	      for index in INDICES:
		labels = labels + values[index+1] + ", "
	      outfile.write(labels + "\n")
	      
	  #read the values
	  elif read_score >= 2: #second time reading SCORE means we can read the numbers
	      #find all floating point numbers in the line
	      values = re.findall("-?\d+\.\d+", line)
	      if len(values) > max(INDICES):#check that we have enough numbers in the line to match the indicies
		#write name of file (after removing path)
		outfile.write(os.path.basename(file_name) + ", ")
		#write the desired data to the output file
		for i in INDICES:
		  outfile.write(values[i] + ", ")
		  
		#sum_val = float(values[4]) + float(values[5]) + float(values[36])
		#outfile.write(str(sum_val))
		
		#write newline to end row
		outfile.write("\n")
			
	      else:
		raise Exception("There aren't enough numerical columns in " + line + "\nfrom file " + file_name)
	  line = infile.readline()
      infile.close()
      
  outfile.close()

if __name__ == "__main__":
  main(sys.argv[1:])