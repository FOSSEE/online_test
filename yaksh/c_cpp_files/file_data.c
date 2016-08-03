#include <stdio.h>
#include <stdlib.h>

extern int ans();

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
	result = ans();
	check(50, result);
}
