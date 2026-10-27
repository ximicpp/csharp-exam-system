# 第 85 题 · Q85 · 取消令牌与检查点

原题号：`Q205`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q205()，返回的字符串是什么？

```csharp
private static string Q205()
{
    CancellationToken token = new(canceled: true);
    try { token.ThrowIfCancellationRequested(); }
    catch (OperationCanceledException error) { return $"{error.CancellationToken == token},canceled"; }
    return "continued";
}
```

- A. `False,canceled`
- B. 编译失败。
- C. `True,canceled`
- D. `continued`
