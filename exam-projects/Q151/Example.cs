// Q94 · 实例方法与扩展方法的绑定（考试第 151 题）


internal static partial class Question
{
    private static (bool Instance, bool ExplicitStatic) BindExtension() =>
        ("abc".Contains("a"), QuizStringExtensions.Contains("abc", "a"));
}

internal static class QuizStringExtensions
{
    public static bool Contains(this string text, string part) => false;
}
