# 第 89 题 · Q89 · CompareExchange 的返回值

原题号：`Q209`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q209()，返回的字符串是什么？

```csharp
private static string Q209()
{
    int state = 2;
    int before = Interlocked.CompareExchange(ref state, 5, 2);
    int rejected = Interlocked.CompareExchange(ref state, 9, 2);
    return $"{before},{rejected},{state}";
}
```

- A. `2,2,9`
- B. `2,5,9`
- C. `2,5,5`
- D. `5,9,9`
