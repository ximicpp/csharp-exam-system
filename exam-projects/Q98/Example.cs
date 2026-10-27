// Q218 · 扩展属性与对象成员（考试第 98 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q218()
    {
        string text = "go";
        return $"{text.HasContent},{"".HasContent}";
    }
}

internal static class MicrosoftTextExtensions
{
    extension(string text)
    {
        public bool HasContent => text.Length > 0;
    }
}
