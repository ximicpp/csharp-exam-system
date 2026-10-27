# 第 62 题 · Q62 · catch 的顺序与可达性

原题号：`Q182`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

以下完整程序为什么在第二个 catch 处产生编译错误？

```csharp
try { throw new FormatException(); }
catch (Exception) { Console.WriteLine("general"); }
catch (FormatException) { Console.WriteLine("specific"); }
```

- A. 前面的 catch (Exception) 已能捕获 FormatException，且没有过滤条件，后面的 catch 因而不可达。
- B. FormatException 不继承 Exception。
- C. try 不能主动 throw。
- D. 一个 try 最多只能有一个 catch。
