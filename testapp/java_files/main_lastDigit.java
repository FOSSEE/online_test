class main_lastDigit
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
       result= t.lastDigit(12, 2, 13);
       System.out.println("Input submitted to the function: 12, 2, 13");
       check(true, result);
       result = t.lastDigit(11, 52, 32);
       System.out.println("Input submitted to the function: 11, 52, 32");   
       check(true, result);
       result = t.lastDigit(6, 34, 22);
       System.out.println("Input submitted to the function: 6, 34, 22");
       check(false, result);
       result = t.lastDigit(6, 46, 26);
       System.out.println("Input submitted to the function: 63");
       check(true, result);
       result = t.lastDigit(91, 90, 92);
       System.out.println("Input submitted to the function: 91");
       check(false, result);
 
    }
}
