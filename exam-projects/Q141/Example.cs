// Q56 · volatile 与并发递增（考试第 141 题）
internal static partial class Question
{
    private sealed class VolatileCounter
    {
        public volatile int Value;
        public void Increment() => Value++;
    }

    private static async Task Observe()
    {
        const int workers = 4;
        const int incrementsPerWorker = 100_000;
        var counter = new VolatileCounter();
        Console.WriteLine($"workers={workers}, incrementsPerWorker={incrementsPerWorker}");
        await Task.WhenAll(Enumerable.Range(0, workers).Select(_ => Task.Run(() =>
        {
            for (int i = 0; i < incrementsPerWorker; i++) counter.Increment();
        })));
        Console.WriteLine($"count={counter.Value}");
    }
}
