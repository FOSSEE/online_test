#include <stdio.h>
#include <stdlib.h>

extern bool palindrome(int);

template <class T>

void check(T expect, T result)
{
    if (expect == result)
    {
	//printf("Correct:\n Expected %d got %d \n",expect,result);
    }
    else 
    {
	printf("Incorrect:\n Expected %d got %d \n",expect,result);
	exit (0);
   }
}

int main(void)
{
	bool result;
	result = palindrome(123);
	check(false, result);
	result = palindrome(121);
	check(true, result);
	printf("All Correct\n");
}
