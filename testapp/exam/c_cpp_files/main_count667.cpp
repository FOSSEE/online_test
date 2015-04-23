#include <stdio.h>
#include <stdlib.h>

extern int count667(int[]);

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
	int arr[5] = {2,6,4,5,6};
	result = count667(arr);
	printf("Input submitted to the function: [2, 6, 4, 5,6]");
	check(0, result);
	int arr2[5] = {6,6,2,17,9};
	result = count667(arr2);
	printf("Input submitted to the function: [6, 6, 2, 17, 9]");
	check(1, result);
	int arr3[5] = {6,6,6,7,1};
	result = count667(arr3);
	printf("Input submitted to the function: [6, 6, 7, 2, 1]");
	check(3, result);
	int arr4[5] = {6,7,7,6,6};
	result = count667(arr4);
	printf("Input submitted to the function: [6, 7, 7, 6, 6]");
	check(2, result);
	printf("All Correct\n");
	return 0;
}
