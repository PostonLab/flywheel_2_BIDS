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


dcm_path = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/raw'
id_map_table = 'FW_data.csv'
nii_path = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data/sourcedata/nii_data'
bids_path = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data'
config_file = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/bids_data/code/dcm2bids_config.json'


# Read the CSV file into a DataFrame
id_map_df = pd.read_csv(id_map_table)

def convert2nii():
    for subdir in os.listdir(dcm_path):
        full_path = os.path.join(dcm_path, subdir)
        print(full_path)

        if os.path.isdir(full_path):
            base_subdir = os.path.basename(full_path)

            # Find the matching adrc_id in the DataFrame
            ivim_id_match = id_map_df[id_map_df['ivim_id'] == base_subdir]

            if not ivim_id_match.empty:
                adrc_id = ivim_id_match.iloc[0]['adrc_id']  # Get the first matching adrc_id
                print(f"Found matching adrc_id: {adrc_id} for subdirectory: {base_subdir}")

                ivim_id = str(ivim_id_match['adrc_id'].values[0])

                for scan_subdir in glob.glob(full_path+'/*/*'):
                    scan_path = os.path.join(full_path, scan_subdir)

                    base_scan_subdir = os.path.basename(scan_path)
                    final_outpath = nii_path+'/'+ivim_id+'/'+base_scan_subdir

                    os.makedirs(final_outpath, exist_ok=True) 

                    command = ["dcm2niix", "-f", ivim_id, "-o", final_outpath, scan_path]

                    try:
                        subprocess.run(command, check=True)  # Execute the command and check for errors
                        print(f"conversion completed successfully for subdirectory: {base_scan_subdir}")
                    except subprocess.CalledProcessError as error:
                        print(f"conversion failed with error: {error}")

            else:
                print(f"No matching adrc_id found for subdirectory: {base_subdir}")

        else:
            print("Path for dcms does not exist")

def convert2bids():
    # Create an empty DataFrame with the column 'participant_id'
    df = pd.DataFrame(columns=['participant_id'])
    participants = []

    for subdir in os.listdir(dcm_path):
        full_path = os.path.join(dcm_path, subdir)
        print(full_path)

        if os.path.isdir(full_path):
            base_subdir = os.path.basename(full_path)

            # Find the matching adrc_id in the DataFrame
            ivim_id_match = id_map_df[id_map_df['ivim_id'] == base_subdir]

            if not ivim_id_match.empty:
                adrc_id = ivim_id_match.iloc[0]['adrc_id']  # Get the first matching adrc_id
                print(f"Found matching adrc_id: {adrc_id} for subdirectory: {base_subdir}")

                ivim_id = str(ivim_id_match['adrc_id'].values[0])

                final_outpath = bids_path+'/bids'
                os.makedirs(final_outpath, exist_ok=True) 

                participants.append('sub-'+str(adrc_id)) # storing participnat IDs to be saved in tsv later

                command = ["dcm2bids", "-d", full_path, "-p", ivim_id, "-c", config_file, "-o", final_outpath, "--auto_extract_entities", "--force_dcm2bids"]

                try:
                    subprocess.run(command, check=True)  # Execute the command and check for errors
                    print(f"conversion completed successfully for subject: {ivim_id}")
                    subprocess.run(["rm", "-r", bids_path+'/bids/tmp_dcm2bids'], check=True) # Removing the temporary files

                except subprocess.CalledProcessError as error:
                    print(f"conversion failed with error: {error}")

            else:
                print(f"No matching adrc_id found for subdirectory: {base_subdir}")

        else:
            print("Path for dcms does not exist")


    df['participant_id'] = participants
    # Save the DataFrame as a TSV file
    df.to_csv("../participants_reuploads.tsv", sep="\t", index=False)

        
#convert2nii() #use this first to convert dcms to nii, so that you can evaluate json files to desing the dcm2bids_config.json
convert2bids()
