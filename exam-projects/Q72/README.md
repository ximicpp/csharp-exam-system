# 第 72 题 · Q72 · 查询 let 与中间计算

原题号：`Q192`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q192()，返回的字符串是什么？

```csharp
private static string Q192()
{
    int calls = 0;
    int Square(int value) { calls++; return value * value; }
    int[] source = [2, 3];
    var query = from value in source let square = Square(value) where square > 4 select square;
    string result = string.Join(",", query);
    return $"{result}|{calls}";
}
```

- A. `9|2`
- B. `9|3`
- C. `4,9|2`
- D. `9|0`
