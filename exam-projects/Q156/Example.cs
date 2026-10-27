// Q34 · WhenAll 的故障完成与异常观察（考试第 156 题）


internal static partial class Question
{
    private static async Task<(bool Pending, int Failures, bool OneOriginal)> Q34()
    {
        var second = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var firstError = new InvalidOperationException("first");
        var secondError = new ArgumentException("second");
        Task all = Task.WhenAll(Task.FromException(firstError), second.Task);
        bool pending = !all.IsCompleted;
        second.SetException(secondError);
        Exception? observed = null;
        try { await all; }
        catch (Exception error) { observed = error; }
        return (pending, all.Exception!.InnerExceptions.Count,
            ReferenceEquals(observed, firstError) || ReferenceEquals(observed, secondError));
    }
}
