#include <stdio.h>
#include <stdlib.h>

extern int blackJack(int, int);

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
	result = blackJack(11, 12);
        printf("Input submitted to the function: 11, 12");
	check(12, result);
	result = blackJack(15, 19);
        printf("Input submitted to the function: 15, 19");
	check(19, result);
	result = blackJack(10, 21);
        printf("Input submitted to the function: 10, 21");
	check(21, result);
        result = blackJack(31, 22);
        printf("Input submitted to the function: 31, 22");
        check(0, result);
        result = blackJack(91, 61);
        printf("Input submitted to the function: 91, 61");
        check(0, result);
	printf("All Correct\n");
	return 0;
}
