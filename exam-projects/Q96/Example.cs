// Q216 · Span 切片与后备数组（考试第 96 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q216()
    {
        int[] data = [1, 2, 3, 4];
        Span<int> middle = data.AsSpan(1, 2);
        middle[0] = 9;
        return string.Join(",", data);
    }
}
