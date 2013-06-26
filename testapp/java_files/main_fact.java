class main_fact
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
       int result;
       result = t.factorial(0);
       check(1, result);
       result = t.factorial(3);
       check(6, result);
       result = t.factorial(4);
       check(24, result);
    }
}
