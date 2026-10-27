// Q200 · 查询创建与源集合修改（考试第 80 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q200()
    {
        List<int> source = [1, 2];
        var query = source.Where(value => value > 1);
        source.Add(3);
        int[] snapshot = query.ToArray();
        source.Add(4);
        return string.Join(",", snapshot);
    }
}
