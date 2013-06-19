#include<string.h>
#include<stdio.h>

char *message(char a[])
{
  return (strcat("hello",a));
}

main()
{
 printf("he\n");
 char q[]="re";
 char s[20];
 s= message(q);
 printf("%s",s);
}
