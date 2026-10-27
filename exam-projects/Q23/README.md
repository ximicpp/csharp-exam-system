# 第 23 题 · Q23 · null 条件索引会不会计算索引

原题号：`Q143`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q143()，返回的字符串是什么？

```csharp
private static string Q143()
{
    int calls = 0;
    int Index() { calls++; return 0; }
    int[]? data = null;
    int value = data?[Index()] ?? 9;
    return $"{value},{calls}";
}
```

- A. `9,1`
- B. `0,1`
- C. 编译失败。
- D. `9,0`
