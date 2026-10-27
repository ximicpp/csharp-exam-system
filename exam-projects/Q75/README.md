# 第 75 题 · Q75 · 左外连接与未匹配项

原题号：`Q195`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q195()，返回的字符串是什么？

```csharp
private static string Q195()
{
    int[] orders = [1, 2];
    var customers = new[] { (Id: 1, Name: "Lin") };
    var rows = from id in orders
               join customer in customers on id equals customer.Id into matches
               from customer in matches.DefaultIfEmpty()
               select $"{id}:{customer.Name ?? "missing"}";
    return string.Join(",", rows);
}
```

- A. `1:Lin,2:missing`
- B. `1:Lin`
- C. `1:Lin,2:Lin`
- D. `1:missing,2:missing`
