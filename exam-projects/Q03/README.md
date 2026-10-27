# 第 3 题 · Q03 · var 的类型推断与后续赋值

原题号：`Q123`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

这份完整程序为何不能编译？

```csharp
var retries = 2;
retries = 2.5;
Console.WriteLine(retries);
```

- A. 顶级语句禁止声明 var。
- B. 必须先把文件命名为 Program.cs。
- C. retries 被推断为 int，double 到 int 不存在隐式转换。
- D. var 变量必须在每次赋值时重新写 var。
