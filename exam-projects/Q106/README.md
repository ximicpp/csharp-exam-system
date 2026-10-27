# 第 106 题 · Q106 · 标志枚举的位组合

原题号：`Q226`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q226()，返回的字符串是什么？

```csharp
[Flags]
private enum Access226 { None = 0, Read = 1, Write = 2, Execute = 4 }

private static string Q226()
{
    Access226 permissions = Access226.Read | Access226.Write;
    return $"{(int)permissions},{permissions.HasFlag(Access226.Write)},{permissions.HasFlag(Access226.Execute)}";
}
```

- A. `3,True,False`
- B. `2,True,False`
- C. `3,True,True`
- D. 编译失败。
