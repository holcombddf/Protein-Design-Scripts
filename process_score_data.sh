#!/usr/bin/bash
#Script should have an argument that is a path to the directory containing all the subdirectories
#Otherwise, it uses the current directory

#choose whether to use an argument or the current directory
if [[ $# -ge 1 ]]; then
    dir="$1"
else
    dir="$PWD"
fi

#run scripts in each subdirectory
for subdir in $dir/*/
do
    python score_data_extractor.py $subdir
    python csv_sorter_and_top_10.py $subdir
    
done
wait