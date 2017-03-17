from __future__ import print_function

import django
import subprocess
import contextlib
import os
from os import path
import argparse
from django.conf import settings
from django.core import management
from django.template import Template, Context

CUR_DIR = os.getcwd()
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
TEMPLATE_DIR = path.join(PARENT_DIR, 'demo_templates')

settings.configure()
django.setup()


def main():
    # Parse command-line to obtain the arguments and/or options
    # create top-level parser object
    parser = argparse.ArgumentParser(prog="yaksh")
    subparser = parser.add_subparsers(dest="subcommand")

    # create parser for the "create_demo" subcommand
    create_demo_parser = subparser.add_parser(
        "create_demo",
        help="Create a new demo Django project"
    )
    create_demo_parser.add_argument(
        "path", type=str,
        default=path.join(CUR_DIR, "yaksh_demo"),
        nargs="?",
        help="Path to the demo Django project (defaults to 'yaksh_demo')"
    )

    # create parser for the "run_demo" subcommand
    run_parser = subparser.add_parser(
        "run",
        help="Initialise django server and run the demo project"
    )
    run_parser.add_argument(
        "path", type=str, nargs=1,
        help="full path to the demo yaksh project"
    )

    # create parser for the "run_code_server" subcommand
    code_server_parser = subparser.add_parser(
        "run_code_server",
        help="Initialise yaksh code server"
    )
    code_server_parser.add_argument("-P", "--ports", type=int, nargs='+',
                                    help="code server ports")

    args = parser.parse_args()

    if args.subcommand == "create_demo":
        pth = path.abspath(args.path)
        name = path.basename(pth)
        create_demo(name, pth)
    elif args.subcommand == "run":
        pth = path.abspath(args.path[0])
        name = path.basename(pth)
        run_demo(name, pth)
    elif args.subcommand == "run_code_server":
        if args.ports:
            run_server(args.ports)
        else:
            run_server()


def create_demo(project_name='yaksh_demo', project_dir=CUR_DIR):
    if not path.exists(project_dir):
        os.makedirs(project_dir)
    try:
        management.call_command('startproject', project_name, project_dir)
        print("Demo Django project '{0}' created at '{1}'".format(
            project_name, project_dir)
        )
    except Exception as e:
        print("Error: {0}\nExiting yaksh Installer".format(e))

    if project_dir is None:
        top_dir = path.join(os.getcwd(), project_name)
    else:
        top_dir = project_dir

    project_path = path.join(top_dir, project_name)
    fixture_dir = path.join(PARENT_DIR, 'fixtures')
    fixture_path = path.join(fixture_dir, 'demo_fixtures.json')

    with _chdir(project_path):
        root_urlconf = "{0}.{1}".format(project_name, 'demo_urls')
        settings_template_path = path.join(TEMPLATE_DIR, 'demo_settings.py')
        settings_target_path = path.join(project_path, 'demo_settings.py')
        settings_context = Context({'project_name': project_name,
                                    'root_urlconf': root_urlconf,
                                    'fixture_dir': fixture_dir})
        urls_template_path = path.join(TEMPLATE_DIR, 'demo_urls.py')
        urls_target_path = path.join(project_path, 'demo_urls.py')
        loaddata_command = ("python ../manage.py loaddata "
                            "--settings={0}.demo_settings {1}").format(
                                project_name, fixture_path)

        # Create demo_settings file
        _render_demo_files(
            settings_template_path, settings_target_path, settings_context
        )
        # Create demo_urls file
        _render_demo_files(urls_template_path, urls_target_path)
        # Create database and load initial data
        command_path = path.join(top_dir, 'manage.py')
        _check_migrations(project_name, command_path)
        _migrate(project_name, command_path)
        subprocess.call(loaddata_command, shell=True)


def run_demo(project_name, top_dir):
    with _chdir(top_dir):
        command_path = path.join(top_dir, 'manage.py')
        _check_migrations(project_name, command_path)
        _migrate(project_name, command_path)
        command = ("python manage.py runserver "
                   "--settings={0}.demo_settings").format(project_name)
        subprocess.call(command, shell=True)


def run_server(args=None):
    try:
        from yaksh import code_server
        code_server.main(args)
    except Exception as e:
        print("Error: {0}\nExiting yaksh code server".format(e))


def _check_migrations(project_name, command_path):
    migrations = ("python {0} makemigrations --settings={1}.demo_settings"
        ).format(command_path, project_name)
    subprocess.call(migrations, shell=True)


def _migrate(project_name, command_path):
    migrate = ("python {0} migrate --settings={1}.demo_settings"
        ).format(command_path, project_name)
    subprocess.call(migrate, shell=True)


def _render_demo_files(template_path, output_path, context=None):
    with open(template_path, 'r') as template_file:
        content = template_file.read()
        if context:
            template = Template(content)
            content = template.render(context)

    with open(output_path, 'w') as new_file:
        new_file.write(content)


@contextlib.contextmanager
def _chdir(path):
    starting_directory = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(starting_directory)


if __name__ == '__main__':
    main()
