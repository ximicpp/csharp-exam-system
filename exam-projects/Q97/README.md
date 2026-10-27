# 第 97 题 · Q97 · field 支持的属性规范化

原题号：`Q217`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q217()，返回的字符串是什么？

```csharp
private sealed class Label217
{
    public string Text { get; set => field = value.Trim(); } = "";
}

private static string Q217()
{
    Label217 label = new() { Text = "  go  " };
    return $"[{label.Text}]";
}
```

- A. `[go]`
- B. `[  go  ]`
- C. `[]`
- D. 编译失败。
