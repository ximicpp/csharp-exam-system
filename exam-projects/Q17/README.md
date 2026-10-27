# 第 17 题 · Q17 · Remove 删除哪一个重复项

原题号：`Q137`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q137()，返回的字符串是什么？

```csharp
private static string Q137()
{
    List<int> pending = [4, 7, 4];
    bool removed = pending.Remove(4);
    return $"{removed}:{string.Join(",", pending)}";
}
```

- A. `False:4,7,4`
- B. `True:7,4`
- C. `True:7`
- D. `True:4,7`
