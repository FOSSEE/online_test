class main_square
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
       result = t.square_num(0);
       check(0, result);
       result = t.square_num(5);
       check(25, result);
       result = t.square_num(6);
       check(36, result);
    }
}
