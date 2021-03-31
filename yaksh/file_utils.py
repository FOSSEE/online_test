import shutil
import os
import zipfile
import tempfile
import csv
import asyncio
import os
import aiohttp
import async_timeout


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
            z_files, path = extract_files(file_name, os.getcwd())
            for file in z_files:
                files.append(file)
    return files


def delete_files(files, file_path=None):
    """ Delete Files from directory """
    for file_name in files:
        if file_path:
            file = os.path.join(file_path, file_name)
        else:
            file = os.path.join(os.getcwd(), file_name)
        if os.path.exists(file):
            if os.path.isfile(file):
                os.remove(file)
            else:
                shutil.rmtree(file)


def extract_files(zip_file, path=None):
    """ extract files from zip """
    zfiles = []
    if zipfile.is_zipfile(zip_file):
        zip_file = zipfile.ZipFile(zip_file, 'r')
        for z_file in zip_file.namelist():
            zfiles.append(z_file)
        if path:
            extract_path = path
        else:
            extract_path = tempfile.mkdtemp()
        zip_file.extractall(extract_path)
        zip_file.close()
        return zfiles, extract_path


def is_csv(document):
    ''' Check if document is csv with ',' as the delimiter'''
    try:
        try:
            content = document.read(1024).decode('utf-8')
        except AttributeError:
            document.seek(0)
            content = document.read(1024)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(content, delimiters=',')
        document.seek(0)
    except (csv.Error, UnicodeDecodeError):
        return False, None
    return True, dialect


class Downloader:
    async def get_url(self, url, path, session):
        file_name = url.split("/")[-1]
        if not os.path.exists(path):
            os.makedirs(path)
        async with async_timeout.timeout(120):
            async with session.get(url) as response:
                with open(os.path.join(path, file_name), 'wb') as fd:
                    async for data in response.content.iter_chunked(1024):
                        fd.write(data)
        return file_name

    async def download(self, urls, path):
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_url(url, path, session) for url in urls]
            return await asyncio.gather(*tasks)

    def main(self, urls, download_path):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.download(urls, download_path))

