# 第 22 题 · Q22 · 条件表达式的分支求值

原题号：`Q142`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q142()，返回的字符串是什么？

```csharp
private static string Q142()
{
    int calls = 0;
    int Next() => ++calls;
    bool fast = true;
    int chosen = fast ? Next() : Next() + 10;
    return $"{chosen},{calls}";
}
```

- A. `1,2`
- B. `12,2`
- C. `11,1`
- D. `1,1`
