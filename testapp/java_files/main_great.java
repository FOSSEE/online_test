class main_great
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
       result = t.greatest(1, 3, 4);
       System.out.println("Input submitted to the function: 1, 3, 4");
       check(4, result);
       result = t.greatest(5, 10, 3);
       System.out.println("Input submitted to the function: 5, 10, 3");
       check(10, result);
       result = t.greatest(6, 1, 4);
       System.out.println("Input submitted to the function: 6, 1, 4");
       check(6, result);
       result = t.greatest(6, 11, 14);
       System.out.println("Input submitted to the function: 6, 11, 14");
       check(14, result);
       result = t.greatest(3, 31, 4);
       System.out.println("Input submitted to the function: 3, 31, 4");
       check(31, result);
       result = t.greatest(26, 13, 3);
       System.out.println("Input submitted to the function: 26, 13, 3");
       check(26, result);

    }
}
