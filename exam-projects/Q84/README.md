# 第 84 题 · Q84 · async 方法的异常传播

原题号：`Q204`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q204()，得到的字符串是什么？

```csharp
private static async Task<int> Fail204()
{
    int value = int.Parse("bad", CultureInfo.InvariantCulture);
    await Task.CompletedTask;
    return value;
}

private static async Task<string> Q204()
{
    Task<int> task = Fail204();
    try { _ = await task; }
    catch (FormatException) { return $"{task.IsFaulted},caught"; }
    return "success";
}
```

- A. `False,caught`
- B. `success`
- C. 调用 Fail204 时异常直接传播到 Q204，无法返回字符串。
- D. `True,caught`
