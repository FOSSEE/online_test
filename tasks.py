import invoke
from invoke import task
import os
from yaksh.settings import SERVER_POOL_PORT

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
TARGET_CONTAINER_NAME = 'yaksh_code_server'
SRC_IMAGE_NAME = 'yaksh_code_server_image'

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

@task
def setupdb(ctx):
    print("** Setting up & migrating database **")
    ctx.run("python manage.py migrate")

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
        result = ctx.run("sudo docker inspect {0}".format(image), hide=True)
    except invoke.exceptions.Failure:
        print("The docker image {0} does not exist locally".format(image))
        print("\nPulling latest image <{0}> from docker hub".format(image))
        ctx.run("sudo docker pull {0}".format(image))

@task
def start(ctx, ports=SERVER_POOL_PORT, image=SRC_IMAGE_NAME, unsafe=False):
    if unsafe:
        with ctx.cd(SCRIPT_DIR):
            ctx.run("sudo python -m yaksh.code_server")
    else:
        cmd_params = {'ports': ports,
            'image': SRC_IMAGE_NAME,
            'name': TARGET_CONTAINER_NAME,
            'vol_mount': os.path.join(SCRIPT_DIR, 'yaksh_data/'),
            'command': 'sh {0}'.format(
                os.path.join(SCRIPT_DIR,
                'yaksh_data/yaksh/scripts/yaksh_script.sh')
            )
        }

        getimage(ctx, image=SRC_IMAGE_NAME)

        create_dir(os.path.join(SCRIPT_DIR, 'yaksh_data/data'))
        create_dir(os.path.join(SCRIPT_DIR, 'yaksh_data/output'))

        ctx.run('cp -r {0} {1}'.format(
                os.path.join(SCRIPT_DIR, 'yaksh/'),
                os.path.join(SCRIPT_DIR, 'yaksh_data/')
            )
        )
        ctx.run('cp {0} {1}'.format(
                os.path.join(SCRIPT_DIR, 'requirements/requirements-codeserver.txt'),
                os.path.join(SCRIPT_DIR, 'yaksh_data')
            )
        )

        ctx.run(
            "sudo docker run \
            -dp {ports}:{ports} --name={name} \
            -v {vol_mount}:{vol_mount} \
            -w {vol_mount} \
            {image} {command}".format(**cmd_params)
        )

@task
def stop(ctx, container=TARGET_CONTAINER_NAME, hide=True):
    result = ctx.run("sudo docker ps -q --filter='name={0}'".format(container))
    if result.stdout:
        print ("** Discarding the docker container <{0}>".format(container))
        ctx.run("sudo docker rm {0}".format(container))
    else:
        print("** Docker container <{0}> not found **".format(container))
