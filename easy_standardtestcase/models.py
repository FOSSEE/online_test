from django.db import models
from django.utils import timezone


languages = (
        ("python", "Python"),
        ("bash", "Bash"),
        ("c", "C Language"),
        ("cpp", "C++ Language"),
        ("java", "Java Language"),
        ("scilab", "Scilab"),
    )


class easy_standardtestcase(models.Model):
    lang=models.CharField(max_length=24, choices=languages, null=True)
    function = models.TextField()
    typeval=models.CharField(max_length=200)
    inputVals = models.CharField(max_length=200)
    operator=models.CharField(max_length=200)
    output = models.IntegerField()
    final_standardtestcase=models.TextField()
    #def __str__(self):
    #    return self.function