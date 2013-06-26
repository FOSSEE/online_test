class main_array_sum
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
       int result;
       Test t = new Test();
       int x[] = {0,0,0,0,0};
       result = t.array_sum(x);
       check(0, result);
       int a[] = {1,2,3,4,5};
       result = t.array_sum(a);
       check(15, result);
       int b[] = {1,2,3,0,0};
       result = t.array_sum(b);
       check(6, result);
       int c[] = {1,1,1,1,1};
       result = t.array_sum(c);
       check(5, result);
    }
}
