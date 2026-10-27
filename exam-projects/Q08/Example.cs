// Q128 · 可空整数的运算（考试第 8 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q128()
    {
        int? reading = null;
        int? adjusted = reading + 2;
        return $"{adjusted.HasValue},{adjusted.GetValueOrDefault()}";
    }
}
