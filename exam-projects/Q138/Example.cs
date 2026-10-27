// Q49 · 对象存活与地址固定（考试第 138 题）

internal static partial class Question
{
    private static unsafe int NativeStyleRead(byte* address) => address[0] + address[1];
    private static unsafe int Observe()
    {
        byte[] buffer = [20, 22];
        int sum;
        fixed (byte* address = buffer) { sum = NativeStyleRead(address); }
        GC.KeepAlive(buffer);
        return sum;
    }

}
