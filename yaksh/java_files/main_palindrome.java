class main_palindrome
{
    public static <E> void check(E expect, E result)
    {
        if(result.equals(expect))
        {
            System.out.println("Correct:\nOutput expected "+expect+" and got "+result+"\n");
        }
	else
	{
	    System.out.println("Incorrect:\nOutput expected "+expect+" but got "+result+"\n");
	    System.exit(1);
	}
    }
    public static void main(String arg[])
    {
       Test t = new Test();
       boolean result;
       result= t.palindrome(123);
       System.out.println("Input submitted to the function: 123");
       check(false, result);
       result = t.palindrome(151);
       System.out.println("Input submitted to the function: 151");   
       check(true, result);
       result = t.palindrome(23432);
       System.out.println("Input submitted to the function: 23432");
       check(true, result);
    }
}
