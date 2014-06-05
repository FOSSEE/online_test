#include <stdio.h>
#include <stdlib.h>

extern bool lessThan9(int);

template <class T>

void check(T expect, T result)
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
	result = lessThan9(10);
	printf("Input submitted to the function: 10");
	check(false, result);
	result = lessThan9(17);
	printf("Input submitted to the function: 17");
	check(true, result);
	result = lessThan9(16);
	printf("Input submitted to the function: 16");
	check(true, result);
	result = lessThan9(15);
	printf("Input submitted to the function: 15");
	check(false, result);
	printf("All Correct\n");
	return 0;
}
