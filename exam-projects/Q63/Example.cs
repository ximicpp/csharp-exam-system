// Q183 · 异常包装与 InnerException（考试第 63 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q183()
    {
        Exception original = new FormatException("bad input");
        Exception wrapped = new InvalidOperationException("cannot import", original);
        return $"{wrapped.Message}|{wrapped.InnerException?.Message}";
    }
}
