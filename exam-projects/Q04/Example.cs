// Q124 · 负数的商与余数（考试第 4 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q124()
    {
        int offset = -7;
        return $"{offset / 3},{offset % 3}";
    }
}
