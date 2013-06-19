#include <stdio.h>
#include <stdlib.h>

extern int add(int, int);

template <class T>

void check(T expect, T result)
{
    if (expect == result)
    {
	//printf("Correct:\n Expected %d got %d \n",expect,result);
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
	result = add(0,0);
	check(0, result);
	result = add(2,3);
	check(5,result);
	printf("All Correct\n");
	return 0;
}
