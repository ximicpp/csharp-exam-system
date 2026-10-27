// Q134 · 逐字字符串与转义（考试第 14 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q134()
    {
        string path = @"C:\temp\new";
        return $"{path.Contains('\n')},{path.EndsWith(@"\new", StringComparison.Ordinal)}";
    }
}
