# 第 132 题 · Q132 · object 中保存的是可变值的哪一份

原题号：`Q42`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 BoxingSnapshot() 返回什么？

```csharp
private struct Position
{
    public int X;
}
```

```csharp
private static (int Original, int Boxed, int Unboxed) BoxingSnapshot()
{
    var original = new Position { X = 3 };
    object boxed = original;
    original.X = 9;
    Position unboxed = (Position)boxed;
    unboxed.X = 7;
    return (original.X, ((Position)boxed).X, unboxed.X);
}
```

- A. (9, 3, 7)：装箱和普通解箱赋值各产生一份值复制。
- B. (9, 9, 7)：object 始终指向 original 变量的最新值。
- C. (7, 7, 7)：解箱赋值使三个变量共享可写存储。
- D. (9, 7, 7)：解箱出的普通变量是箱内值的可写别名。
