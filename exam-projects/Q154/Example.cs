// Q27 · 事件重复订阅后的退订责任（考试第 154 题）


internal static partial class Question
{
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
}
