# 第 81 题 · Q81 · await 已完成的 Task

原题号：`Q201`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q201()，得到的字符串是什么？

```csharp
private static async Task<int> Answer201() => await Task.FromResult(5) + 1;

private static async Task<string> Q201()
{
    Task<int> result = Answer201();
    return $"{result.IsCompletedSuccessfully},{await result}";
}
```

- A. 编译失败。
- B. `True,6`
- C. `False,6`
- D. `True,5`
