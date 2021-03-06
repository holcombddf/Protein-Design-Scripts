#!/usr/bin/python
#This script will compare one or more PDB files to a reference PDB file, giving all edit mutations relative to the reference for each.
#Script takes as arguments a path to a PDB file to use as a reference for comparison, and a path to a list of paths of other PDB files to compare to the reference PDB
import sys
import re
import os
import util
import threading
import argparse

def find_dif(ref_vals, dif_dict, pdb):
  #read and compare the data for the other PDBs
  dif = []
  line = pdb.readline()
  while (line):
    lineparts = re.findall("\S+", line)
    if len(lineparts) > 5 and lineparts[0] == "ATOM":
      key = (lineparts[4], int(lineparts[5]))
      if lineparts[3] != ref_vals[key]: #there's a difference to add
        difference = str(lineparts[5])+"\t"+str(ref_vals[key])+ "->" + str(lineparts[3])
        if (difference not in dif): #the difference is not in the array for this PDB
          dif.append(difference)
    line = pdb.readline()
  dif_dict[pdb.name]=dif
  
def parse_args(sysargv=[]):
  parser = argparse.ArgumentParser()
  parser.add_argument("--ref", metavar='FILE', type=str, default=None, action="store", help="reference PDB file to compare all other PDB files to")
  parser.add_argument("--pdblist", metavar='FILE', type=str, default=None, action="store", help="file containing a list of PDB files to compare to the reference")
  parser.add_argument("--pdbs", metavar='FILE', type=str, default=None, nargs='+', action="store", help="PDB file(s) to compare to the reference")
  return parser.parse_args()

def main(sysargv=[]):
  args = parse_args(sysargv)
  
  ref_pdb = None
  pdb_files = []

  #open PDBs to compare
  if args.ref is not None:
    ref_pdb = util.get_file2(args.ref, "r", "PDB")
  if args.pdblist is not None:
    pdb_files.extend(util.get_file_list2(args.pdblist, "r", "PDB"))
  if args.pdbs is not None:
    pdb_files.extend(util.get_file_list2(args.pdbs, "r", "PDB"))
      
  #open an output file, using the name of the reference PDB
  outfile = open(os.path.splitext(ref_pdb.name)[0] + "_changes_output.txt", "w")

  #dictionary of arrays of changes, key is the PDB path/name
  dif_dict = {}
  #dictionary of data for the reference PDB, key is "A" or "B" and the line number 
  ref_vals = {}

  #read the data for the reference PDB
  line = ref_pdb.readline()
  while (line):
    if isinstance(line, (bytes, bytearray)):
      line = str(line, "utf-8")
    lineparts = re.findall("\S+", str(line))
    if len(lineparts) > 5 and lineparts[0] == "ATOM":
      key = (lineparts[4], int(lineparts[5]))
      if key not in ref_vals: #line data is not already in the dictionary
        ref_vals[key] = lineparts[3]
    line = ref_pdb.readline()

  t_arr = []
  #read and compare the data for the other PDBs
  for i,pdb in enumerate(pdb_files):
    t_arr.append(threading.Thread(target=find_dif, args=(ref_vals, dif_dict, pdb,)))
    t_arr[i].start()
    
  for i,pdb in enumerate(pdb_files):
    t_arr[i].join()
  
  util.double_print("Changes to " + os.path.basename(ref_pdb.name), outfile)
  util.double_print("-------------------------------------------------", outfile)
  ref_pdb.close()

  #write the comparison data
  for pdb in pdb_files:
    util.double_print(os.path.basename(pdb.name) + ": " + str(len(dif_dict[pdb.name])), outfile)
    for difference in dif_dict[pdb.name]:
      util.double_print(difference, outfile)
    util.double_print("", outfile)
    pdb.close()
  outfile.close()

if __name__ == "__main__":
  main(sys.argv[1:])
