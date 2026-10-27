await Question.Run();

internal static partial class Question
{
    internal static async Task Run()
    {
        await Observe();
    }
}
