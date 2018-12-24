#!/user/bin/python
#This script will replace the HETATM part of one PDB file with the HETATM part of another PDB file, creating a new PDB file containing data for both.
import sys
import re
import os
import util
import argparse

def parse_args(sysargv=[]):
  parser = argparse.ArgumentParser()
  parser.add_argument("--before", metavar='FILE', type=str, default=None, action="store", help="file containing the PDB file whose HETATM lines should be replaced")
  parser.add_argument("--after", metavar='FILE', type=str, default=None, action="store", help="file containing the PDB file whose HETATM lines we want to use")
  parser.add_argument("--drug", type=str, default="", action="store", help="name of the drug in the HETATM lines of the after file")
  return(parser.parse_args())

def main(sysargv=[]):
  
  args = parse_args(sysargv)
  
  #open files to read
  to_be_replaced = util.get_file2(args.before, "r", "PDB")
  to_replace_with = util.get_file2(args.after, "r", "PDB")
  
  #open file to write
  newfilename = os.path.splitext(args.before)[0] + "_mod.pdb"
  newfile = util.get_file2(newfilename, "w", "PDB")
  
  index = -1
  #read through file whose HETATM lines we want to replace
  line = to_be_replaced.readline()
  while line:
    vals = re.findall("\S+", line)
    if re.match("HETATM", line) and len(vals[3]) >= 3: #lines to replace
      data = [vals[3], vals[4], vals[5]]
    else: #copy to file
      if index == -1:
        index = int(vals[1])
      else:
        index = index + 1
      arr = [vals[0], str(index)] + vals[2:]
      printline = util.format_pdb_line(arr)+"\n"
      newfile.write(printline)
    line = to_be_replaced.readline()

  #read through file whose HETATM lines we want to use
  line = to_replace_with.readline()
  while line:
    vals = re.findall("\S+", line)
    if re.match("HETATM", vals[0]): #HETATM line
      if (args.drug).lower() == vals[3].lower() or len(vals[3]) >= 3: #line contains the drug
        index = index + 1
        arr = [vals[0], str(index), vals[2]] + data + vals[6:]
        printline = util.format_pdb_line(arr)+"\n" #format the line for PDB
        newfile.write(printline)
    line = to_replace_with.readline()

  newfile.close()
  to_replace_with.close()
  to_be_replaced.close()

if __name__ == "__main__":
  main(sys.argv[1:])
