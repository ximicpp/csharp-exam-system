# 第 146 题 · Q146 · 属性访问器的执行

原题号：`Q84`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

ReadProperty() 返回什么？

```csharp
private sealed class Reading
{
    private int reads;
    public int Value => ++reads;
}
private static (int First, int Second) ReadProperty()
{
    var reading = new Reading();
    return (reading.Value, reading.Value);
}
```

- A. (1, 1)
- B. (0, 0)
- C. 不能编译：getter 不能修改对象
- D. (1, 2)
