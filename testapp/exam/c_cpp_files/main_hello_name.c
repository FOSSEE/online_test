#include <stdio.h>
#include <stdlib.h>


void check(char expect[], char result[])
{
    if (expect == result)
    {
	printf("Correct:expected %s got %s \n",expect,result);
    }
    else 
    {
	printf("ERROR:expected %s got %s \n",expect,result);
	exit (0);
   }
}

int main(void)
{
	char result[20];
	char A[20]=" pratham";
	char B[20]=" sir";
 	result[20] = message(A);
        printf("%s",result);
	check("hello pratham", result);
	result[20] = message(B);
	check("hello sir",result);
	printf("All Correct\n");
}
