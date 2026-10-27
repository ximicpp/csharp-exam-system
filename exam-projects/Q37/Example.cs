// Q157 · yield break 与枚举结束（考试第 37 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static IEnumerable<int> Read157()
    {
        foreach (int value in new[] { 2, 4, 0, 8 })
        {
            if (value == 0) yield break;
            yield return value;
        }
    }

    private static string Q157()
    {
        return string.Join(",", Read157());
    }
}
