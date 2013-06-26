class main_palindrome
{
    public static <E> void check(E expect, E result)
    {
        if(result.equals(expect))
        {
            System.out.println("Output expected "+expect+" and got "+result);
        }
	else
	{
	    System.out.println("Output expected "+expect+" but got "+result);
	    System.exit(1);
	}
    }
    public static void main(String arg[])
    {
       Test t = new Test();
       boolean result;
       result= t.palindrome(123);
       check(false, result);
       result = t.palindrome(151);
       check(true, result);
       result = t.palindrome(23432);
       check(true, result);
    }
}
