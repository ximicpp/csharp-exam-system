// Q224 · null-forgiving 与可空分析（考试第 104 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q224()
    {
        string? raw = null;
        string assumed = raw!;
        return (assumed is null).ToString();
    }
}
