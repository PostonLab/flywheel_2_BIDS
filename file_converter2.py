#!/usr/bin/env python3

# This script is designed to convert ADRC (Alzheimer's Disease Resource Center) data from its raw format to BIDS (Brain Imaging Data Structure) format.
# It consists of two main sections:
# 1. The `convert2nii()` function converts DICOM data to NIfTI format using dcm2niix, allowing for inspection of the data and generation of a configuration file (dcm2bids_config.json) for the next step.
# 2. The `convert2bids()` function utilizes the dcm2bids tool to organize the NIfTI files into the BIDS format.
# To run this script, ensure that dcm2bids is installed on your system.
#
# Author: Dimuthu Hemachandra
# Contact: dimuthu@stanford.com

import os
import pandas as pd
import glob
import subprocess


#dcm_path = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/raw'
#id_map_table = 'FW_data.csv'
#nii_path = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data/sourcedata/nii_data'
#bids_path = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data'
#config_file = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data/code/dcm2bids_config.json'

dcm_path = '/Users/kjung6/eva/flywheel/flywheel/mormino/Lucas_PETMR/'
id_map_table = '/Users/kjung6/Eva/flywheel/FW_data.csv'
nii_path = '/Users/kjung6/Eva/flywheel/nii_data'
bids_path = '/Users/kjung6/Eva/flywheel/bids_data'
#config_file = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data/code/dcm2bids_config.json'

# Read the CSV file into a DataFrame
id_map_df = pd.read_csv(id_map_table)

import zipfile
import os

def extract_zip(zip_path, extract_to):
    """Extract a ZIP file to a specified directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted {zip_path} to {extract_to}")

def convert2nii():
    for subdir in os.listdir(dcm_path):
        full_path = os.path.join(dcm_path, subdir)
        print(full_path)

        if os.path.isdir(full_path):
            base_subdir = os.path.basename(full_path)

            # Find the matching adrc_id in the DataFrame
            pet_scan_id_match = id_map_df[id_map_df['pet_scan_id'] == base_subdir]

            if not pet_scan_id_match.empty:
                adrc_id = pet_scan_id_match.iloc[0]['adrc_id']  # Get the first matching adrc_id
                print(f"Found matching adrc_id: {adrc_id} for subdirectory: {base_subdir}")

                pet_scan_id = str(pet_scan_id_match['adrc_id'].values[0])

                for scan_subdir in glob.glob(full_path+'/*/*'):
                    scan_path = os.path.join(full_path, scan_subdir)
                    base_scan_subdir = os.path.basename(scan_path)
                    final_outpath = nii_path+'/'+pet_scan_id+'/'+base_scan_subdir

                    os.makedirs(final_outpath, exist_ok=True)

                    # Check if the scan directory is a .zip file
                    if scan_path.endswith('.zip'):
                        # Extract the ZIP file to a temporary directory
                        temp_dir = final_outpath + '_temp'
                        os.makedirs(temp_dir, exist_ok=True)
                        extract_zip(scan_path, temp_dir)

                        # Update the scan_path to point to the extracted directory
                        scan_path = temp_dir
                        command = ["dcm2niix", "-f", pet_scan_id, "-o", final_outpath, scan_path]

                    else:
                        command = ["dcm2niix", "-f", pet_scan_id, "-o", final_outpath, scan_path]

                    try:
                        subprocess.run(command, check=True)  # Execute the command and check for errors
                        print(f"conversion completed successfully for subdirectory: {base_scan_subdir}")
                    except subprocess.CalledProcessError as error:
                        print(f"conversion failed with error: {error}")

            else:
                print(f"No matching adrc_id found for subdirectory: {base_subdir}")

        else:
            print("Path for dcms does not exist")
            
    df['participant_id'] = participants
    # Save the DataFrame as a TSV file
    df.to_csv("../participants_reuploads.tsv", sep="\t", index=False)

        
convert2nii() #use this first to convert dcms to nii, so that you can evaluate json files to desing the dcm2bids_config.json
#convert2bids()