class factorial
{
    int factorial(int a)
    {
        if(a<1)
        {
            return 1;
        }
        else
        {
            return a*factorial(a-1);
        }
    }
}
