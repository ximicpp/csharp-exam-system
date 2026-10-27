# 第 6 题 · Q06 · 十进制字面量的计算

原题号：`Q126`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q126()，返回的字符串是什么？

```csharp
private static string Q126()
{
    decimal amount = 0.1m + 0.2m;
    return amount.ToString(CultureInfo.InvariantCulture);
}
```

- A. `0.3`
- B. `0.30000000000000004`
- C. `0`
- D. 编译失败。
