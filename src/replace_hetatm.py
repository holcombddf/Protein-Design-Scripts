#!/user/bin/python
import sys
import re
import os
import util

#function to determine whether or not line from PDB contains a metal
def is_metal(string):
  for s in ["MN", "FE", "CO", "NI", "CU", "ZN", "CA"]:
    if string.upper() == s.upper():
      return True
  return False

def main(sysargv=[]):
  
  #open files to read
  to_be_replaced = util.get_file2(sysargv[0], "r", "PDB")
  to_replace_with = util.get_file2(sysargv[1], "r", "PDB")
  
  #open file to write
  newfilename = os.path.splitext(sysargv[0])[0] + "_mod.pdb"
  newfile = util.get_file2(newfilename, "w", "PDB")
  
  #read through file whose HETATM lines we want to replace
  line = to_be_replaced.readline()
  while line:
    vals = re.findall("\S+", line)
    if re.match("HETATM", line):
      if is_metal(vals[3]): #write as usual
	newfile.write(line)
      else: #track the index, and the data
	index = int(vals[1])
	data = [vals[3], vals[4], vals[5]]
	break
    else: #copy to file
      newfile.write(line)
    line = to_be_replaced.readline()

  #read through file whose HETATM lines we want to use
  line = to_replace_with.readline()
  while line:
    vals = re.findall("\S+", line)
    if re.match("HETATM", vals[0]) and re.match("[A-Z]\d+", vals[2]): #write the new line
      arr = [vals[0], str(index), vals[2]] + data + vals[6:]
      printline = util.format_pdb_line(arr)+"\n" #format the line for PDB
      newfile.write(printline)
      index = index + 1
    line = to_replace_with.readline()

  newfile.close()
  to_replace_with.close()
  to_be_replaced.close()

if __name__ == "__main__":
  main(sys.argv[1:])