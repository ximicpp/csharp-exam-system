# 第 33 题 · Q33 · TryParse 失败时的输出

原题号：`Q153`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q153()，返回的字符串是什么？

```csharp
private static string Q153()
{
    int value = 17;
    bool ok = int.TryParse("not-a-number", NumberStyles.Integer, CultureInfo.InvariantCulture, out value);
    return $"{ok},{value}";
}
```

- A. `False,0`
- B. `False,17`
- C. `True,0`
- D. 编译失败。
