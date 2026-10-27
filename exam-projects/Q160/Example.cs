// Q38 · ConfigureAwait(false) 的精确边界（考试第 160 题）

internal static partial class Question
{
    private sealed class CountingSynchronizationContext : SynchronizationContext
    {
        private int posts;
        public int Posts => Volatile.Read(ref posts);

        public override void Post(SendOrPostCallback callback, object? state)
        {
            Interlocked.Increment(ref posts);
            ThreadPool.QueueUserWorkItem(_ =>
            {
                SynchronizationContext? previous = Current;
                try
                {
                    SetSynchronizationContext(this);
                    callback(state);
                }
                finally
                {
                    SetSynchronizationContext(previous);
                }
            });
        }
    }

    private static async Task<(TaskStatus SourceStatus, string? Ambient, bool SameContext, bool HasContext)>
        ResumeAsync(Task source, bool continueOnCapturedContext,
            CountingSynchronizationContext context, AsyncLocal<string?> ambient)
    {
        await source.ConfigureAwait(continueOnCapturedContext);
        return (source.Status, ambient.Value,
            ReferenceEquals(context, SynchronizationContext.Current),
            SynchronizationContext.Current is not null);
    }

    private static async Task<string> Observe()
    {
        var observations = new List<string>();
        foreach (bool initiallyCompleted in new[] { true, false })
        foreach (bool continueOnCapturedContext in new[] { true, false })
        {
            var context = new CountingSynchronizationContext();
            var ambient = new AsyncLocal<string?> { Value = "request-7" };
            var completion = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
            if (initiallyCompleted) completion.SetResult();

            TaskStatus sourceBefore = completion.Task.Status;
            SynchronizationContext? previous = SynchronizationContext.Current;
            Task<(TaskStatus SourceStatus, string? Ambient, bool SameContext, bool HasContext)> observation;
            TaskStatus observerAtStart;
            try
            {
                SynchronizationContext.SetSynchronizationContext(context);
                observation = ResumeAsync(completion.Task, continueOnCapturedContext, context, ambient);
                observerAtStart = observation.Status;
            }
            finally
            {
                SynchronizationContext.SetSynchronizationContext(previous);
            }

            ambient.Value = null;
            if (!initiallyCompleted) completion.SetResult();
            var result = await observation.ConfigureAwait(false);
            observations.Add(
                $"InitiallyCompleted={initiallyCompleted}, ContinueOnCapturedContext={continueOnCapturedContext}, " +
                $"SourceBefore={sourceBefore}, ObserverAtStart={observerAtStart}, SourceAfter={result.SourceStatus}, " +
                $"Posts={context.Posts}, Ambient={result.Ambient ?? "<null>"}, " +
                $"SameContext={result.SameContext}, HasContext={result.HasContext}");
        }
        return string.Join(Environment.NewLine, observations);
    }
}
