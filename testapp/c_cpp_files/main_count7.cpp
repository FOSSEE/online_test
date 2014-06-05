#include <stdio.h>
#include <stdlib.h>

extern int count7(int[]);

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
	int arr[4] = {2,3,4,5};
	result = count7(arr);
	printf("Input submitted to the function: [2, 3, 4, 5]");
	check(0, result);
	int arr2[4] = {1,2,17,9};
	result = count7(arr2);
	printf("Input submitted to the function: [1, 2, 17, 9]");
	check(0, result);
	int arr3[4] = {7,9,2,1};
	result = count7(arr3);
	printf("Input submitted to the function: [7, 9, 2, 1]");
	check(1, result);
	int arr4[4] = {1,7,7,7};
	result = count7(arr4);
	printf("Input submitted to the function: [1, 7, 7, 7]");
	check(3, result);
	printf("All Correct\n");
	return 0;
}
