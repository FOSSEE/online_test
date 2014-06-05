#include <stdio.h>
#include <stdlib.h>

extern bool mean(int, int , int);

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
        result = mean(11, 11, 11);
        printf("Input submitted to the function: 11, 121, 11");
	check(true, result);
	result = mean(16, 12, 9);
        printf("Input submitted to the function: 16, 144, 9");
	check(true, result);
	result = mean(19, 221, 9);
        printf("Input submitted to the function: 19, 221, 9");
	check(false, result);
	result = mean(34, 12, 3);
        printf("Input submitted to the function: 11, 121, 11");
	check(false, result);
	printf("All Correct\n");
	return 0;
}
