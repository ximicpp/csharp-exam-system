// Q202 · WhenAny 与获胜任务的异常（考试第 82 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async Task<string> Q202()
    {
        Task<int> failed = Task.FromException<int>(new InvalidOperationException("failed"));
        var pending = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        Task<int> winner = await Task.WhenAny(failed, pending.Task);
        try { _ = await winner; }
        catch (InvalidOperationException) { pending.SetResult(0); return $"{ReferenceEquals(winner, failed)},{winner.IsFaulted}"; }
        return "success";
    }
}
