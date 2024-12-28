#!/bin/bash

#cat /Users/kjung6/Eva/subj_list.txt

#while read -r line; do
#  echo "$line"
#done < /Users/kjung6/Eva/subj_list.txt

#path to scans of interest list
scans="scan_list.txt"
#path to subjects of interest list
subj="subj_list.txt"
#path to output
output="/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/download_fw/"

# Initialize empty arrays to store the contents of the files
list1=()
list2=()

# Read file1.txt line by line and add each line to list1 array
while IFS= read -r line; do
    list1+=("$line")
done < "$subj"

# Read file2.txt line by line and add each line to list2 array
while IFS= read -r line; do
    list2+=("$line")
done < "$scans"

cd $output
# Iterate through both arrays using a for loop
for sub_id in "${list1[@]}"; do

    #mkdir -P $sub_id
    for scan_id in "${list2[@]}"; do
        echo "Processing ${sub_id} and ${scan_id}"
        
        yes | fw ls "mormino/Lucas_PETMR/${sub_id}/" -o "${sub_id}/${sub_id}_${scan_id}.tar"
    done
done




#yes | fw download "mormino/Lucas_PETMR/${subject}/" --include="*/*/${scan}/*" -i bval -i bvec 



