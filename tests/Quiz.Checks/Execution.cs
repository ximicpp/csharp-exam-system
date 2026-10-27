internal static class QuizExecution
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q21", () => QuizAssert.Equal("body,second,first,caught", Q21()));
        suite.AddAsync("Q22", async () => QuizAssert.Equal((true, true), await Q22()));
        suite.Add("Q23", () => QuizAssert.Equal("filter:False,finally,catch:True", Q23()));
        suite.Add("Q25", () => QuizAssert.Equal("20,30", Q25()));
        suite.Add("Q27", () => QuizAssert.Equal((1, 1, 0), Q27()));
        suite.Add("Q28", () => QuizAssert.Equal((0, 3, 7, "2", "2,4"), Q28()));
        suite.Add("Q29", () => QuizAssert.Equal((2, 1, "updated"), Q29()));
        suite.Add("Q31", () =>
        {
            QuizAssert.Equal("created,enumerator,argument", Q31());
            static IEnumerable<int> ValidateThenIterate(int count)
            {
                if (count <= 0) throw new ArgumentOutOfRangeException(nameof(count));
                return Iterate(count);
                static IEnumerable<int> Iterate(int count)
                {
                    for (int i = 0; i < count; i++) yield return i;
                }
            }
            QuizAssert.Throws<ArgumentOutOfRangeException>(() => ValidateThenIterate(0));
            QuizAssert.Equal("0,1", string.Join(",", ValidateThenIterate(2)));
        });
        suite.Add("Q32", () => QuizAssert.Equal("open,1,dispose,after", Q32()));
        suite.AddAsync("Q33", async () => QuizAssert.Equal("A,B,caller,C", await Q33()));
        suite.AddAsync("Q34", async () =>
        {
            var result = await Q34();
            QuizAssert.True(result.Pending, "WhenAll must wait for the second task.");
            QuizAssert.Equal(2, result.Failures);
            QuizAssert.True(result.OneOriginal, "await must expose one original failure here.");

            var first = new InvalidOperationException("first");
            var second = new ArgumentException("second");
            Task all = Task.WhenAll(Task.FromException(first), Task.FromException(second));
            await QuizAssert.ThrowsAsync<Exception>(() => all);
            QuizAssert.Equal(2, all.Exception!.InnerExceptions.Count);
            QuizAssert.True(all.Exception.InnerExceptions.Contains(first), "The aggregate must retain the first failure.");
            QuizAssert.True(all.Exception.InnerExceptions.Contains(second), "The aggregate must retain the second failure.");
        });
        suite.AddAsync("Q35", async () => QuizAssert.Equal((true, true, true, true), await Q35()));
        suite.AddAsync("Q36", async () =>
        {
            QuizAssert.Equal((0, 3, 6), await Q36());
            int starts = 0;
            Task<int> FetchAsync(int id)
            {
                starts++;
                return Task.FromResult(id);
            }
            int[] ids = [1, 2, 3];
            Task<int>[] tasks = ids.Select(FetchAsync).ToArray();
            QuizAssert.Equal(3, starts);
            await Task.WhenAll(tasks);
            await Task.WhenAll(tasks);
            QuizAssert.Equal(3, starts);
        });
        suite.AddAsync("Q40", async () => QuizAssert.Equal("1,disposed,canceled", await Q40()));
    }

    #region Q21
    private sealed class Resource(string name, List<string> log) : IDisposable
    {
        public void Dispose() => log.Add(name);
    }

    private static string Q21()
    {
        var log = new List<string>();
        try
        {
            using var first = new Resource("first", log);
            using var second = new Resource("second", log);
            log.Add("body");
            throw new InvalidOperationException();
        }
        catch (InvalidOperationException)
        {
            log.Add("caught");
        }
        return string.Join(",", log);
    }
    #endregion

    #region Q22
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
    #endregion

    #region Q23
    private static string Q23()
    {
        bool cleaned = false;
        var log = new List<string>();
        bool Accept()
        {
            log.Add($"filter:{cleaned}");
            return true;
        }
        try
        {
            try { throw new InvalidOperationException(); }
            finally
            {
                cleaned = true;
                log.Add("finally");
            }
        }
        catch (InvalidOperationException) when (Accept())
        {
            log.Add($"catch:{cleaned}");
        }
        return string.Join(",", log);
    }
    #endregion

    #region Q25
    private static string Q25()
    {
        int limit = 10;
        Func<int> read = () => limit;
        limit = 20;
        int first = read();
        limit = 30;
        return $"{first},{read()}";
    }
    #endregion

    #region Q27
    private sealed class Publisher
    {
        public event Action? Changed;
        public int SubscriptionCount => Changed?.GetInvocationList().Length ?? 0;
        public void Raise() => Changed?.Invoke();
    }

    private static (int Calls, int Remaining, int Final) Q27()
    {
        var publisher = new Publisher();
        int calls = 0;
        Action handler = () => calls++;
        publisher.Changed += handler;
        publisher.Changed += handler;
        publisher.Changed -= handler;
        publisher.Raise();
        int remaining = publisher.SubscriptionCount;
        publisher.Changed -= handler;
        return (calls, remaining, publisher.SubscriptionCount);
    }
    #endregion

    #region Q28
    private static (int Before, int First, int Second, string A, string B) Q28()
    {
        var values = new List<int> { 1, 2, 3 };
        int calls = 0;
        var query = values.Where(x => { calls++; return x % 2 == 0; });
        int before = calls;
        string a = string.Join(",", query);
        int first = calls;
        values.Add(4);
        string b = string.Join(",", query);
        return (before, first, calls, a, b);
    }
    #endregion

    #region Q29
    private sealed class Row(string name)
    {
        public string Name { get; set; } = name;
    }

    private static (int SourceCount, int SnapshotCount, string Name) Q29()
    {
        var rows = new List<Row> { new("initial") };
        var snapshot = rows.ToList();
        rows.Add(new Row("added"));
        rows[0].Name = "updated";
        return (rows.Count, snapshot.Count, snapshot[0].Name);
    }
    #endregion

    #region Q31
    private static IEnumerable<int> RepeatPositive(int count)
    {
        if (count <= 0)
            throw new ArgumentOutOfRangeException(nameof(count));
        for (int i = 0; i < count; i++)
            yield return i;
    }

    private static string Q31()
    {
        var log = new List<string>();
        try
        {
            var sequence = RepeatPositive(0);
            log.Add("created");
            using var iterator = sequence.GetEnumerator();
            log.Add("enumerator");
            iterator.MoveNext();
        }
        catch (ArgumentOutOfRangeException)
        {
            log.Add("argument");
        }
        return string.Join(",", log);
    }
    #endregion

    #region Q32
    private sealed class Cursor(List<string> log) : IDisposable
    {
        public void Dispose() => log.Add("dispose");
    }

    private static IEnumerable<int> ReadRows(List<string> log)
    {
        using var cursor = new Cursor(log);
        log.Add("open");
        yield return 1;
        yield return 2;
    }

    private static string Q32()
    {
        var log = new List<string>();
        foreach (int row in ReadRows(log))
        {
            log.Add(row.ToString());
            break;
        }
        log.Add("after");
        return string.Join(",", log);
    }
    #endregion

    #region Q33
    private static async Task<string> Q33()
    {
        var log = new List<string>();
        var gate = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        async Task WorkAsync()
        {
            log.Add("A");
            await Task.CompletedTask;
            log.Add("B");
            await gate.Task;
            log.Add("C");
        }
        Task work = WorkAsync();
        log.Add("caller");
        gate.SetResult();
        await work;
        return string.Join(",", log);
    }
    #endregion

    #region Q34
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
    #endregion

    #region Q35
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
    #endregion

    #region Q36
    private static async Task<(int Before, int First, int Second)> Q36()
    {
        int starts = 0;
        Task<int> FetchAsync(int id)
        {
            starts++;
            return Task.FromResult(id);
        }
        int[] ids = [1, 2, 3];
        IEnumerable<Task<int>> requests = ids.Select(FetchAsync);
        int before = starts;
        await Task.WhenAll(requests);
        int first = starts;
        await Task.WhenAll(requests);
        return (before, first, starts);
    }
    #endregion

    #region Q40
    private static async IAsyncEnumerable<int> ReadAsync(
        List<string> log,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken token = default)
    {
        try
        {
            for (int i = 1; i <= 3; i++)
            {
                token.ThrowIfCancellationRequested();
                await Task.CompletedTask;
                yield return i;
            }
        }
        finally { log.Add("disposed"); }
    }

    private static async Task<string> Q40()
    {
        var log = new List<string>();
        using var cts = new CancellationTokenSource();
        try
        {
            await foreach (int value in ReadAsync(log).WithCancellation(cts.Token))
            {
                log.Add(value.ToString());
                cts.Cancel();
            }
        }
        catch (OperationCanceledException) when (cts.IsCancellationRequested)
        {
            log.Add("canceled");
        }
        return string.Join(",", log);
    }
    #endregion
}
