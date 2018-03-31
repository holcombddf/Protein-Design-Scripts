#!/bin/python
#Removes all files with an extension in ext_array from directory and all recursive subdirectories.
import os
import sys

#recursively process each subdirectory
def rec_del(directory,ext_array):
  for f in os.listdir(directory):
    f = os.path.join(directory,f)
    if f.endswith(".git"): #ignore
      continue
    elif os.path.isdir(f): #recurse
      rec_del(f,ext_array)
    else: #check if the file is a removable filetype
      delflag = False
      for ext in ext_array:
	delflag = delflag or f.endswith(ext)
      if delflag:
	print "Removing "+f
	os.remove(f)
	
def main(sysargv=[]):
  if len(sysargv) > 0:
    directory = sysargv[0]
  else:
    directory = "/home/david_holcomb/Workspace/Protein-Design-Scripts"
  if len(sysargv) > 1:
    ext_array = sysargv[1:]
  else:
    ext_array = [".pyc", ".csv", ".log", ".pdf", ".rtf", ".png"]

  rec_del(directory, ext_array)

if __name__ == "__main__":
  main(sys.argv[1:])