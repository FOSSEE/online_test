#include <stdio.h>
#include <stdlib.h>

extern bool check_digit(int, int);

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
	result = check_digit(12, 23);
        printf("Input submitted to the function: 12, 23");
	check(true, result);
	result = check_digit(22, 11);
        printf("Input submitted to the function: 121");
	check(false, result);
	printf("All Correct\n");
	return 0;
}
