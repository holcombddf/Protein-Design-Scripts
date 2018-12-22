#!/usr/bin/python
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels
#Script can be given a third argument which is a column label to sort the values on

import sys
import os
import util
import threading
import argparse
import score_data_extractor
import csv_sorter_and_top_10

def run_scripts(subdir, headerlist=None, headers=None, sort_header=None):
  if headerlist is not None: #list of headers is given by user
    score_data_extractor.main([subdir, headerlist])
  elif headers is not None: #path to a list of headers is given by user
    score_data_extractor.main([subdir, headers])
  else:
    score_data_extractor.main([subdir])
    
  if sort_header is not None: #the column label to sort on is given by user
    csv_sorter_and_top_10.main([subdir, sort_header])
  else:
    csv_sorter_and_top_10.main([subdir])
    
def parse_args(sysargv=[]):
  parser = argparse.ArgumentParser()
  parser.add_argument("--directory", metavar='DIR', type=str, default=None, action="store", help="directory containing the subdirectories to process")
  parser.add_argument("--headerlist", metavar='FILE', type=str, default=None, action="store", help="file containing a list of column headers indicating which columns to extract")
  parser.add_argument("--headers", type=str, default=None, nargs='+', action="store", help="column header(s) indicating which columns to extract")
  parser.add_argument("--sortheader", type=str, default=None, action="store", help="column header to sort the spreadsheet data on")
  return(parser.parse_args())

def main(sysargv=[]):
  args = parse_args(sysargv)
  
  if args.directory is not None:
    directory = args.directory
  else:
    directory = os.getcwd()
  directory = os.path.join(directory, "")
  #run scripts in each subdirectory
  for subdir in [x[0] for x in os.walk(directory)]:
      subdir.strip()
      os.path.join(subdir, "")
      if os.path.isdir(subdir) and os.path.normpath(subdir) != os.path.normpath(directory):
	print(subdir)
	runargs=(subdir, args.headerlist, args.headers, args.sortheader,)
	t = threading.Thread(target=run_scripts, args=runargs)
	t.start()
      
if __name__ == "__main__":
  main(sys.argv[1:])
