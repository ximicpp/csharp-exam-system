// Q51 · 累计分配计数不能回答什么（考试第 139 题）
using System.Collections.Concurrent;

internal static partial class Question
{
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
}
