// Q22 · await using 的完成边界与所有权（考试第 153 题）


internal static partial class Question
{
    private sealed class AsyncLease(Task finishDispose) : IAsyncDisposable
    {
        public TaskCompletionSource DisposeStarted { get; } =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        public bool Disposed { get; private set; }

        public async ValueTask DisposeAsync()
        {
            DisposeStarted.SetResult();
            await finishDispose;
            Disposed = true;
        }
    }

    // 此方法的契约是接管 lease 的释放责任。
    private static async Task UseOwnedAsync(AsyncLease lease)
    {
        await using (lease)
        {
            await Task.CompletedTask;
        }
    }

    private static async Task<(bool, bool)> Q22()
    {
        var finish = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var lease = new AsyncLease(finish.Task);
        Task operation = UseOwnedAsync(lease);
        await lease.DisposeStarted.Task;
        bool pending = !operation.IsCompleted;
        finish.SetResult();
        await operation;
        return (pending, lease.Disposed);
    }
}
