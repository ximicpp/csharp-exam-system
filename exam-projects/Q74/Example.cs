// Q194 · 分组后的数量求和（考试第 74 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q194()
    {
        var entries = new[] { (Team: "a", Count: 2), (Team: "b", Count: 4), (Team: "a", Count: 3) };
        var totals = entries.GroupBy(row => row.Team).OrderBy(group => group.Key, StringComparer.Ordinal)
            .Select(group => $"{group.Key}:{group.Sum(row => row.Count)}");
        return string.Join(",", totals);
    }
}
