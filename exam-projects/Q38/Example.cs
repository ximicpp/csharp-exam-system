// Q158 · 同一序列的两次枚举（考试第 38 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static IEnumerable<int> Count158()
    {
        yield return 1;
        yield return 2;
    }

    private static string Q158()
    {
        IEnumerable<int> values = Count158();
        return $"{string.Join(",", values)}|{string.Join(",", values)}";
    }
}
