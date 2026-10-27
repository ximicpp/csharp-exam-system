# 第 115 题 · Q115 · 同一线程的嵌套 lock

原题号：`Q235`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q235()，返回的字符串是什么？

```csharp
private static string Q235()
{
    object gate = new();
    int count = 0;
    lock (gate) { count++; lock (gate) { count++; } }
    return count.ToString(CultureInfo.InvariantCulture);
}
```

- A. 发生死锁，调用无法返回。
- B. 编译失败。
- C. `2`
- D. `1`
