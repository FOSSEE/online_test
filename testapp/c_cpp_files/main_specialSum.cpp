#include <stdio.h>
#include <stdlib.h>

extern int specialSum(int,int,int);

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
	result = specialSum(10, 2, 9);
        printf("Input submitted to the function: 10, 2, 9");
	check(21, result);
	result = specialSum(1, 21, 9);
        printf("Input submitted to the function: 1, 21, 9");
	check(1, result);
        result = specialSum(21, 2, 3);
        printf("Input submitted to the function: 21, 2, 3");
	check(0, result);
        result = specialSum(10, 2, 21);
        printf("Input submitted to the function: 10, 2, 21");
	check(12, result);
        result = specialSum(10, 2, 6);
        printf("Input submitted to the function: 10, 2, 6");
	check(18, result);

        printf("All Correct\n");
	return 0;
}
