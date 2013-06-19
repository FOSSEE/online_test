#include <stdio.h>
#include <stdlib.h>

extern int greatest(int, int, int);

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
	result = greatest(1, 2, 3);
	check(3, result);
	result = greatest(5, 9, 2);
	check(9, result);
	result = greatest(7, 2, 4);
	check(7, result);
	printf("All Correct\n");
	return 0;
}
