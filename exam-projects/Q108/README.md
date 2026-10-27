# 第 108 题 · Q108 · 自定义索引器的访问

原题号：`Q228`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q228()，返回的字符串是什么？

```csharp
private sealed class Slots228
{
    private readonly int[] data = new int[2];
    public int this[int index] { get => data[index]; set => data[index] = value; }
}

private static string Q228()
{
    Slots228 slots = new();
    slots[1] = 9;
    return $"{slots[0]},{slots[1]}";
}
```

- A. `0,9`
- B. `9,0`
- C. `0,0`
- D. 编译失败。
