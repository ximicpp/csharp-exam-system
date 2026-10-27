Question.Run();

internal static partial class Question
{
    internal static void Run()
    {
        _ = MeasureAllocation();
        Console.WriteLine(MeasureAllocation());
    }
}
