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

#Testing directory
if [[ $# -ge 1 ]]; then
  DIR="$1"
else
  DIR="/home/david_holcomb/Desktop/Workspace/Testing"
fi

#write the pdblist, using the testing directory
echo "$DIR/pdb2.pdb" >$DIR/pdbs.list
echo "$DIR/pdb3.pdb" >>$DIR/pdbs.list 
echo "$DIR/pdb4.pdb" >>$DIR/pdbs.list 

#print the date and time
dt=$(date '+%d/%m/%Y %H:%M:%S')
echo "Time $dt" > test.log
echo "Time $dt" > err.log

#run the tests
run_test "process_score_data.sh 1 argument" "bash process_score_data.sh $DIR"
run_test "process_score_data.sh 2 arguments" "bash process_score_data.sh $DIR/ $DIR/column_headers.list"
run_test "process_score_data.sh 3 arguments" "bash process_score_data.sh $DIR/ $DIR/column_headers.list total_score"
run_test "process_score_data.py 1 argument" "python process_score_data.py --directory $DIR"
run_test "process_score_data.py 2 arguments" "python process_score_data.py --directory $DIR  --headerlist $DIR/column_headers.list"
run_test "process_score_data.py 3 arguments list" "python process_score_data.py --directory $DIR --headerlist $DIR/column_headers.list --sortheader total_score"
run_test "process_score_data.py 3 arguments" "python process_score_data.py --directory $DIR --headers total_score RMSD_WT binding_score catalytic_score specificity_score --sortheader total_score"
run_test "amarel_score_data_extractor.py" "python amarel_score_data_extractor.py $DIR $DIR/column_headers.list"
run_test "score_data_extractor.py list" "python score_data_extractor.py $DIR/job1/ $DIR/column_headers.list"
run_test "score_data_extractor.py labels" "python score_data_extractor.py $DIR/job1/ total_score RMSD_WT binding_score catalytic_score specificity_score"
run_test "csv_sorter_and_top_10.py file" "python csv_sorter_and_top_10.py $DIR/job1/job1_collected_scores.csv"
run_test "csv_sorter_and_top_10.py folder and label" "python csv_sorter_and_top_10.py $DIR/job1/ total_score"
run_test "dna_editor_ecoli.py 2 arguments" "python dna_editor_ecoli.py --infile $DIR/amino_acid_edits.txt --outfile $DIR/outfile.txt"
run_test "dna_editor_ecoli.py 1 argument" "python dna_editor_ecoli.py --infile $DIR/amino_acid_edits.txt"
run_test "pdb_change_parser.py list" "python pdb_change_parser.py --ref $DIR/pdb1.pdb --pdblist $DIR/pdbs.list"
run_test "pdb_change_parser.py files" "python pdb_change_parser.py --ref $DIR/pdb1.pdb --pdbs $DIR/pdb2.pdb $DIR/pdb3.pdb $DIR/pdb4.pdb"
run_test "pdb_change_parser.py gz" "python pdb_change_parser.py --ref $DIR/pdb.pdb.gz --pdblist $DIR/pdbs.list"
run_test "pdb_to_res.py" "python pdb_to_res.py $DIR/pdb1.pdb"
run_test "visualize_score_data.r" "Rscript visualize_score_data.r $DIR/job1/job1_collected_scores.csv total_score binding_score"
run_test "ad_hoc_scheduler.py" "python ad_hoc_scheduler.py 45 15"
run_test "queue_scheduler.py" "python queue_scheduler.py 45 15"

#if the error log file has more than one line, inform the user
NUMLINES=$(wc -l < "err.log")
if [ "$NUMLINES" -gt 1 ]; then
  echo "Errors found. See err.log for details."
fi