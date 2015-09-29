class main_square
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
       int result, input, output;
       input = 0; output = 0;
       result = t.square_num(input);
       System.out.println("Input submitted to the function: "+input);
       check(output, result);
       input = 5; output = 25;
       result = t.square_num(input);
       System.out.println("Input submitted to the function: "+input);
       check(output, result);
       input = 6; output = 36;
       result = t.square_num(input);
       System.out.println("Input submitted to the function: "+input);
       check(output, result);
    }
}
