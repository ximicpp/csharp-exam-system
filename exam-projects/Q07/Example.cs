// Q127 · NaN 的两种相等检查（考试第 7 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q127()
    {
        double first = double.NaN;
        double second = double.NaN;
        return $"{first == second},{first.Equals(second)},{double.IsNaN(first)}";
    }
}
