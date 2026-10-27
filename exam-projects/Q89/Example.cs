// Q209 · CompareExchange 的返回值（考试第 89 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q209()
    {
        int state = 2;
        int before = Interlocked.CompareExchange(ref state, 5, 2);
        int rejected = Interlocked.CompareExchange(ref state, 9, 2);
        return $"{before},{rejected},{state}";
    }
}
