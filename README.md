# Protein-Design-Scripts
Script Documentation
David Holcomb
March 2018

DNA_editor_EColi.py
Produces the amino acid sequence and DNA resulting from a series of edit mutations, as expressed in E. Coli. 
It takes in a file formatted as one line of the original amino acid sequence, one line of the original DNA sequence, and a series of lines of edit mutations formatted as: the location of the amino acid to change, the original amino acid, and the amino acid to change to (for example, "25 A->G"). Note that the edit locations are 0-indexed.
Takes as arguments the path to the input file and the path to the output file, but also accepts the path from the command line if no arguments are given.

score_data_extractor.py
Produces a spreadsheet of the desired columns from all the score files in a desired directory. 
To change the columns, edit the INDICES variable.
Takes as an argument a path to the directory containing the score files.

csv_sorter_and_top_10.py
Produces a spreadsheet containing the top NUM lines of an input spreadsheet, sorted on column COL. Designed to be used after score_data_extractor.py.
The spreadsheet to be sorted should be named "[folder name]_collected_scores.csv", where [folder name] gives the name of the folder containing the spreadsheet. 
To change the number of lines to be output or the column to sort on, change variables NUM or COL, respectively.
Takes as an argument a path to the directory containing the spreadsheet to be sorted.

process_score_files.sh
Runs score_data_extractor.py and csv_sorter_and_top_10.py in each subdirectory of a given directory. 
Takes as an argument the path to the directory containing all subdirectories.