# 第 102 题 · Q102 · 类变量赋值与对象状态

原题号：`Q222`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q222()，返回的字符串是什么？

```csharp
private sealed class Box222 { public int Value; }

private static string Q222()
{
    Box222 first = new() { Value = 3 };
    Box222 second = first;
    second.Value = 8;
    return $"{first.Value},{ReferenceEquals(first, second)}";
}
```

- A. `3,True`
- B. `8,False`
- C. `8,True`
- D. `3,False`
