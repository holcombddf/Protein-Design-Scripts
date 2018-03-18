#!/usr/bin/bash
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels
#Script can be given a third argument which is a column label to sort the values on

run_scripts(){
  if [[ $# -eq 1 ]]; then #no information given, uses default coded values
    python score_data_extractor.py $1
    python csv_sorter_and_top_10.py $1
  elif [[ $# -eq 2 ]]; then #labels are given in $2, need to find indices
    python score_data_extractor.py $1 $2
    python csv_sorter_and_top_10.py $1
  elif [[ $# -gt 2 ]]; then #labels are given in $2, and the label to sort on is given in $3
    python score_data_extractor.py $1 $2
    python csv_sorter_and_top_10.py $1 $3
  fi
}

#choose whether to use an argument or the current directory
if [[ $# -ge 1 ]]; then
    dir="$1"
else
    dir="$PWD"
fi

#run scripts in each subdirectory
for subdir in $dir/*/
do
  if [[ $# -le 1 ]]; then 
    run_scripts $subdir & 
  elif [[ $# -eq 2 ]]; then
    run_scripts $subdir $2 &
  elif [[ $# -gt 2 ]]; then
    run_scripts $subdir $2 $3 &
  fi
done
wait