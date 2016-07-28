class read_file
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
       String result = "";
       Test t = new Test();
       try{
       result = t.readFile();}
       catch(Exception e){
	System.out.print(e);
	}
       check("2", result);
    }
}
