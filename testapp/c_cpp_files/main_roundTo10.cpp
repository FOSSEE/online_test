#include <stdio.h>
#include <stdlib.h>

extern int roundTo10(int,int,int);

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
	int result;
	result = roundTo10(10, 22, 39);
	printf("Input submitted to the function: 10, 22, 39");
	check(70, result);
	result = roundTo10(45, 42, 39);
	printf("Input submitted to the function: 45, 42, 39");
	check(130, result);
	result = roundTo10(7, 3, 9);
	printf("Input submitted to the function: 7, 3, 9");
	check(20, result);
	result = roundTo10(1, 2, 3);
	printf("Input submitted to the function: 1, 2, 3");
	check(0, result);
	result = roundTo10(30, 40, 50);
	printf("Input submitted to the function: 30, 40, 50");
	check(120, result);
	printf("All Correct\n");
	return 0;
}
