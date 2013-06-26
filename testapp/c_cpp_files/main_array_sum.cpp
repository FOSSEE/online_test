#include <stdio.h>
#include <stdlib.h>

extern int array_sum(int []);

template <class T>

void check(T expect,T result)
{
    if (expect == result)
    {
	//printf("Correct:\n Expected %d got %d \n",expect,result);
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
        int a[] = {1,2,3,0,0};
	result = array_sum(a);
	check(6, result);
	int b[] = {1,2,3,4,5};
	result = array_sum(b);
	check(15,result);
	printf("All Correct\n");
	return 0;
}
