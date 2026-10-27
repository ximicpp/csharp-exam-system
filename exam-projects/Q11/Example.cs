// Q131 · 字符串 Replace 的结果（考试第 11 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q131()
    {
        string name = "draft.txt";
        _ = name.Replace("draft", "final", StringComparison.Ordinal);
        string renamed = name.Replace("draft", "final", StringComparison.Ordinal);
        return $"{name}|{renamed}";
    }
}
