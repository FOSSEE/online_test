class main_hello_name
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
       String result;
       result = t.hello_name("pratham");
       check("hello pratham", result);
       result = t.hello_name("raj");
       check("hello raj", result);
       result = t.hello_name("ram");
       check("hello ram", result);
    }
}
