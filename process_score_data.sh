#!/usr/bin/bash
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory
#Script can be given a second argument, which is a file containing a list of column labels

run_scripts(){
  if [[ $# -eq 1 ]]; then #indices are given
    python score_data_extractor.py $1
    python csv_sorter_and_top_10.py $1
  elif [[ $# -gt 1 ]]; then #labels are given in #2, need to find indices
    python score_data_extractor.py $1 $2
    python csv_sorter_and_top_10.py $1
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
  elif [[ $# -gt 1 ]]; then
    run_scripts $subdir $2 &
  fi
done
wait