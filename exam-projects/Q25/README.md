# 第 25 题 · Q25 · when 条件与匹配顺序

原题号：`Q145`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q145()，返回的字符串是什么？

```csharp
private static string Q145()
{
    static string Classify(int count) => count switch
    {
        int n when n >= 0 => "nonnegative",
        int n when n > 10 => "large",
        _ => "negative"
    };
    return Classify(20);
}
```

- A. `nonnegative`
- B. `large`
- C. `negative`
- D. 编译失败。
