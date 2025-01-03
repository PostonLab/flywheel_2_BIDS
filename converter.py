import flywheel
import os
import tarfile
import shutil
from concurrent.futures import ThreadPoolExecutor
import zipfile
import subprocess
import pandas as pd
import yaml
import random
from datetime import datetime
import json


# Global variable to store the configuration
config = {}

# Load configuration from YAML file
def load_config(config_file):
    global config  # Declare that we are using the global variable
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)


def create_temp_dir(base_path):
    # Get current date in YYYY-MM-DD format
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Generate a random 5-digit number
    random_number = random.randint(10000, 99999)
    
    # Construct the directory name
    dir_name = f'flywheel_2_bids_{current_date}_{random_number}'
    
    # Full directory path
    full_path = os.path.join(base_path, dir_name)
    
    # Create the directory
    try:
        os.makedirs(full_path)
        print(f"Temporary directory created: {full_path}")
    except FileExistsError:
        print(f"Directory already exists: {full_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return full_path

def unzip_files_in_directory(directory, pattern):
    extract_path = os.path.join(directory, 'dicoms')
    os.makedirs(extract_path, exist_ok=True)

    for item in os.listdir(directory):
        if item.endswith(pattern):
            file_path = os.path.join(directory, item)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)  # Unzipping
            print(f'Unzipped: {file_path}')

def copy_matching_folders(source_directory, target_directory):
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True) 

    
    # Walk through the source directory
    for root, dirs, files in os.walk(source_directory):
        for dir_name in dirs:
            # Check if any of the search strings are in the directory name
            if any(s in dir_name for s in config['scan_names']) and not any(e in dir_name for e in config['exclude_strings']):
                # Create the full path to the source directory
                full_dir_path = os.path.join(root, dir_name)
                selected_scan_path = os.path.join(target_directory, dir_name)
                # Copy the directory to the target directory
                shutil.copytree(full_dir_path, selected_scan_path, dirs_exist_ok=True)
                print(f'Copied: {full_dir_path} to {target_directory}')
                dcm_path = unzip_files_in_directory(selected_scan_path, 'dicom.zip')

def convert2bids(dcm_path, subj_id, final_bids_path):

    config_json = config['config_json']

    bids_id = str(id_map_df.loc[id_map_df['subject_id'] == subj_id, 'adrc_id'].values[0])

    command = ["dcm2bids", "-d", dcm_path, "-p", bids_id, "-c", config_json, "-o", final_bids_path, "--auto_extract_entities", "--force_dcm2bids"]

    print(command)

    try:
        subprocess.run(command, check=True)  # Execute the command and check for errors
        print(f"conversion completed successfully for subject: {bids_id}")
        subprocess.run(["rm", "-r", f'{final_bids_path}/tmp_dcm2bids/sub-{bids_id}'], check=True) # Removing the temporary files

    except subprocess.CalledProcessError as error:
        print(f"conversion failed with error: {error}")

def generate_bids_dataset_description(yaml_file, output_dir):
    # Read the YAML configuration file
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    # Set the path for the output JSON file
    output_file = os.path.join(output_dir, 'dataset_description.json')

    # Write the data to the JSON file
    with open(output_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print(f"Generated {output_file} successfully.")

def pull_and_run_bids_validator(container_destination, bids_directory):
    """Pulls the BIDS Validator Singularity container if not present and runs validation."""
    
    # Define the container name
    container_name = "validator_latest.sif"
    container_path = os.path.join(container_destination, container_name)
    
    # Check if the container already exists
    if not os.path.exists(container_path):
        print(f"The container does not exist at {container_path}. Pulling the container...")
        try:
            # Pull the container from Docker repository
            subprocess.run(
                ["singularity", "pull", "--dir", container_destination, "docker://bids/validator"],
                check=True
            )
            print("Container pulled successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error pulling the container: {e}")
            return
    
    # Now run the BIDS Validator
    if not os.path.exists(bids_directory):
        print(f"The specified BIDS directory does not exist: {bids_directory}")
        return
    
    try:
        subprocess.run(
            ["singularity", "exec", "--bind", bids_directory + ":/home", container_path, "bids-validator", "/home"],
            check=True
        )
        print("BIDS validation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running BIDS validator: {e}")
    
def fw_2_bids(subject_id, scan_names, temp_dir, bids_dir):
    """
    Downloads, filters scans for a given subject and convert to BIDS.

    :param subject_id: Subject ID to download scans from
    :param output_dir: Directory to save the downloaded scans
    :param scan_names: List of scan names to keep
    :param force_download: Boolean to force download even if file exists
    """
    fw_project_path = config['fw_project_path']
    subject = fw.lookup(f'{fw_project_path}/{subject_id}')  # Lookup subject by ID


    if not subject:
        print(f"Subject {subject_id} not found.")
        return

    # Create the output directory if it doesn't exist
    subj_out_dir = os.path.join(temp_dir, f'download_fw/{subject_id}')
    os.makedirs(subj_out_dir, exist_ok=True)

    scan_data = fw.sessions.find(f'subject.code={subject_id}')

    if not scan_data:
        print(f"No sessions found for subject {subject_id}.")
        return

    # Define the tar file path
    tar_file_path = f'{subj_out_dir}/{subject_id}.tar'

    # Downloading the tar file from Flywheel
    try:
        fw.download_tar(scan_data, tar_file_path)
        print(f"Successfully downloaded: {subject_id}")
    except Exception as e:
        print(f"Error downloading {subject_id}: {e}")
        return


    # Extract the tar file
    try:
        with tarfile.open(tar_file_path) as tar:
            tar.extractall(subj_out_dir)
            print(f"Extracted tar for subject: {subject_id}")
    except Exception as e:
        print(f"Error extracting tar for {subject_id}: {e}")
        return

    # Check only the last directory for files that match the specified scan names, Also excluding specifiled files by a string
    sorted_path = f'{temp_dir}/sorted_fw/{subject_id}'
    copy_matching_folders(subj_out_dir, sorted_path)
    convert2bids(sorted_path, subject_id, bids_dir)


    if config['clean_up']:
        subprocess.run(["rm", "-r", sorted_path], check=True) # Cleaning up
        subprocess.run(["rm", "-r", subj_out_dir], check=True) # Cleaning up


def main(subject_ids, scan_names, temp_dir, bids_dir):
    """
    Downloads specific scans from a list of subjects in parallel.

    :param subject_ids: List of subject IDs to download scans from
    :param output_dir: Directory to save the downloaded scans
    :param num_threads: Number of threads to use for downloading scans
    :param scan_names: List of scan names to keep
    :param force_download: Boolean to force download even if file exists
    """

    # Use ThreadPoolExecutor to handle parallel downloads
    with ThreadPoolExecutor(max_workers=config['num_threads']) as executor:
        executor.map(lambda subject_id: fw_2_bids(subject_id, scan_names, temp_dir, bids_dir), subject_ids)



if __name__ == "__main__":

    load_config('config.yml')  # Load the config file

    # Initialize Flywheel client with your API key
    api_key = config['api_key']  
    fw = flywheel.Client(api_key=api_key)

    scan_names = config['scan_names']

    id_map_df = pd.read_csv(config['participants_csv'])
    subject_ids = id_map_df['subject_id'].values
    # Specify your subject IDs and scan names
    #subject_ids = ['PI443', 'PI444']  # Replace with actual subject IDs

    temp_dir_path = config['temp_dir']
    temp_dir = create_temp_dir(temp_dir_path)

    bids_dir = config['output_dir']
    os.makedirs(bids_dir, exist_ok=True)
    

    main(subject_ids, scan_names, temp_dir, bids_dir)

    generate_bids_dataset_description('dataset_description.yml', bids_dir) # This is a BIDS mandatory file

    subprocess.run(["rm", "-r", f'{bids_dir}/tmp_dcm2bids'], check=True) # Removing the dcm2bids temp dir

    if config['BIDS_validate']:
        pull_and_run_bids_validator(temp_dir, bids_dir) # Running the BIDS validator 

    if config['clean_up']:
        subprocess.run(["rm", "-r", temp_dir], check=True) # Removing the temp dir