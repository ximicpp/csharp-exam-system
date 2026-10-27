// Q151 · params 的空调用与数组调用（考试第 31 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q151()
    {
        static int Total(params int[] values) => values.Sum();
        int[] pair = [2, 3];
        return $"{Total()},{Total(pair)},{Total(1, 2, 3)}";
    }
}
