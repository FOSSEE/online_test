bool palindrome(int n)
{
  int n1, rev = 0, rem;
  n1 = n;
  while (n > 0)
  {
  rem = n % 10;
  rev = rev * 10 + rem;
  n = n / 10; 
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
