from jinja2 import Environment, FileSystemLoader
import os
import pdfkit

CUR_DIR = os.path.abspath(os.path.dirname(__file__))

def render_certificate_template(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    template_loader = FileSystemLoader(path)
    rendering_env = Environment(loader=template_loader)
    template = rendering_env.get_template(filename)
    return template.render(context)

def _fetch_files(path, ext):
    file_list = []
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            if os.path.splitext(f)[1] == ext:
                file_list.append(f)
    return file_list if file_list else None


class HTMLFormatter(object):
    def __init__(self, html_content):
        self.html_content = html_content
        self.base_template_name = 'base_template.html'
        self.base_template_dir = CUR_DIR

    def get_response(self):
        context = {'html_content': self.html_content}
        base_template_path = os.path.join(self.base_template_dir, self.base_template_name)
        return render_certificate_template(base_template_path, context)

class PDFFormatter(object):
    def __init__(self, template_path, html):
        self.css_files = []
        self.template_path = template_path
        self.html = html

    def fetch_css_files(self):
        return _fetch_files(self.template_path, 'css')

    def get_pdf(self):
        return pdfkit.from_string(self.html, output_path=False, css=self.fetch_css_files())
