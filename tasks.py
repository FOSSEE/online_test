from __future__ import print_function
import os
import sys
import shutil
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

import invoke
from invoke import task

from yaksh.settings import SERVER_POOL_PORT

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
TARGET_CONTAINER_NAME = 'yaksh_code_server'
SRC_IMAGE_NAME = 'fossee/yaksh_codeserver'
CHECK_FILE = 'server_running.txt'
CHECK_FILE_PATH = os.path.join(SCRIPT_DIR, 'yaksh_data', CHECK_FILE)
OS_NAME = sys.platform


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remove_check_file(path):
    if os.path.isfile(path):
        os.remove(path)

def run_as(os_name):
    if os_name.startswith('linux') or os_name == 'darwin':
        return 'sudo'
    elif os_name.startswith('Win32'):
        return None

def get_cmd(run_as_cmd, base_cmd):
    if run_as_cmd:
        return '{0} {1}'.format(run_as_cmd, base_cmd)
    else:
        return base_cmd

@task
def setupdb(ctx):
    print("** Setting up & migrating database **")
    ctx.run("python manage.py makemigrations")
    ctx.run("python manage.py migrate")
    ctx.run("python manage.py loaddata demo_fixtures.json")

@task(setupdb)
def serve(ctx):
    print("** Running the Django web server. Press Ctrl-C to Exit **")
    ctx.run("python manage.py runserver")

@task
def clean(ctx):
    print("** Discarding database **")
    ctx.run("rm -rf {0}".format(os.path.join(SCRIPT_DIR, 'db.sqlite3')))

@task
def getimage(ctx, image=SRC_IMAGE_NAME):
    try:
        base_cmd = "docker inspect {0}".format(image)
        run_as_cmd = run_as(OS_NAME)
        cmd = get_cmd(run_as_cmd, base_cmd)
        ctx.run(cmd, hide=True)
    except invoke.exceptions.Failure:
        print("The docker image {0} does not exist locally".format(image))
        print("\n** Pulling latest image <{0}> from docker hub **".format(image))
        base_cmd = "docker pull {0}".format(image)
        run_as_cmd = run_as(OS_NAME)
        cmd = get_cmd(run_as_cmd, base_cmd)
        ctx.run(cmd)
        print("\n** Done! Successfully pulled latest image <{0}> **".format(image))

@task
def start(ctx, ports=SERVER_POOL_PORT, image=SRC_IMAGE_NAME, unsafe=False,
    version=3):
    if unsafe:
        with ctx.cd(SCRIPT_DIR):
            print("** Initializing local code server **")
            base_cmd = "python{0} -m yaksh.code_server".format(
                version
            )
            run_as_cmd = run_as(OS_NAME)
            cmd = get_cmd(run_as_cmd, base_cmd)
            ctx.run(cmd)
    else:
        cmd_params = {'ports': ports,
            'image': SRC_IMAGE_NAME,
            'name': TARGET_CONTAINER_NAME,
            'vol_mount': os.path.join(SCRIPT_DIR, 'yaksh_data'),
            'command': 'sh {0}'.format(
                os.path.join(SCRIPT_DIR,
                'yaksh_data', 'yaksh', 'scripts', 'yaksh_script.sh')
            )
        }

        remove_check_file(CHECK_FILE_PATH)
        getimage(ctx, image=SRC_IMAGE_NAME)

        print("** Preparing code server **")
        create_dir(os.path.join(SCRIPT_DIR, 'yaksh_data', 'data'))
        create_dir(os.path.join(SCRIPT_DIR, 'yaksh_data', 'output'))

        copy_tree(
            os.path.join(SCRIPT_DIR, 'yaksh'),
            os.path.join(SCRIPT_DIR, 'yaksh_data', 'yaksh')
        )

        copy_file(
            os.path.join(SCRIPT_DIR, 'requirements', 'requirements-codeserver.txt'),
            os.path.join(SCRIPT_DIR, 'yaksh_data')
        )

        print("** Initializing code server within docker container **")
        base_cmd = "docker run \
            -dp {ports}:{ports} --name={name} \
            -v {vol_mount}:{vol_mount} \
            -w {vol_mount} \
            {image} {command}".format(**cmd_params)
        run_as_cmd = run_as(OS_NAME)
        cmd = get_cmd(run_as_cmd, base_cmd)
        ctx.run(cmd)

        while not os.path.isfile(CHECK_FILE_PATH):
            print("** Checking code server status. Press Ctrl-C to exit **\r", end="")
        print("\n** Code server is up and running successfully **")


@task
def stop(ctx, container=TARGET_CONTAINER_NAME, hide=True):
    base_filter_cmd = "docker ps -q --filter='name={0}'".format(container)
    run_as_cmd = run_as(OS_NAME)
    cmd = get_cmd(run_as_cmd, base_filter_cmd)
    result = ctx.run(cmd)

    remove_check_file(CHECK_FILE_PATH)
    if result.stdout:
        print ("** Stopping the docker container <{0}>".format(container))
        base_stop_cmd = "docker stop {0}".format(container)
        cmd = get_cmd(run_as_cmd, base_stop_cmd)
        ctx.run(cmd)
        print ("** Done! Stopped the docker container <{0}>".format(container))

        print ("** Discarding the docker container <{0}>".format(container))
        base_rm_cmd = "docker rm {0}".format(container)
        cmd = get_cmd(run_as_cmd, base_rm_cmd)
        ctx.run(cmd)
        print ("** Done! Discarded the docker container <{0}>".format(container))
    else:
        print("** Docker container <{0}> not found **".format(container))
