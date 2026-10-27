# 第 92 题 · Q92 · 封闭泛型类型与泛型定义

原题号：`Q212`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q212()，返回的字符串是什么？

```csharp
private static string Q212()
{
    Type closed = typeof(List<int>);
    Type definition = closed.GetGenericTypeDefinition();
    return $"{closed.IsGenericType},{definition == typeof(List<>)},{closed == definition}";
}
```

- A. `True,True,True`
- B. `False,True,False`
- C. `True,True,False`
- D. `True,False,False`
