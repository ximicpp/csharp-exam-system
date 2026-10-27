// Q47 · GC 没有释放业务已结束的对象（考试第 137 题）

internal static partial class Question
{
    private sealed class RequestState { public byte[] Payload { get; } = new byte[8]; }
    private static readonly Dictionary<string, RequestState> Active = new();
    private static (bool Retained, bool Removed, int Entries) Observe()
    {
        var state = new RequestState();
        Active.Add("request", state);
        bool retained = ReferenceEquals(state.Payload, Active["request"].Payload);
        bool removed = Active.Remove("request");
        return (retained, removed, Active.Count);
    }

}
