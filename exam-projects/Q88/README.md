# 第 88 题 · Q88 · SemaphoreSlim 的许可与等待

原题号：`Q208`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q208()，得到的字符串是什么？

```csharp
private static async Task<string> Q208()
{
    using SemaphoreSlim gate = new(1, 1);
    await gate.WaitAsync();
    Task next = gate.WaitAsync();
    bool waiting = !next.IsCompleted;
    gate.Release();
    await next;
    int available = gate.CurrentCount;
    gate.Release();
    return $"{waiting},{available}";
}
```

- A. `True,0`
- B. `False,0`
- C. `True,1`
- D. `False,1`
