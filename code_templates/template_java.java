class main
{3}
    public static <E> void check(E expect, E result)
    {3}
        if(result.equals(expect))
        {3}
            System.out.println("Correct");
        {4}
        {4}
        else
        {3}
            System.out.println("Incorrect");
            System.exit(1);
        {4}
    {4}
    public static void main(String arg[])
    {3}
        Test t = new Test();
        int result,  output;
        output = {2};
        result = t.{0}({1});
        check(output, result);
        
    {4}
{4}
