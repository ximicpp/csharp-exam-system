// Q129 · 可空文本链上的空内容（考试第 9 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q129()
    {
        string? absent = null;
        string? blank = "   ";
        return $"{absent?.Trim().Length ?? -1},{blank?.Trim().Length ?? -1}";
    }
}
