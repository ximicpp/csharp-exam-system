# 第 112 题 · Q112 · 普通类的主构造参数

原题号：`Q232`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q232()，返回的字符串是什么？

```csharp
private sealed class Cursor232(int position)
{
    public void Move() => position++;
    public int Position() => position;
}

private static string Q232()
{
    Cursor232 cursor = new(3);
    cursor.Move();
    return cursor.Position().ToString(CultureInfo.InvariantCulture);
}
```

- A. `0`
- B. 编译失败。
- C. `4`
- D. `3`
