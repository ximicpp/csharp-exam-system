using System.Collections.Concurrent;

internal static class QuizRuntime
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q42", () => QuizAssert.Equal((9, 3, 7), BoxingSnapshot()));
        suite.Add("Q43", () => QuizAssert.Equal((1, 2), InterfaceAndGeneric()));
        suite.Add("Q44", () => QuizAssert.Equal((99, 7), SharedViews()));
        suite.Add("Q51", () =>
        {
            _ = MeasureAllocation();
            QuizAssert.True(MeasureAllocation() > 0, "A returned array must allocate managed storage.");
        });
        suite.Add("Q52", () => QuizAssert.Equal((7, 0, false), GenericState()));
        suite.AddAsync("Q56", async () =>
        {
            var counter = new AtomicCounter();
            await Task.WhenAll(Enumerable.Range(0, 4).Select(_ => Task.Run(() =>
            {
                for (int i = 0; i < 1_000; i++) counter.Increment();
            })));
            QuizAssert.Equal(4_000, counter.Value);
        });
        suite.AddAsync("Q57", async () =>
        {
            var ledger = new Ledger();
            await Task.WhenAll(Enumerable.Range(0, 4).Select(_ => Task.Run(() =>
            {
                for (int i = 0; i < 500; i++)
                {
                    ledger.DepositOne();
                    var snapshot = ledger.Snapshot();
                    QuizAssert.Equal(snapshot.Balance, snapshot.Version);
                }
            })));
            QuizAssert.Equal((2_000, 2_000), ledger.Snapshot());
        });
        suite.AddAsync("Q58", CheckConcurrentFactories);
        suite.AddAsync("Q59", async () => QuizAssert.Equal(("request-7", "request-7"), await AmbientFlow()));
        suite.Add("Q60", () => QuizAssert.Equal((1, 1, 0), ReadonlyCopies()));
    }

    #region Q42-types
    private struct Position
    {
        public int X;
    }
    #endregion

    #region Q42-call
    private static (int Original, int Boxed, int Unboxed) BoxingSnapshot()
    {
        var original = new Position { X = 3 };
        object boxed = original;
        original.X = 9;
        Position unboxed = (Position)boxed;
        unboxed.X = 7;
        return (original.X, ((Position)boxed).X, unboxed.X);
    }
    #endregion

    #region Q43-types
    private interface ICounter
    {
        void Increment();
        int Value { get; }
    }

    private struct Counter : ICounter
    {
        public int Value { get; private set; }
        public void Increment() => Value++;
    }

    private static void IncrementGeneric<T>(ref T counter) where T : struct, ICounter
        => counter.Increment();
    #endregion

    #region Q43-call
    private static (int Original, int Boxed) InterfaceAndGeneric()
    {
        var counter = new Counter();
        ICounter boxed = counter;
        boxed.Increment();
        boxed.Increment();
        IncrementGeneric(ref counter);
        return (counter.Value, boxed.Value);
    }
    #endregion

    #region Q44
    private static (int ReadOnlyFirst, int TailValue) SharedViews()
    {
        int[] data = [10, 20, 30];
        Span<int> middle = data.AsSpan(1, 2);
        ReadOnlySpan<int> readOnly = middle;
        middle[0] = 99;
        data[2] = 7;
        return (readOnly[0], middle[1]);
    }
    #endregion

    #region Q51
    [System.Runtime.CompilerServices.MethodImpl(
        System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
    private static byte[] AllocateBuffer() => new byte[4_096];

    private static long MeasureAllocation()
    {
        long before = GC.GetAllocatedBytesForCurrentThread();
        byte[] buffer = AllocateBuffer();
        long after = GC.GetAllocatedBytesForCurrentThread();
        GC.KeepAlive(buffer);
        return after - before;
    }
    #endregion

    #region Q52-types
    private static class Cache<T>
    {
        public static int Hits;
    }
    #endregion

    #region Q52-call
    private static (int StringHits, int ObjectHits, bool SameType) GenericState()
    {
        Cache<string>.Hits = 7;
        Cache<object>.Hits = 0;
        return (Cache<string>.Hits, Cache<object>.Hits,
            typeof(Cache<string>) == typeof(Cache<object>));
    }
    #endregion

    #region Q56
    private sealed class VolatileCounter
    {
        public volatile int Value;
        public void Increment() => Value++;
    }
    #endregion

    private sealed class AtomicCounter
    {
        public int Value;
        public void Increment() => Interlocked.Increment(ref Value);
    }

    #region Q57
    private sealed class Ledger
    {
        private readonly object gate = new();
        private int balance;
        private int version;

        public void DepositOne()
        {
            lock (gate)
            {
                balance++;
                version++;
            }
        }

        public (int Balance, int Version) Snapshot()
        {
            lock (gate) return (balance, version);
        }
    }
    #endregion

    private static async Task CheckConcurrentFactories()
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
        QuizAssert.True(entered, "Both factories must enter before either returns.");
        QuizAssert.Equal(2, calls);
        QuizAssert.Equal(1, cache.Count);
        QuizAssert.True(ReferenceEquals(values[0], values[1]), "Both callers receive the winning value.");
        QuizAssert.True(ReferenceEquals(values[0], cache["shared"]), "The returned value is the stored value.");
    }

    #region Q59
    private static async Task<(string? Child, string? Parent)> AmbientFlow()
    {
        var requestId = new AsyncLocal<string?>();
        requestId.Value = "request-7";
        string? child = await Task.Run(async () =>
        {
            await Task.Yield();
            return requestId.Value;
        }).ConfigureAwait(false);
        return (child, requestId.Value);
    }
    #endregion

    #region Q60-types
    private struct Cursor
    {
        public int Position;
        public int Advance() => ++Position;
    }

    private static (int First, int Second) Probe(in Cursor cursor)
        => (cursor.Advance(), cursor.Advance());
    #endregion

    #region Q60-call
    private static (int First, int Second, int Original) ReadonlyCopies()
    {
        var cursor = new Cursor();
        var pair = Probe(in cursor);
        return (pair.First, pair.Second, cursor.Position);
    }
    #endregion
}
