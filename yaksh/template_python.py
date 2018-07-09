from yaksh.models import EasyStandardTestCase

def template_python(fn,inp,out,temp2,temp3,op):
	for y in temp3:
	    temp4=y['id']
	    temp5=EasyStandardTestCase.objects.get(testcase_ptr=temp4)
	    temp5.test_case='assert ' + fn + '(' + inp + ')' + op + out
	    # print ("test_case====",temp5.test_case)
	    temp5.save()