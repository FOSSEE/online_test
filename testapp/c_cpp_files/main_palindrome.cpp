#include <stdio.h>
#include <stdlib.h>

extern bool palindrome(int);

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
	result = palindrome(123);
        printf("Input submitted to the function: 123");
	check(false, result);
	result = palindrome(121);
        printf("Input submitted to the function: 121");
	check(true, result);
	printf("All Correct\n");
	return 0;
}
