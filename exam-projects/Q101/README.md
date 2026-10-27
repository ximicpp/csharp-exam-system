# 第 101 题 · Q101 · 结构体复制与数值字段

原题号：`Q221`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q221()，返回的字符串是什么？

```csharp
private struct Position221 { public int X; }

private static string Q221()
{
    Position221 start = new() { X = 3 };
    Position221 copy = start;
    copy.X = 8;
    return $"{start.X},{copy.X}";
}
```

- A. 编译失败。
- B. `3,8`
- C. `8,8`
- D. `3,3`
