#!/usr/bin/python
#This script will convert a PDB file to a RES file
#Script takes a path to a PDB file to convert, as an argument
import sys
import re
import os
import util

def main(sysargv):
  #open PDB to convert 
  pdb_file = util.get_file(sysargv, 0, "r", "PDB")
  #open the RES file, using the name of the PDB
  res_file = open(os.path.splitext(pdb_file.name)[0] + ".res", "w")

  line_dict = {}
  #read the PDB data
  pdb_lines = pdb_file.readlines()
  for line in pdb_lines:
    if re.match("ATOM", line) or re.match("HETATM", line):
      cols = re.findall("\S+", line) #does not find the right columns when there is no whitespace separating them
      try:
        key = (cols[4],int(cols[5]))
        if key not in line_dict:
          line_dict[key] = "NATAA"
      except:
        pass
    
  #write data to RES file
  res_file.write("USE_INPUT_SC\nEX 1 EX 2\nstart\n")
  for key in sorted(line_dict.keys()):
    line = str(key[1]).rjust(4)+key[0].rjust(3)+"  "+line_dict[key]+"\n"
    res_file.write(line)
  
  pdb_file.close()
  res_file.close()

if __name__ == "__main__":
  main(sys.argv[1:])
