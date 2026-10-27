# 第 46 题 · Q46 · record struct 的 with 更新

原题号：`Q166`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q166()，返回的字符串是什么？

```csharp
private record struct Point166(int X, int Y);

private static string Q166()
{
    Point166 start = new(2, 3);
    Point166 moved = start with { X = 7 };
    return $"{start.X},{start.Y}|{moved.X},{moved.Y}";
}
```

- A. `2,3|7,0`
- B. 编译失败。
- C. `2,3|7,3`
- D. `7,3|7,3`
