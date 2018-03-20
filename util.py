#!/usr/bin/python
#This script contains utility functions used by other scripts
import os
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