Question.Run();

internal static partial class Question
{
    internal static void Run()
    {
        Console.WriteLine(Observe());
        try
        {
            Console.WriteLine(Checked(-1));
        }
        catch (Exception error)
        {
            Console.WriteLine(error.GetType().Name);
        }
        Console.WriteLine(Checked(1));
    }
}
