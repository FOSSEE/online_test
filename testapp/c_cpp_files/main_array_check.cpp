#include <stdio.h>
#include <stdlib.h>

extern  bool array_check(int [], int);

template <class T>

void check(T expect,T result)
{
    if (expect == result)
    {
	printf("\nCorrect:\n Expected %d got %d \n",expect,result);
    }
    else 
    {
	printf("\nIncorrect:\n Expected %d got %d \n",expect,result);
	exit (1);
   }
}

int main(void)
{
	bool result;
        int a[] = {1,2,3,0,0};
	result = array_check(a, 2);
        printf("Input submitted to the function: {1, 2, 3, 0, 0} and index 2");
	check(false, result);
	int b[] = {1,2,3,4,5};
       	result = array_check(b, 3);
        printf("Input submitted to the function: {1, 2, 3, 4, 5} and index 3");
	check(true, result);
	printf("All Correct\n");
	return 0;
}
