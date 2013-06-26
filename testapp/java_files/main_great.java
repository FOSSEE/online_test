class main_great
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
       result = t.greatest(1, 3, 4);
       check(4, result);
       result = t.greatest(5, 10, 3);
       check(10, result);
       result = t.greatest(6, 1, 4);
       check(6, result);
       result = t.greatest(16, 1, 4);
       check(16, result);
       result = t.greatest(6, 61, 4);
       check(61, result);
       result = t.greatest(2, 1, 3);
       check(3, result);
    }
}
