// Q176 · Func 的组合调用（考试第 56 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q176()
    {
        Func<int, int> twice = value => value * 2;
        Func<int, int> next = value => twice(value) + 1;
        return next(4).ToString(CultureInfo.InvariantCulture);
    }
}
