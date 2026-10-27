# 第 141 题 · Q141 · volatile 与并发递增

原题号：`Q56`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

多个工作线程共享同一个计数器，每次成功完成工作就调用 Increment；全部工作结束后再读取结果。

下面实现是否能保证每次调用都计入结果？假定计数不溢出。

```csharp
private sealed class VolatileCounter
{
    public volatile int Value;
    public void Increment() => Value++;
}
```

- A. 能，volatile 把 Value++ 整体变成原子读改写。
- B. 能，int 的读取和写入各自原子，所以组合的 ++ 必然原子。
- C. 不能；可把字段改成普通 int，并用 Interlocked.Increment(ref Value) 实现原子递增。
- D. 不能；但只在最终读取时加 lock 就能补回丢失的更新。

## 动手问题

- 保持 VolatileCounter 的实现，改变 Program.cs 中的工作线程数与每个线程的调用次数，记录实际计数。某次计数与调用次数一致，能否说明所有交错都满足题目的保证？
