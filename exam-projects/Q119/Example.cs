// Q239 · GC 与 IDisposable 的职责（考试第 119 题）

internal static partial class Question
{
    private sealed class Resource : IDisposable
    {
        public bool Closed { get; private set; }
        public void Dispose() => Closed = true;
    }
    private static (bool Before, bool After, bool StillReferenced) Observe()
    {
        var resource = new Resource();
        bool before = resource.Closed;
        using (resource) { }
        return (before, resource.Closed, resource is not null);
    }

}
