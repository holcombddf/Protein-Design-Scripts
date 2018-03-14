#!/usr/bin/python
#This script will compare one or more PDB files to a reference PDB file, giving all edit mutations relative to the reference for each.
#Script takes as arguments a path to a PDB file to use as a reference for comparison, and a path to a list of paths of other PDB files to compare to the reference PDB
import sys
import re
import os

#utility function to print to both console and output file
def double_print(string, handle):
  print string
  handle.write(string + "\n")

ref_pdb = None
pdb_files = []

#open pdbs to compare
if len(sys.argv) > 1: #user gave the reference pdb
  ref_pdb = open(sys.argv[1], "r")
else:
  ref_pdb = open(raw_input("Please enter the path to the reference pdb: "), "r")

if len(sys.argv) > 3: #user gave the reference pdb, and a number of comparison pdbs
  for i in xrange(2,len(sys.argv)):
    pdb_files.append(open(sys.argv[i], "r"))
elif len(sys.argv) == 3: #user gave the reference pdb and a list of comparison pdbs to read
  #open the list of pdbs
  list_of_pdbs = open(sys.argv[2], "r")
  pdb_names = list_of_pdbs.readlines()
  list_of_pdbs.close()
  #open the pdb files
  for name in pdb_names:
    name = name.rstrip()
    pdb_files.append(open(name, "r"))
elif len(sys.argv) < 3: #user did not give any info on comparison pdbs
  file_name = raw_input("Please enter the path to a pdb to compare, or \"DONE\" to finish: ")
  while file_name.upper() != "DONE":
    pdb_files.append(open(file_name), "r")
    file_name = raw_input("Please enter the path to a pdb to compare, or \"DONE\" to finish: ")
    
#open an output file, using the name of the reference pdb
outfile = open(os.path.basename(ref_pdb.name) + "_changes_output.txt", "w")

#dictionary of arrays of changes, key is the PDB path/name
dif_dict = {}
#dictionary of data for the reference PDB, key is "A" or "B" and the line number 
ref_vals = {}

#read the data for the reference PDB
line = ref_pdb.readline()
while (line):
  lineparts = re.findall("\S+", line)
  if len(lineparts) > 5 and lineparts[0] == "ATOM":
    key = str(lineparts[4]) + str(lineparts[5])
    if key not in ref_vals: #line data is not already in the dictionary
      ref_vals[key] = lineparts[3]
  line = ref_pdb.readline()

#read and compare the data for the other PDBs
for pdb in pdb_files:
  dif = []
  line = pdb.readline()
  while (line):
    lineparts = re.findall("\S+", line)
    if len(lineparts) > 5 and lineparts[0] == "ATOM":
      key = str(lineparts[4]) + str(lineparts[5])
      if lineparts[3] != ref_vals[key]: #there's a difference to add
	difference = str(lineparts[5])+"\t"+str(ref_vals[key])+ "->" + str(lineparts[3])
	if (difference not in dif): #the difference is not in the array for this PDB
	  dif.append(difference)
    line = pdb.readline()
  dif_dict[pdb.name]=dif
  
double_print("Changes to " + os.path.basename(ref_pdb.name), outfile)
double_print("-------------------------------------------------", outfile)
ref_pdb.close()

#write the comparison data
for pdb in pdb_files:
  double_print(os.path.basename(pdb.name) + ": " + str(len(dif_dict[pdb.name])), outfile)
  for difference in dif_dict[pdb.name]:
    double_print(difference, outfile)
  double_print("", outfile)
  pdb.close()
outfile.close()