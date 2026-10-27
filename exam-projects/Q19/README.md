# 第 19 题 · Q19 · Stack 的 Peek 与 Pop

原题号：`Q139`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q139()，返回的字符串是什么？

```csharp
private static string Q139()
{
    Stack<string> undo = new();
    undo.Push("edit");
    undo.Push("rename");
    string preview = undo.Peek();
    string removed = undo.Pop();
    return $"{preview},{removed},{undo.Count}";
}
```

- A. `rename,edit,0`
- B. `rename,rename,0`
- C. `rename,rename,1`
- D. `edit,edit,1`
