# 第 142 题 · Q142 · 锁与多字段一致性

原题号：`Q57`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

账本用两个字段表示累计入账次数及版本号，初始都为 0；多个线程调用 DepositOne 和 Snapshot，所有访问均限于以下代码。

假定不溢出，关于 Snapshot 的结果与修改方案，哪个判断正确？

```csharp
private sealed class Ledger
{
    private readonly object gate = new();
    private int balance;
    private int version;

    public void DepositOne()
    {
        lock (gate)
        {
            balance++;
            version++;
        }
    }

    public (int Balance, int Version) Snapshot()
    {
        lock (gate) return (balance, version);
    }
}
```

- A. 当前 Snapshot 不会观察到 Balance 与 Version 不等；读写都在同一把锁下维护这个不变量。
- B. 把两个字段分别改为 Interlocked.Increment 后，可以删除所有锁，仍保证任意 Snapshot 的两个值一致。
- C. Snapshot 自己加锁就足够，DepositOne 可以删除锁，因为只有读取需要一致性。
- D. Snapshot 每次新建一个 object 再 lock 也同样有效，因为锁住的是代码块本身。

## 动手问题

- 在 DepositOne 和 Snapshot 设断点，追踪每次访问使用的锁。分别移除写入处或读取处的锁，列出可能发生的交错；最终一次快照能否代表所有中途读取？
