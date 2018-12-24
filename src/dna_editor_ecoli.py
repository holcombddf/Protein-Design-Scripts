#!/usr/bin/python
import sys
import os
import re
import util
import argparse
from operator import itemgetter
import copy

#utility function that converts the amino acid into the corresponding dna codon for E Coli
def aa_to_dna(amino_acid):
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
  elif (amino_acid == 'L'):
    replacement = "CTT"
  else:
    raise Exception("Unaccounted amino acid: " + amino_acid)
  return(replacement)

#function to process the edits and print the resulting sequences, highlighting the edited parts
def print_with_colors(amino_seq, dna_seq, editlist, colorstart, colorend, endline="", endfile="", handle=None):

    copy_aa_seq = copy.deepcopy(amino_seq)
    copy_dna_seq = copy.deepcopy(dna_seq)
    
    #iterate through edits, sorted by location
    numedits = 0
    for edit in sorted(editlist, key=itemgetter(0)):
      aa_location = edit[0]+(len(colorstart+colorend)*numedits) #adjust for colorstart and colorend for edits previously made
      dna_location = 3*edit[0]+(len(colorstart+colorend)*numedits)#adjust for colorstart and colorend for edits previously made
      new_aa = edit[1]
      new_dna = edit[2]
      
      #add edit to string with color highlight substring
      copy_aa_seq = copy_aa_seq[:aa_location] + colorstart + new_aa + colorend + copy_aa_seq[aa_location+1:]
      copy_dna_seq = copy_dna_seq[:dna_location] + colorstart + new_dna + colorend + copy_dna_seq[dna_location+3:]
      numedits = numedits + 1 #number of edits already processed
      
    if handle is None: #print to console
      print(copy_aa_seq + endline)
      print(copy_dna_seq + endline)
      print(endfile)
    else: #write to file handle
      handle.write(copy_aa_seq+endline)
      handle.write(copy_dna_seq+endline)
      handle.write(endfile)

def parse_args(sysargv=[]):
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", metavar='FILE', type=str, default=None, action="store", help="file containing the changes to read")
  parser.add_argument("--outfile", metavar='FILE', type=str, default=None, action="store", help="file to write the output to")
  parser.add_argument("--index", type=int, default=0, action="store", help="determines whether the input file is 0-indexed or 1-indexed")
  return(parser.parse_args())

def main(sysargv=[]):
  
  args = parse_args(sysargv)
  #arguments should be the file to read from and the file to write to, respectively
  #input file has three sections, each started by one line containing ">":first section contains the amino acid sequence, second section contains the dna sequence, third section contains the amino acid changes
  #amino acid changes should be formatted as a location (either 0-indexed or 1-indexed) with two single letters denoting amino acids (for example 25A>G, 25 A->G, 25AG, etc.) on a single line

  dataFile = util.get_file2(args.infile, "r", "input")
  if args.outfile is not None:
    outFile = util.get_file2(os.path.splitext(args.outfile)[0]+".rtf", "w", "RTF") #make sure output file is RTF formatted so edits are colored
  else:
    directory = os.path.dirname(dataFile.name)
    directory = os.path.join(directory, "")
    outFile = util.get_file2(directory+"outfile.rtf", "w", "output")
  outFile.write("{\\rtf1\\ansi\\deff0\n{\\colortbl;\\red0\\green0\\blue0;\\red255\\green0\\blue0;}\n") #RTF garbage

  amino_seq = ""
  dna_seq = ""
  section = 0
  editlist = []
  linelist = dataFile.readlines()
  for line in linelist:
    line = line.rstrip()
    
    if re.match(">", line):#changing to another section
      section=section+1
    elif section == 1: #reading the amino acid sequence
      amino_seq = amino_seq + line
    elif section == 2: #reading the DNA sequence
      dna_seq = dna_seq + line
    elif section == 3: # reading the changes
      lineparts = re.findall("\d+|[a-zA-Z]", line) #capture all (multidigit) numbers and single letters

      if len(lineparts) == 0: #only whitespace or irrelevant characters in line
        pass
      elif len(lineparts) < 3 and len(lineparts) > 0: #check that location and replacement info are both given
        raise Exception("Changes are incorrectly formatted: " + str(lineparts))
      else:
        location = int(lineparts[0])-int(args.index)
        if (lineparts[1]).upper() != (amino_seq[location]).upper(): #check that the intended amino acid to be replaced is at the given location
          raise Exception("Amino acid at location " + str(location) + " does not match given amino acid: " + lineparts[1])
        new_dna=aa_to_dna(lineparts[2])
        editlist.append([int(lineparts[0]), lineparts[2], new_dna])
  
  #process and print the edits
  print_with_colors(amino_seq, dna_seq, editlist, '\033[93m', '\033[0m') #print to console
  print_with_colors(amino_seq, dna_seq, editlist, "\n\\cf2\n", "\n\\cf1\n", "\\line\n", "}", outFile) #write to outFile

  dataFile.close()
  outFile.close()

if __name__ == "__main__":
  main(sys.argv[1:])
