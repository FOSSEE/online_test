#include <stdio.h>
#include <stdlib.h>

extern  bool array_check_all(int []);

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
	int a[] = {1,2,3,2,8};
	result = array_check_all(a);
	printf("Input submitted to the function: {1, 2, 3, 2, 8}");
	check(false, result);
	int b[] = {4,2,32,4,56};
	result = array_check_all(b);
	printf("Input submitted to the function: {4, 2, 32, 4, 56}");
	check(true, result);
	printf("All Correct\n");
	return 0;
}
