// Q121 · 文件应用与项目应用（考试第 1 题）

internal static partial class Question
{
    private static string Observe() => Greeting.Message;
    private static class Greeting { internal static string Message => "hello from a project"; }

}
