from __future__ import unicode_literals
import unittest

from utils import render_certificate_template, CUR_DIR

class RenderCertificateTemplateTest(unittest.TestCase):
    def setUp(self):
        self.template_path = CUR_DIR
        self.template_name = 'base_template.html'
        self.expected_output = dedent("""
            <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta name="description" content="">
                    <meta name="author" content="">
                    <title>Certificate</title>
                    <link href="http://getbootstrap.com/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>

                <body>
                    <div class="container">
                        test html
                    </div>
                </body>
            </html>
            """
        )

    def assert_output(self, expected_output, actual_output):
        context = {'html_content': "test html"}
        template_path = os.path.join(self.template_path, self.template_name)
        output = render_certificate_template(template_path, context)
        self.assertEquals(self.expected_output, output)
