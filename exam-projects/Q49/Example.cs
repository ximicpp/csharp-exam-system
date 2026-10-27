// Q169 · 扩展方法语法与静态调用（考试第 49 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q169()
    {
        int[] values = [-1, 2, 3];
        int instanceStyle = values.Count(v => v > 0);
        int staticStyle = Enumerable.Count(values, v => v > 0);
        return $"{instanceStyle},{staticStyle}";
    }
}
