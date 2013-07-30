class main_hello_name
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
       String result;
       result = t.hello_name("Raj");
       System.out.println("Input submitted to the function: 'Raj'");
       check("hello Raj", result);
       result = t.hello_name("Pratham");
       System.out.println("Input submitted to the function: 'Pratham'");
       check("hello Pratham", result);
       result = t.hello_name("Ram");
       System.out.println("Input submitted to the function: 'Ram'");
       check("hello Ram", result);
    }
}
