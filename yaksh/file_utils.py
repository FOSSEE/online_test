from __future__ import absolute_import
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
            z_files = extract_files(file_name)
            for file in z_files:
                files.append(file)
    return files


def delete_files(files):
    """ Delete Files from current directory """

    for file in files:
        if os.path.exists(file):
            if os.path.isfile(file):
                os.remove(file)
            else:
                shutil.rmtree(file)


def extract_files(zip_file):
    zfiles = []
    if zipfile.is_zipfile(zip_file):
        zip_file = zipfile.ZipFile(zip_file, 'r')
        for z_file in zip_file.namelist():
            zfiles.append(z_file)
        zip_file.extractall()
        zip_file.close()
        return zfiles

