// Q210 · WaitAsync 的取消边界（考试第 90 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async Task<string> Q210()
    {
        var work = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        CancellationToken token = new(canceled: true);
        try { _ = await work.Task.WaitAsync(token); }
        catch (OperationCanceledException)
        {
            bool originalCompleted = work.Task.IsCompleted;
            work.SetResult(7);
            return $"{originalCompleted},{await work.Task}";
        }
        return "unexpected";
    }
}
