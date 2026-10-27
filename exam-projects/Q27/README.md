# 第 27 题 · Q27 · 属性模式能否接受 null

原题号：`Q147`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q147()，返回的字符串是什么？

```csharp
private sealed record Label147(string Text);

private static string Q147()
{
    Label147? missing = null;
    Label147 empty = new("");
    Label147 valid = new("go");
    return $"{missing is { Text.Length: > 0 }},{empty is { Text.Length: > 0 }},{valid is { Text.Length: > 0 }}";
}
```

- A. `False,True,True`
- B. 编译失败。
- C. `False,False,True`
- D. `True,False,True`
