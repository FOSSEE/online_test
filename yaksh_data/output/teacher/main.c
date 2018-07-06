#include <stdio.h>
#include <stdlib.h>
#include<assert.h>

extern int add(int,int);

int main(void)
{
	int result,output;
	result = 10;
	assert(result == add(5,5));

}
		