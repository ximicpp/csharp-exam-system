await Question.Run();

internal static partial class Question
{
    internal static async Task Run()
    {
        Console.WriteLine(await Q204());
    }
}
