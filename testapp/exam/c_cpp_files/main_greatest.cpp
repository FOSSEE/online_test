#include <stdio.h>
#include <stdlib.h>

extern int greatest(int, int, int);

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
	result = greatest(1, 2, 3);
        printf("Input submitted to the function: 1, 2, 3");
	check(3, result);
	result = greatest(5, 9, 2);
        printf("Input submitted to the function: 5, 9, 2");
	check(9, result);
	result = greatest(7, 2, 4);
        printf("Input submitted to the function: 7, 2, 4");
	check(7, result);
        result = greatest(11, 2, 45);
        printf("Input submitted to the function: 11, 2, 45");
        check(45, result);
        result = greatest(2, 7, 0);
        printf("Input submitted to the function: 2, 7, 0");
        check(7, result);
        result = greatest(9, 6, 5);
        printf("Input submitted to the function: 9, 6, 5");
        check(9, result);
	printf("All Correct\n");
	return 0;
}
