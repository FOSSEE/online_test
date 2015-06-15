import subprocess
import contextlib
import os
from os import path
import argparse
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
    help_msg = ("Enter the subcommand to be executed.\n"
    "Available subcommands:\n"
    " - create_demo <projectname> [destination-path]\n"
    " - run_demo")

    parser = argparse.ArgumentParser(prog="vimarsh", 
                                        usage="vimarsh.py subcommand [args]",
                                        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("subcommand", type=str, nargs='+', help=help_msg)
    args = parser.parse_args()

    if args.subcommand[0] == "create_demo":
        if len(args.subcommand) > 3 or len(args.subcommand) <= 1:
            parser.print_help()
        elif len(args.subcommand) == 3:
            project_name = args.subcommand[1]
            project_dir = args.subcommand[2]
            create_demo(args.subcommand[1], args.subcommand[2])
        else:
            project_name = args.subcommand[1]
            create_demo(args.subcommand[1])

    elif args.subcommand[0] == "run_demo":
        if len(args.subcommand) != 1:
            parser.print_help()
        else:
            try:
                run_demo(NAME, PATH)
            except Exception, e:
                if not NAME or not PATH:
                    print "Error: Unable to find Project Name and Path variables\n"
                else:
                    print "Error: ", e, "\n"
                parser.print_help()

    else:
        parser.print_help()


def create_demo(project_name='vimarsh_demo', project_dir=None):
    try:
        management.call_command('startproject', project_name, project_dir)
        print "Demo Django project '{0}' created at '{1}'"
    except Exception, e:
        print "Error: ", e, "\nExiting Vimarsh Installer"

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
