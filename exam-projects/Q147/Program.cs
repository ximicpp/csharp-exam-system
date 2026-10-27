Question.Run();

internal static partial class Question
{
    internal static void Run()
    {
        var result = Observe();
        Console.WriteLine($"const-read={result.ConstantValue}; readonly-read={result.ReadonlyValue}");
    }
}
