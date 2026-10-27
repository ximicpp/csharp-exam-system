# 第 139 题 · Q139 · 累计分配计数不能回答什么

原题号：`Q51`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

团队用同一线程上的两次分配计数之差评估同步热路径，运行前已预热。现在需要确定这个指标能说明什么。

对 MeasureAllocation() 返回值，哪个解释正确？这里不要求任何固定字节数。

```csharp
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
```

- A. 它记录区间内当前线程累计的托管分配；不是泄漏量，也不等于最终存活对象大小。
- B. 它等于区间结束时整个进程仍然存活的托管内存。
- C. 它包含原生库分配和其他线程的所有分配，因而适合直接跨 await 做差。
- D. 区间内只要发生 GC，已经回收的对象会从累计值中扣除。
