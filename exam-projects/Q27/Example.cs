// Q147 · 属性模式能否接受 null（考试第 27 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed record Label147(string Text);

    private static string Q147()
    {
        Label147? missing = null;
        Label147 empty = new("");
        Label147 valid = new("go");
        return $"{missing is { Text.Length: > 0 }},{empty is { Text.Length: > 0 }},{valid is { Text.Length: > 0 }}";
    }
}
