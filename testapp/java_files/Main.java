//import java.lang.*;
class Main
{
    public static <E> void check(E result, E expect)
    {
        if(result.equals(expect))
        {
            System.out.println("right");
        }
	else
	{
	    System.out.println("*"+expect+"*    *"+result+"*");
	    System.exit(1);
	}
    }
    public static void main(String arg[])
    {
       Test t = new Test();
       int a = t.square_num(5);
       check(a,10);
       int b = t.square_num(6);
       check(b,12);
    }
}
