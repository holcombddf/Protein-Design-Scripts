#!/usr/bin/python
#This script contains utility functions used by other scripts
import os
import re
import gzip

#for opening and reading GZ files
def openfile(filename, mode="r"):
  ext = os.path.splitext(filename)[-1]
  if ext == ".gz":
    return gzip.open(filename, mode)
  else:
    return open(filename, mode)

#open file
def get_file(sysargv, index=0, mode="r", filetype=""): 
  if len(sysargv) > index: #user gave the reference PDB
    path = sysargv[index]
  else:
    path = raw_input("Please enter the path to the "+filetype+" file: ")
  read_file = openfile(path, mode)
  return read_file

#open a list of files
def get_file_list(sysargv, index=2, mode="r", filetype=""):
  filenames = []
  if len(sysargv) > index: #user gave multiple files
    filenames = sysargv[index-1:]
  elif len(sysargv) == index: #user gave a list of files
    list_of_files = openfile(sysargv[index-1], mode)
    filenames = list_of_files.readlines()
    list_of_files.close()
  elif len(sysargv) < index: #user did not give any file info
    name = raw_input("Please enter the path to a "+filetype+" file, or \"DONE\" to finish: ")
    while name.upper() != "DONE":
      filenames.append(name)
    name = raw_input("Please enter the path to a "+filetype+" file, or \"DONE\" to finish: ")
  files = []
  for f in filenames:
    f = f.rstrip()
    files.append(openfile(f, mode))
  return files
    
#print to both console and output file
def double_print(string, handle):
  print string
  handle.write(string + "\n")
  
def extract_score_data(filelist, outfile, INDICES, col_labels, labels):
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
	  if read_score == 1 and (len(col_labels) > 0):
	    INDICES = []
	    values = re.findall ("\S+", line)
	    for label in col_labels:
	      for i, value in enumerate(values):
		if (label.rstrip()).lower() == (value.rstrip()).lower():
		  INDICES.append(i-1)
	    
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