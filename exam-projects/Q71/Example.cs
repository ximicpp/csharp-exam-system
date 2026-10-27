// Q191 · 查询表达式中的排序与投影（考试第 71 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q191()
    {
        int[] scores = [3, 8, 5];
        var query = from score in scores where score > 3 orderby score descending select $"n{score}";
        return string.Join(",", query);
    }
}
