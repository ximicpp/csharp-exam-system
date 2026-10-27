# 第 4 题 · Q04 · 负数的商与余数

原题号：`Q124`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q124()，返回的字符串是什么？

```csharp
private static string Q124()
{
    int offset = -7;
    return $"{offset / 3},{offset % 3}";
}
```

- A. `-2,-1`
- B. `-3,2`
- C. `-2,1`
- D. `-3,-1`
