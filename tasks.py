import invoke
from invoke import task
import os
from yaksh.settings import SERVER_POOL_PORT


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
TARGET_CONTAINER_NAME = 'yaksh_code_server'
SRC_IMAGE_NAME = 'yaksh_image'

def create_dir(path):
    if not os.path.exists(path):
            ctx.run("mkdir {0}".format(path))

@task
def setupdb(ctx):
    print("** Setting up & migrating database **")
    ctx.run("python manage.py migrate")

@task(setupdb)
def run(ctx):
    print("** Running the Django web server **")
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
def runcodeserver(ctx, ports=SERVER_POOL_PORT, image=SRC_IMAGE_NAME, unsafe=False):
    if unsafe:
        with ctx.cd(SCRIPT_DIR):
            ctx.run("sudo python -m yaksh.code_server")
    else:
        cmd_params = {'ports': ports,
            'image': SRC_IMAGE_NAME,
            'name': TARGET_CONTAINER_NAME,
            'vol_mount_dest': '/src/online_test/',
            'vol_mount_src': os.path.join(SCRIPT_DIR),
            'command': 'sh /src/yaksh_script.sh',
        }

        getimage(ctx, image=SRC_IMAGE_NAME)

        create_dir(os.path.join(SCRIPT_DIR, 'output/'))
        create_dir(os.path.join(SCRIPT_DIR, 'yaksh/data/'))

        ctx.run(
            "sudo docker run --privileged \
            -dp {ports}:{ports} --name={name} \
            -v {vol_mount_src}:{vol_mount_dest} \
            {image} {command}".format(**cmd_params)
        )
