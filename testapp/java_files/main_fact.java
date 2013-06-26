class main_fact
{
    public static <E> void check(E expect, E result)
    {
        if(result.equals(expect))
        {
            System.out.println("Correct:\nOutput expected "+expect+" and got "+result);
        }
	else
	{
	    System.out.println("Incorrect:\nOutput expected "+expect+" but got "+result);
	    System.exit(1);
	}
    }
    public static void main(String arg[])
    {
       Test t = new Test();
       int result;
       result = t.factorial(0);
       System.out.println("Input submitted to the function: 0");
       check(1, result);
       result = t.factorial(3);
       System.out.println("Input submitted to the function: 3");
       check(6, result);
       result = t.factorial(4);
       System.out.println("Input submitted to the function: 4");
       check(24, result);
    }
}
