#!/usr/bin/python
import sys
import os
import re
import util
import argparse

#utility function that converts the amino acid into the corresponding dna codon for E Coli
def aa_to_dna(dna_seq, location, amino_acid):
  location = 3*location
  replacement = dna_seq[location: location+3]
  amino_acid = amino_acid.upper()
  
  if (amino_acid == 'C'):
    replacement = "TGC"
  elif (amino_acid == 'S'):
    replacement = "GCA"
  elif (amino_acid == 'D'):
    replacement = "GAT"
  elif (amino_acid == 'F'):
    replacement = "TTT"
  elif (amino_acid == 'T'):
    replacement = "ACC"
  elif (amino_acid == 'G'):
    replacement = "GGC"
  elif (amino_acid == 'Q'):
    replacement = "CAG"
  elif (amino_acid == 'E'):
    replacement = "GAA"
  elif (amino_acid == 'W'):
    replacement = "TGG"
  elif (amino_acid == 'Y'):
    replacement = "TAC"
  elif (amino_acid == 'R'):
    replacement = "CGG"
  elif (amino_acid == 'A'):
    replacement = "GCA"
  elif (amino_acid == 'K'):
    replacement = "AAA"
  elif (amino_acid == 'H'):
    replacement = "CAC"
  elif (amino_acid == 'P'):
    replacement = "CCG"
  elif (amino_acid == 'N'):
    replacement = "AAC"
  elif (amino_acid == 'V'):
    replacement = "GTC"
  else:
    raise Exception("Unaccounted amino acid: " + amino_acid)
  
  dna_seq = dna_seq[:location] + replacement + dna_seq[location+3:]
  return dna_seq

def parse_args(sysargv=[]):
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", metavar='FILE', type=str, default=None, action="store", help="file containing the changes to read")
  parser.add_argument("--outfile", metavar='FILE', type=str, default=None, action="store", help="file to write the output to")
  return parser.parse_args()

def main(sysargv=[]):
  args = parse_args(sysargv)
  #arguments should be the file to read from and the file to write to, respectively
  #input file has one line of the amino acid sequence, one line of the dna sequence, and multiple lines consisting of changes to the amino acid sequence formatted as follows: the location of the amino acid to be replaced, the amino acid to be replaced, and the new amino acid to replace with: example: 25 A->G

  dataFile = util.get_file2(args.infile, "r", "input")
  if args.outfile is not None:
    outFile = util.get_file2(args.outfile, "w", "output")
  else:
    directory = os.path.dirname(dataFile.name)
    directory = os.path.join(directory, "")
    outFile = util.get_file2(directory+"outfile.txt", "w", "output")

  amino_seq = (dataFile.readline()).rstrip()
  dna_seq = (dataFile.readline()).rstrip()

  line = dataFile.readline()
  while (line):
    line = line.rstrip()
    lineparts = re.findall("\d+|[a-zA-Z]", line) #capture all (multidigit) numbers and single letters
    
    if len(lineparts) < 3: #check that location and replacement info are both given
      raise Exception("Changes are incorrectly formatted: " + str(lineparts))

    location = int(lineparts[0])
    if (lineparts[1]).upper() != (amino_seq[location]).upper(): #check that the intended amino acid to be replaced is at the given location
      raise Exception("Amino acid at location " + str(location) + " does not match given amino acid: " + lineparts[1])
    amino_seq = amino_seq[:location] + lineparts[2] + amino_seq[location+1:]
    dna_seq=aa_to_dna(dna_seq, location, lineparts[2])
    line = dataFile.readline()
    
  util.double_print(amino_seq, outFile)
  util.double_print(dna_seq, outFile)

  dataFile.close()
  outFile.close()

if __name__ == "__main__":
  main(sys.argv[1:])