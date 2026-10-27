// Q206 · 异步序列的枚举（考试第 86 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async IAsyncEnumerable<int> Read206()
    {
        yield return 1;
        await Task.CompletedTask;
        yield return 2;
    }

    private static async Task<string> Q206()
    {
        int total = 0;
        await foreach (int value in Read206()) total += value;
        return total.ToString(CultureInfo.InvariantCulture);
    }
}
