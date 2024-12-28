import flywheel
import os
import tarfile
import shutil
from concurrent.futures import ThreadPoolExecutor
import zipfile
import subprocess

# Initialize Flywheel client with your API key
api_key = 'key'  # Replace with your Flywheel API key
fw = flywheel.Client(api_key=api_key)

config_file = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/flywheel_2_BIDS/dcm2bids_config.json'

def unzip_files_in_directory(directory, pattern):
    extract_path = os.path.join(directory, 'dicoms')
    os.makedirs(extract_path, exist_ok=True)

    for item in os.listdir(directory):
        if item.endswith(pattern):
            file_path = os.path.join(directory, item)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)  # Unzipping
            print(f'Unzipped: {file_path}')

def copy_matching_folders(source_directory, target_directory, search_strings, exclude_strings):
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True) 

    # Walk through the source directory
    for root, dirs, files in os.walk(source_directory):
        for dir_name in dirs:
            # Check if any of the search strings are in the directory name
            if any(s in dir_name for s in search_strings) and not any(e in dir_name for e in exclude_strings):
                # Create the full path to the source directory
                full_dir_path = os.path.join(root, dir_name)
                selected_scan_path = os.path.join(target_directory, dir_name)
                # Copy the directory to the target directory
                shutil.copytree(full_dir_path, selected_scan_path, dirs_exist_ok=True)
                print(f'Copied: {full_dir_path} to {target_directory}')
                dcm_path = unzip_files_in_directory(selected_scan_path, 'dicom.zip')

def convert2bids(dcm_path, bids_id, final_bids_path):

    print('test')


    command = ["dcm2bids", "-d", dcm_path, "-p", bids_id, "-c", config_file, "-o", final_bids_path, "--auto_extract_entities", "--force_dcm2bids"]

    print(command)

    try:
        subprocess.run(command, check=True)  # Execute the command and check for errors
        print(f"conversion completed successfully for subject: {ivim_id}")
        subprocess.run(["rm", "-r", bids_path+'/bids/tmp_dcm2bids'], check=True) # Removing the temporary files

    except subprocess.CalledProcessError as error:
        print(f"conversion failed with error: {error}")



def download_and_filter_subject_scans(subject_id, output_dir, scan_names, exclude_strings, bids_dir, force_download):
    """
    Downloads and filters scans for a given subject.

    :param subject_id: Subject ID to download scans from
    :param output_dir: Directory to save the downloaded scans
    :param scan_names: List of scan names to keep
    :param force_download: Boolean to force download even if file exists
    """
    subject = fw.lookup(f'mormino/Lucas_PETMR/{subject_id}')  # Lookup subject by ID

    if not subject:
        print(f"Subject {subject_id} not found.")
        return

    # Create the output directory if it doesn't exist
    subj_out_dir = os.path.join(output_dir, f'download_fw/{subject_id}')
    os.makedirs(subj_out_dir, exist_ok=True)

    scan_data = fw.sessions.find(f'subject.code={subject_id}')

    if not scan_data:
        print(f"No sessions found for subject {subject_id}.")
        return

    # Define the tar file path
    tar_file_path = f'{subj_out_dir}/{subject_id}.tar'

    # Only download if the tar file does not exist or if force_download is True
    if not os.path.exists(tar_file_path) or force_download:
        try:
            fw.download_tar(scan_data, tar_file_path)
            print(f"Successfully downloaded: {subject_id}")
        except Exception as e:
            print(f"Error downloading {subject_id}: {e}")
            return
    else:
        print(f"Tar file already exists for {subject_id}. Skipping download.")

    # Extract the tar file
    """try:
        with tarfile.open(tar_file_path) as tar:
            tar.extractall(subj_out_dir)
            print(f"Extracted tar for subject: {subject_id}")
    except Exception as e:
        print(f"Error extracting tar for {subject_id}: {e}")
        return"""

    # Check only the last directory for files that match the specified scan names, Also excluding specifiled files by a string
    sorted_path = f'{output_dir}sorted_fw/{subject_id}'
    #copy_matching_folders(subj_out_dir, sorted_path, scan_names, exclude_strings)
    convert2bids(sorted_path, subject_id, bids_dir)

    #os.remove(subj_out_dir) # Cleaning up


def download_scans(subject_ids, output_dir, num_threads, scan_names, exclude_strings, bids_dir, force_download):
    """
    Downloads specific scans from a list of subjects in parallel.

    :param subject_ids: List of subject IDs to download scans from
    :param output_dir: Directory to save the downloaded scans
    :param num_threads: Number of threads to use for downloading scans
    :param scan_names: List of scan names to keep
    :param force_download: Boolean to force download even if file exists
    """
    # Use ThreadPoolExecutor to handle parallel downloads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(lambda subject_id: download_and_filter_subject_scans(subject_id, output_dir, scan_names, exclude_strings, bids_dir, force_download), subject_ids)

if __name__ == "__main__":
    # Specify your subject IDs and scan names
    subject_ids = ['PI443', 'PI444']  # Replace with actual subject IDs
    output_dir = '/mnt/poston/projects/parkinsons/postonlab/EvaETP_IVIM/'  # Specify output directory
    num_threads = 5  # Set the number of threads as per your requirement
    #scan_names = ['DTI_108_7s_2thick_2space_DL', 'DTI_84_7s_2thick_2space_DL_pepolar', 'CLARiTI_Accelerated_Sagittal']  # Scans to keep
    scan_names = ['CLARiTI_Accelerated_Sagittal']  # Scans to keep
    exclude_strings = ['SOURCE']  # This is IVIM specific exclusion criteria, Leave empty if no exclusions
    force_download = False  # Set to True to force re-download

    bids_dir = f'{output_dir}/test_fw_bids'
    os.makedirs(bids_dir, exist_ok=True)

    print(bids_dir)

    download_scans(subject_ids, output_dir, num_threads, scan_names, exclude_strings, bids_dir, force_download)