import shutil
import os
import zipfile


def copy_files(file_paths):
    """ Copy Files to current directory, takes
    tuple with file paths and extract status"""

    files = []
    for src in file_paths:
        file_path, extract = src
        file_name = os.path.basename(file_path)
        files.append(file_name)
        shutil.copy(file_path, os.getcwd())
        if extract and zipfile.is_zipfile(file_name):
            unzip = zipfile.ZipFile(file_name)
            for zip_files in unzip.namelist():
                files.append(zip_files)
            unzip.extractall()
            unzip.close()
    return files


def delete_files(files):
    """ Delete Files from current directory """

    for file in files:
        if os.path.exists(file):
            if os.path.isfile(file):
                os.remove(file)
            else:
                shutil.rmtree(file)
