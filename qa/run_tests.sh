#!/usr/bin/bash
#Used for testing all other scripts more efficiently

#prints the name and the output of each test
#$1 is the name
#$2 is the command (with arguments) to test
run_test(){
  echo "$1" | tee -a test.log
  #capture the error
  ERR=$(((eval "$2") 1>>test.log) 2>&1)
  #print if there is an error
  if [ "$ERR" != "" ]; then
    echo "$1" >>err.log
    echo "$ERR" >>err.log
    echo "---------------------------------------------------------------------------------------------------" >>err.log
  fi
  echo "---------------------------------------------------------------------------------------------------" >>test.log
}

#source directory
if [[ $# -ge 1 ]]; then
  DIR="$1"
else
  DIR="/home/david_holcomb/Workspace/Protein-Design-Scripts/src"
fi

#testing directory
if [[ $# -ge 2 ]]; then
  TESTDIR="$2"
else
  TESTDIR="/home/david_holcomb/Workspace/Protein-Design-Scripts/qa"
fi

#write the pdblist, using the testing directory
echo "$TESTDIR/pdb2.pdb" >$TESTDIR/pdbs.list
echo "$TESTDIR/pdb3.pdb" >>$TESTDIR/pdbs.list 
echo "$TESTDIR/pdb4.pdb" >>$TESTDIR/pdbs.list 

#print the date and time
dt=$(date '+%d/%m/%Y %H:%M:%S')
echo "Time $dt" > test.log
echo "Time $dt" > err.log

#start=$(date +%s.%N)

#run the tests
run_test "process_score_data.py 1 argument" "python $DIR/process_score_data.py --directory $TESTDIR"
run_test "process_score_data.py 2 arguments" "python $DIR/process_score_data.py --directory $TESTDIR  --headerlist $TESTDIR/column_headers.list"
run_test "process_score_data.py 3 arguments" "python $DIR/process_score_data.py --directory $TESTDIR --headers total_score RMSD_WT binding_score catalytic_score specificity_score --sortheader total_score"
run_test "process_score_data.py 3 arguments list" "python $DIR/process_score_data.py --directory $TESTDIR --headerlist $TESTDIR/column_headers.list --sortheader total_score"
run_test "amarel_score_data_extractor.py" "python $DIR/amarel_score_data_extractor.py $TESTDIR $TESTDIR/column_headers.list"
run_test "score_data_extractor.py list" "python $DIR/score_data_extractor.py $TESTDIR/job1/ $TESTDIR/column_headers.list"
run_test "score_data_extractor.py labels" "python $DIR/score_data_extractor.py $TESTDIR/job1/ total_score RMSD_WT binding_score catalytic_score specificity_score"
run_test "csv_sorter_and_top_10.py file" "python $DIR/csv_sorter_and_top_10.py $TESTDIR/job1/job1_collected_scores.csv"
run_test "csv_sorter_and_top_10.py folder and label" "python $DIR/csv_sorter_and_top_10.py $TESTDIR/job1/ total_score"
run_test "dna_editor_ecoli.py 2 arguments 0-indexed" "python $DIR/dna_editor_ecoli.py --infile $TESTDIR/amino_acid_edits_0.txt --outfile $TESTDIR/dna_editor_ecoli_output_20.txt"
run_test "dna_editor_ecoli.py 1 argument 0-indexed" "python $DIR/dna_editor_ecoli.py --infile $TESTDIR/amino_acid_edits_0.txt"
run_test "dna_editor_ecoli.py 3 arguments 1-indexed" "python $DIR/dna_editor_ecoli.py --infile $TESTDIR/amino_acid_edits_1.txt --outfile $TESTDIR/dna_editor_ecoli_output_31.txt --index 1"
run_test "dna_editor_ecoli.py 2 argument 1-indexed" "python $DIR/dna_editor_ecoli.py --infile $TESTDIR/amino_acid_edits_1.txt --index 1"
run_test "pdb_change_parser.py list" "python $DIR/pdb_change_parser.py --ref $TESTDIR/pdb1.pdb --pdblist $TESTDIR/pdbs.list"
run_test "pdb_change_parser.py files" "python $DIR/pdb_change_parser.py --ref $TESTDIR/pdb1.pdb --pdbs $TESTDIR/pdb2.pdb $TESTDIR/pdb3.pdb $TESTDIR/pdb4.pdb"
run_test "pdb_change_parser.py gz" "python $DIR/pdb_change_parser.py --ref $TESTDIR/pdb.pdb.gz --pdblist $TESTDIR/pdbs.list"
run_test "pdb_to_res.py" "python $DIR/pdb_to_res.py $TESTDIR/pdb1.pdb"
run_test "visualize_score_data.r" "Rscript $DIR/visualize_score_data.r $TESTDIR/job1/job1_collected_scores.csv total_score binding_score"
run_test "ad_hoc_scheduler.py" "python $DIR/ad_hoc_scheduler.py 45 15"
run_test "queue_scheduler.py" "python $DIR/queue_scheduler.py 45 15"

#end=$(date +%s.%N)
#dt=$(echo "$end - $start" | bc)
#echo "$dt seconds elapsed"

#if the error log file has more than one line, inform the user
NUMLINES=$(wc -l < "err.log")
if [ "$NUMLINES" -gt 1 ]; then
  echo "Errors found. See err.log for details."
fi

#python cleanup.py $DIR 
#python cleanup.py $TESTDIR