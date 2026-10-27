// Q207 · await foreach 提前退出的收尾（考试第 87 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async IAsyncEnumerable<int> Read207(List<string> log)
    {
        try
        {
            yield return 1;
            await Task.CompletedTask;
            yield return 2;
        }
        finally { log.Add("close"); }
    }

    private static async Task<string> Q207()
    {
        List<string> log = [];
        await foreach (int value in Read207(log)) { log.Add($"item{value}"); break; }
        return string.Join(",", log);
    }
}
