#!/bin/bash

#path to scans of interest list
scans="/Users/kjung6/Eva/scan_list.txt"
#path to subjects of interest list
subj="/Users/kjung6/Eva/subj_list2.txt"
#path to output
output="/Users/kjung6/Eva/flywheel/"

yes | fw download "mormino/Lucas_PETMR/${sub_id}/" --include="*/*/${scan_id}/*" -i bval -i bvec -o "${sub_id}/${sub_id}_${scan_id}.tar"

