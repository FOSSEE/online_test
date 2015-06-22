from __future__ import print_function

import subprocess
import contextlib
import os
from os import path
import argparse
from importlib import import_module
from django.conf import settings
from django.core import management
from django.template import Template, Context, loader

from project_detail import NAME, PATH 

CUR_DIR = os.getcwd()
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
TEMPLATE_DIR = path.join(PARENT_DIR, 'templates')

def main():
    #Parse command-line to obtain the arguments and/or options
    # create top-level parser object
    parser = argparse.ArgumentParser(prog="vimarsh")
    subparser = parser.add_subparsers(dest="subcommand")

    # create parser for the "create_demo" subcommand
    create_demo_parser = subparser.add_parser("create_demo",
                                        help="Create a new demo Django project")
    create_demo_parser.add_argument("project_name", type=str,
                                        help="name of demo Django project")
    create_demo_parser.add_argument("-p", "--path", type=str,
                                        help="path of demo Django project")
    
    # create parser for the "run_demo" subcommand
    run_demo_parser = subparser.add_parser("run_demo",
                        help="Initialise django server and run the demo project")

    # create parser for the "run_code_server" subcommand
    code_server_parser = subparser.add_parser("run_code_server",
                                                help="Initialise Vimarsh code server")
    code_server_parser.add_argument("-P", "--ports", type=int, nargs='+', 
                                        help="code server ports")

    args = parser.parse_args()

    if args.subcommand == "create_demo":
        if args.path:
            create_demo(args.project_name, args.path)
        else:
            create_demo(args.project_name)

    elif args.subcommand == "run_demo":
        try:
            run_demo(NAME, PATH)
        except Exception as e:
            if not NAME or not PATH:
                print("Error: Unable to find Project Name or Path variables\n")
            else:
                print("Error: {0}\n".format(e))
            subparser.print_help()

    elif args.subcommand == "run_code_server":
        if args.ports:
            run_server(args.ports)
        else:
            run_server()

def create_demo(project_name='vimarsh_demo', project_dir=CUR_DIR):
    try:
        management.call_command('startproject', project_name, project_dir)
        print("Demo Django project '{0}' created at '{1}'".format(project_name,
                                                                project_dir))
    except Exception, e:
        print("Error: {0}\nExiting Vimarsh Installer".format(e))

    if project_dir is None:
        top_dir = path.join(os.getcwd(), project_name)
    else:
        top_dir = project_dir

    project_path = path.join(top_dir, project_name)
    # Store project details
    _set_project_details(project_name, top_dir)

    with _chdir(project_path):
        root_urlconf = "{0}.{1}".format(project_name, 'demo_urls')
        settings_template_path = path.join(TEMPLATE_DIR, 'demo_settings.py')
        settings_target_path = path.join(project_path, 'demo_settings.py')
        settings_context = Context({'project_name': project_name, # 'custom_apps': custom_apps, 
                        'root_urlconf': root_urlconf})
        urls_template_path = path.join(TEMPLATE_DIR, 'demo_urls.py')
        urls_target_path = path.join(project_path, 'demo_urls.py')
        command = ("python ../manage.py syncdb "
                        "--noinput --settings={0}.demo_settings").format(project_name)

        # Create demo_settings file
        _render_demo_files(settings_template_path, settings_target_path, settings_context)
        # Create demo_urls file 
        _render_demo_files(urls_template_path, urls_target_path)
        # Run syncdb
        subprocess.call(command, shell=True)

def run_demo(project_name, top_dir):
    with _chdir(top_dir):
        project_path = path.join(top_dir, 'manage.py')
        command = ("python manage.py runserver "
                        "--settings={0}.demo_settings").format(project_name)
        subprocess.call(command, shell=True)

def run_server():
    try:
        from testapp.exam import code_server
        code_server.main()
    except Exception as e:
        print("Error: {0}\nExiting Vimarsh code server".format(e))

def _set_project_details(project_name, top_dir):
    file_path = path.join(SCRIPT_DIR, 'project_detail.py')
    detail = "NAME ='{0}'\nPATH ='{1}'".format(project_name, top_dir)
    with open(file_path, 'w') as data_store:
        data_store.write(detail)

def _render_demo_files(template_path, output_path, context=None):
    with open(template_path, 'r') as template_file:
        content = template_file.read()
        if context:
            content = content.decode('utf-8')
            template = Template(content)
            content = template.render(context)
            content = content.encode('utf-8')

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
