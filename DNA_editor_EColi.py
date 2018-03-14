#!/usr/bin/python
import sys
import re

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

#arguments should be the file to read from and the file to write to, respectively
#input file has one line of the amino acid sequence, one line of the dna sequence, and multiple lines consisting of changes to the amino acid sequence formatted as follows: the location of the amino acid to be replaced, the amino acid to be replaced, and the new amino acid to replace with: example: 25 A->G

if len(sys.argv) > 1:
  dataFile = open(sys.argv[1], "r")
  try:
    outFile = open(sys.argv[2], "w")
  except Exception:
    print "Output file not found"
    outFile = open("output.txt", "w")
else:
  dataFileStr = raw_input("Please enter the path to the input file: ")
  dataFile = open(dataFileStr, "r")
  outFile = open("output.txt", "w")

amino_seq = dataFile.readline()
dna_seq = dataFile.readline()

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
  
outFile.write(amino_seq)
outFile.write(dna_seq)

print amino_seq
print dna_seq

dataFile.close()
outFile.close()