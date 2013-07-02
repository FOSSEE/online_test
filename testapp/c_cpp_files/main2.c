#include <stdio.h>
#include <stdlib.h>

extern int add(int, int, int);

template <class T>
void check(T expect,T result)
{
    if (expect == result)
    {
	printf("\nCorrect:\n Expected %d got %d \n",expect,result);
    }
    else 
    {
	printf("\nIncorrect:\n Expected %d got %d \n",expect,result);
	exit (0);
   }
}

int main(void)
{
	int result;
	result = add(0,0,0);
        printf("Input submitted to the function: 0, 0, 0");
	check(0, result);
	result = add(2,3,3);
        printf("Input submitted to the function: 2, 3, 3");
	check(8,result);
	printf("All Correct\n");
}
