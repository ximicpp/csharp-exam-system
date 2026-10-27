# 第 121 题 · Q121 · 修改对象和替换调用方变量

原题号：`Q01`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

PassReferences() 返回什么？

```csharp
private sealed class Session
{
    public int Revision { get; set; }
}

private static void Update(Session session)
{
    session.Revision = 2;
    session = new Session { Revision = 9 };
}

private static void Replace(ref Session session) =>
    session = new Session { Revision = 3 };

private static (int AfterUpdate, int AfterReplace) PassReferences()
{
    var session = new Session { Revision = 1 };
    Update(session);
    int first = session.Revision;
    Replace(ref session);
    return (first, session.Revision);
}
```

- A. (9, 3)
- B. (2, 3)
- C. (1, 3)
- D. (2, 2)
