// Q43 · 接口参数与受约束的泛型调用（考试第 133 题）
using System.Collections.Concurrent;

internal static partial class Question
{
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
    private static (int Original, int Boxed) InterfaceAndGeneric()
    {
        var counter = new Counter();
        ICounter boxed = counter;
        boxed.Increment();
        boxed.Increment();
        IncrementGeneric(ref counter);
        return (counter.Value, boxed.Value);
    }
}
