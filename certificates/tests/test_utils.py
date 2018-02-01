import unittest
import os
from textwrap import dedent

from certificates.formatters.utils import render_certificate_template, CUR_DIR

class TestRenderCertificateTemplate(unittest.TestCase):
    def setUp(self):
        self.template_path = CUR_DIR
        self.template_name = 'base_template.html'
        self.expected_output = (
            '<html lang="en">\n    <head>\n'
            '        <meta charset="utf-8">\n        <meta http-equiv="X-UA-Compatible"'
            ' content="IE=edge">\n        <meta name="viewport" content="width=device-width,'
            ' initial-scale=1">\n        <meta name="description" content="">\n'
            '        <meta name="author" content="">\n'
            '        <title>Certificate</title>\n'
            '        <link href="http://getbootstrap.com/dist/css/bootstrap.min.css"'
            ' rel="stylesheet">\n    </head>\n\n    <body>\n'
            '        <div class="container">\n            test html\n'
            '        </div>\n    </body>\n</html>'
        )

    def test_render_certificate_template(self):
        context = {'html_content': "test html"}
        template_path = os.path.join(self.template_path, self.template_name)
        output = render_certificate_template(template_path, context)
        self.assertEquals(self.expected_output, output)

if __name__ == '__main__':
    unittest.main()
