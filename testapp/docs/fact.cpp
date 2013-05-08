#include<stdio.h>
int fact = 1;
int factorial(int a)
{
  printf("%d\n",a);
  if(a<1)
  {
    printf("\nfinal");
    return 1;
  }
  else
  {
    printf("count\n");
    return a*factorial(a-1);
  }
}
