# 第 144 题 · Q144 · in 参数与结构体成员调用

原题号：`Q60`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

ReadonlyCopies() 返回什么？

```csharp
private struct Cursor
{
    public int Position;
    public int Advance() => ++Position;
}

private static (int First, int Second) Probe(in Cursor cursor)
    => (cursor.Advance(), cursor.Advance());
```

```csharp
private static (int First, int Second, int Original) ReadonlyCopies()
{
    var cursor = new Cursor();
    var pair = Probe(in cursor);
    return (pair.First, pair.Second, cursor.Position);
}
```

- A. (1, 1, 0)：两次非 readonly 成员调用分别作用于防御性副本，原值未改变。
- B. (1, 2, 2)：in 等同于可写 ref，两次调用直接修改原变量。
- C. (1, 2, 0)：进入 Probe 时只复制一次，此后所有调用共享这个副本。
- D. 编译失败：只读引用上不能调用任何没有 readonly 标记的 struct 方法。
