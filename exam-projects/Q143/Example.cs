// Q58 · 并发字典保证工厂只执行一次吗（考试第 143 题）
using System.Collections.Concurrent;

internal static partial class Question
{
    private static async Task<(bool BothEntered, int Calls, int Stored, bool SameValue, bool MatchesStored)> Observe()
    {
        var cache = new ConcurrentDictionary<string, object>();
        using var bothEntered = new CountdownEvent(2);
        using var release = new ManualResetEventSlim();
        int calls = 0;

        object Factory(string _)
        {
            Interlocked.Increment(ref calls);
            bothEntered.Signal();
            if (!release.Wait(TimeSpan.FromSeconds(10)))
                throw new TimeoutException("Factory release was not signaled.");
            return new object();
        }

        Task<object> Start() => Task.Factory.StartNew(
            () => cache.GetOrAdd("shared", Factory), CancellationToken.None,
            TaskCreationOptions.LongRunning, TaskScheduler.Default);

        Task<object> first = Start();
        Task<object> second = Start();
        bool entered;
        try { entered = bothEntered.Wait(TimeSpan.FromSeconds(10)); }
        finally { release.Set(); }
        object[] values = await Task.WhenAll(first, second);
        return (entered, calls, cache.Count, ReferenceEquals(values[0], values[1]),
            ReferenceEquals(values[0], cache["shared"]));
    }
}
