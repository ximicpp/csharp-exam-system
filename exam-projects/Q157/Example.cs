// Q35 · 取消请求与清理完成（考试第 157 题）


internal static partial class Question
{
    private static async Task<(bool AfterCancel, bool DuringCleanup, bool Cleaned, bool Canceled)> Q35()
    {
        using var cts = new CancellationTokenSource();
        var observe = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var cleaning = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var finish = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        bool cleaned = false;
        async Task WorkAsync()
        {
            try
            {
                await observe.Task;
                cts.Token.ThrowIfCancellationRequested();
            }
            finally
            {
                cleaning.SetResult();
                await finish.Task;
                cleaned = true;
            }
        }
        Task work = WorkAsync();
        cts.Cancel();
        bool afterCancel = !work.IsCompleted;
        observe.SetResult();
        await cleaning.Task;
        bool duringCleanup = !work.IsCompleted;
        finish.SetResult();
        try { await work; }
        catch (OperationCanceledException) when (cts.IsCancellationRequested) { }
        return (afterCancel, duringCleanup, cleaned, work.IsCanceled);
    }
}
