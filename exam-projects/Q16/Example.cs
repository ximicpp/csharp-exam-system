// Q136 · 集合表达式的展开与后续修改（考试第 16 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q136()
    {
        List<int> source = [2, 4];
        int[] packet = [1, .. source, 8];
        source.Add(6);
        return string.Join(",", packet);
    }
}
