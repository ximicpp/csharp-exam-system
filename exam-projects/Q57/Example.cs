// Q177 · static lambda 的参数与使用（考试第 57 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q177()
    {
        int[] values = [2, 3];
        return string.Join(",", values.Select(static value => value * value));
    }
}
