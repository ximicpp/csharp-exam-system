// Q46 · 池化缓冲区何时能归还（考试第 136 题）

internal static partial class Question
{
    private sealed class TrackingPool : System.Buffers.ArrayPool<byte>
    {
        public int Returns { get; private set; }
        public override byte[] Rent(int minimumLength) => new byte[minimumLength];
        public override void Return(byte[] array, bool clearArray = false) => Returns++;
    }
    private static async Task<int> SendAsync(ReadOnlyMemory<byte> data, Task gate)
    {
        await gate;
        return data.Span[0];
    }
    private static async Task<(int WhilePending, int Value, int Returns)> Observe()
    {
        var pool = new TrackingPool();
        byte[] buffer = pool.Rent(1);
        buffer[0] = 42;
        var gate = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        int whilePending;
        int value;
        try
        {
            Task<int> send = SendAsync(buffer.AsMemory(0, 1), gate.Task);
            whilePending = pool.Returns;
            gate.SetResult();
            value = await send;
        }
        finally { pool.Return(buffer); }
        return (whilePending, value, pool.Returns);
    }

}
