#include <stdio.h>
#include <stdlib.h>

extern bool within(int, int, int);

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
	result = within(12, 3, 20);
        printf("Input submitted to the function: 12, 3, 20");
	check(true, result);
        result = within(12, 13, 20);
        printf("Input submitted to the function: 12, 13, 20");
	check(false, result);
        result = within(29, 13, 120);
        printf("Input submitted to the function: 29, 13, 120");
	check(true, result);
        result = within(12, 12, 20);
        printf("Input submitted to the function: 12, 3, 20");
	check(false, result);
	printf("All Correct\n");
	return 0;
}
