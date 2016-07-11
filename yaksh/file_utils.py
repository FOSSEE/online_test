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
        if extract:
            unzip = zipfile.ZipFile(file_name)
            for zip_files in unzip.namelist():
                files.append(zip_files)
            unzip.extractall()
            unzip.close()
    return files


def delete_files(files):
    """ Delete Files from current directory """

    for content in files:
        if os.path.exists(content):
            if os.path.isfile(content):
                os.remove(content)
            else:
                shutil.rmtree(content)
