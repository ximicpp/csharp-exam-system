// Q203 · WhenAll 的结果顺序（考试第 83 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async Task<string> Q203()
    {
        var first = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        var second = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        Task<int[]> combined = Task.WhenAll(first.Task, second.Task);
        second.SetResult(20);
        first.SetResult(10);
        return string.Join(",", await combined);
    }
}
