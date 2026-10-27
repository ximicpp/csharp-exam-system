// Q159 · foreach 退出与迭代器清理（考试第 39 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static IEnumerable<int> Read159(List<string> log)
    {
        try { yield return 1; yield return 2; }
        finally { log.Add("close"); }
    }

    private static string Q159()
    {
        List<string> log = [];
        foreach (int value in Read159(log)) { log.Add($"item{value}"); break; }
        return string.Join(",", log);
    }
}
