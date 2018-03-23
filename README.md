# Protein-Design-Scripts
Script Documentation  
David Holcomb  
March 2018

## dna_editor_ecoli.py
Produces the amino acid sequence and DNA resulting from a series of edit mutations, as expressed in E. Coli.  
Takes in an input file with three sections, started by lines containing ">". First section contains the amino acid sequence. Second section contains the DNA sequence. Third section contains the amino acid changes.  
Amino acid changes should be formatted as a location (either 0-indexed or 1-indexed) with two single letters denoting amino acids (for example 25A>G, 25 A->G, 25AG, etc.) on a single line.  
Takes as arguments the path to the input file and the path to the output file, but also accepts the path from the command line if no arguments are given. Also takes an an argument whether the locations of the changes are 0-indexed or 1-indexed.

## pdb_change_parser.py
Produces a list of amino acid changes for multiple PDB files, relative to a reference PDB.  
It takes in a file consisting of a list of PDB files.  
Takes two arguments: a reference PDB file to compare to, and a list of PDB files to compare.

## pdb_to_res.py
Converts a given PDB file into a RES (.res) file.  
It takes in PDB file.  
Takes as an argument a path to the PDB file to convert.

## score_data_extractor.py
Produces a spreadsheet of the desired columns from all the score files in a desired directory.  
To change the columns, edit the INDICES variable.  
Takes as an argument a path to the directory containing the score files.  
Can be given a second argument, which is a path to a list of column headers.

## csv_sorter_and_top_10.py
Produces a spreadsheet containing the top NUM lines of an input spreadsheet, sorted on column COL. Designed to be used after score_data_extractor.py.  
The spreadsheet to be sorted should be named "[folder name]_collected_scores.csv", where [folder name] gives the name of the folder containing the spreadsheet.  
To change the number of lines to be output or the column to sort on, change variables NUM or COL, respectively.  
Takes as an argument a path to the directory containing the spreadsheet to be sorted, or a path to the spreadsheet to be sorted.  

## process_score_files.py
Same as process_score_files.sh, but written in python.

## util.py
Contains frequently used utility functions for running the other scripts.

## visualize_score_data.r
Produces a scatterplot for two variables in a spreadsheet.  
Takes as arguments the spreadsheet (.csv) to read from, the name of the x-variable column header, and the name of the y-variable column header.

## ad_hoc_scheduler.py (Untested)
Creates threads for jobs (bash commands), limited to TLIM threads and total ~MLIM memory at a time. Uses a bounded semaphore for thread limiting, and lock for memory limiting.  
Can take as arguments an integer representing the thread limit, and a float representing the total memory limit (in GB).  
Change the GENERATE FILELIST HERE and GENERATE CMD HERE sections to suit your needs.

## queue_scheduler.py (Untested)
Same as ad_hoc_scheduler.py, but uses a queue to manage thread limits. 

## run_tests.sh
Tests all other scripts, using qa as a data source.  
Can be given as an argument, a path to the directory containing the scripts (src), and a path to the directory containing the testing data (qa).