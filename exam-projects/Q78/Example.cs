// Q198 · 空序列上的 All 与 Any（考试第 78 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q198()
    {
        int[] values = [];
        return $"{values.All(value => value > 0)},{values.Any()}";
    }
}
