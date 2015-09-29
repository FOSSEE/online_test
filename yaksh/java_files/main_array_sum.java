class main_array_sum
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
       int result;
       Test t = new Test();
       int x[] = {0,0,0,0,0};
       result = t.array_sum(x);
       System.out.println("Input submitted to the function: {0,0,0,0,0}");
       check(0, result);
       int a[] = {1,2,3,4,5};
       result = t.array_sum(a);
       System.out.println("Input submitted to the function: {1,2,3,4,5}");
       check(15, result);
       int b[] = {1,2,3,0,0};
       result = t.array_sum(b);
       System.out.println("Input submitted to the function: {1,2,3,0,0}");
       check(6, result);
       int c[] = {1,1,1,1,1};
       result = t.array_sum(c);
       System.out.println("Input submitted to the function: {1,1,1,1,1}");
       check(5, result);
    }
}
