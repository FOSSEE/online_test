from yaksh.models import EasyStandardTestCase

def template_c(fn,inp,out,temp2,temp3,typevar):
	for y in temp3:
		temp4=y['id']
	    # print("easy tc id", temp4)
		temp5=EasyStandardTestCase.objects.get(testcase_ptr=temp4)
	    # temp5.test_case='#include <stdio.h>\n#include <stdlib.h>\n#include <assert.h>\nextern int '+ fn +'('+typevar+');'+'\nint main(void)\n{\nint result;\nresult = '+ fn+'('+inp+');' +'\nassert(result=='+out+');\n}'
	    # print ("test_case====",temp5.test_case)
		temp5.test_case='''#include <stdio.h>
		#include <stdlib.h>

		extern int {0}({1});

		int main(void)
		{4}
	    	int result;
	    	result = {0}({2});
	    	assert(result=={3});
	    
		{5}'''.format(fn,typevar,inp,out,'{','}')
		temp5.save()