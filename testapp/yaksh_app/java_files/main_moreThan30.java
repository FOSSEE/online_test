class main_moreThan30
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
       result= t.moreThan30(30);
       System.out.println("Input submitted to the function: 30");
       check(false, result);
       result = t.moreThan30(151);
       System.out.println("Input submitted to the function: 151");   
       check(true, result);
       result = t.moreThan30(66);
       System.out.println("Input submitted to the function: 66");
       check(false, result);
       result = t.moreThan30(63);
       System.out.println("Input submitted to the function: 63");
       check(true, result);
       result = t.moreThan30(91);
       System.out.println("Input submitted to the function: 91");
       check(true, result);
 
    }
}
