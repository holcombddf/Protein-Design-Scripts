#!/usr/bin/python
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels

import sys
import os
import re

def main(sysargv=[]):
  #list of indices of the columns we want to store
  INDICES = [0,1,4,5,36]

  ind_flag = False #indicator variable which determines whether or not to try to get the indices of the column labels
  labels = "name, " #first line to be constructed later, contains the labels

  #get the path to the directories
  if os.path.isdir(sysargv[0]):
      path = os.path.join(sysargv[0], "")
      directory = os.path.basename(os.path.dirname(path))
  else: 
    raise Exception("Directory containing score files not given.")
  #if user gives a list of column labels, read them
  if len(sysargv) > 1:
    try:
      indices_file = open(sysargv[1], "r")
      col_labels = indices_file.readlines()
      indices_file.close()
      ind_flag = True
    except Exception as e:
      print str(e)
      print "Error opening column index list. Reverting to default column indices."
      ind_flag = False
    
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
	      
	    #compare the desired labels to the actual labels to get the indices
	    if read_score == 1 and ind_flag:
	      INDICES = []
	      values = re.findall ("\S+", line)
	      for label in col_labels:
		for i, value in enumerate(values):
		  if (label.rstrip()).lower() == (value.rstrip()).lower():
		    INDICES.append(i-1)
	      ind_flag = False
	      
	    #read the labels
	    if read_score == 1 and labels == "name, ": #first time reading SCORE and labels
		values = re.findall ("\S+", line)
		for index in INDICES:
		  labels = labels + values[index+1] + ", "
		outfile.write(labels + "\n")
		
	    #read the values
	    elif read_score >= 2: #second time reading SCORE means we can read the numbers
		#find all floating point numbers in the line
		values = re.findall("\-?\d+\.\d+", line)
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
	
if __name__ == "__main__":
  main(sys.argv[1:])