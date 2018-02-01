from jinja2 import Environment, FileSystemLoader
import os

CUR_DIR = os.path.abspath(os.path.dirname(__file__))

def render_certificate_template(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    template_loader = FileSystemLoader(path)
    rendering_env = Environment(loader=template_loader)
    template = rendering_env.get_template(filename)
    return template.render(context)

class HTMLFormatter(object):
    def __init__(self, html_content):
        self.html_content = html_content
        self.base_template_name = 'base_template.html'
        self.base_template_dir = CUR_DIR

    def get_response(self):
        context = {'html_content': self.html_content}
        base_template_path = os.path.join(self.base_template_dir, self.base_template_name)
        return render_certificate_template(base_template_path, context)
