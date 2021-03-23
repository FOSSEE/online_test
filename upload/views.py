import tempfile
import os
from zipfile import ZipFile
from io import BytesIO as string_io

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from upload.utils import upload_course, write_course_to_file


def upload_course_md(request):
    if request.method == 'POST':
        status = False
        msg = None
        user = request.user
        course_upload_file = request.FILES.get('course_upload_md')
        file_extension = os.path.splitext(course_upload_file.name)[1][1:]
        if file_extension not in ['zip']:
            messages.warning(
                request, "Please upload zip file"
            )
        else:
            curr_dir = os.getcwd()
            try:
                with tempfile.TemporaryDirectory() as tmpdirname, ZipFile(course_upload_file, 'r') as zip_file:
                    zip_file.extractall(tmpdirname)
                    os.chdir(tmpdirname)
                    status, msg = upload_course(user)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.warning(request, f"Error parsing file structure: {e}")
            finally:
                os.chdir(curr_dir)

    return status, msg

def download_course_md(request, course_id):
    curr_dir = os.getcwd()
    zip_file_name = string_io()
    try:
        with tempfile.TemporaryDirectory() as tmpdirname, ZipFile(zip_file_name, 'w') as zip_file:
            os.chdir(tmpdirname)
            write_course_to_file(course_id)
            
            for foldername, subfolders, filenames in os.walk(tmpdirname):
                for filename in filenames:
                    zip_file.write(os.path.join(filename))
    except Exception as e:
        messages.warning(request, f"Error while downloading file: {e}")
    finally:
        os.chdir(curr_dir)

    zip_file_name.seek(0)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=course.zip'
    response.write(zip_file_name.read())

    return response