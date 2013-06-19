#include <stdbooll.h>
bool palindrome(int a)
{
  int n1, rev = 0, rem;
  n1 = a;
  while (a > 0)
  {
  rem = a % 10;
  rev = rev * 10 + rem;
  a = a / 10; 
  }
  if (n1 == rev)
  {
    return true; 
  }
  else
  {
    return false;
  }
}
