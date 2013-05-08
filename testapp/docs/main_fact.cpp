#include <stdio.h>
#include <stdlib.h>

extern int factorial(int);

template <class T>

void check(T expect, T result)
{
    if (expect == result)
    {
	//printf("Correct:\n Expected %d got %d \n",expect,result);
    }
    else 
    {
	printf("Incorrect:\n Expected %d got %d \n",expect,result);
	exit (0);
   }
}

int main(void)
{
	int result;
	result = factorial(0);
	check(1, result);
	result = factorial(3);
	check(6, result);
	printf("All Correct\n");
}
