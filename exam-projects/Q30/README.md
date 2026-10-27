# 第 30 题 · Q30 · switch 分支的结束方式

原题号：`Q150`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

以下完整程序为什么在 case 1 分支末尾产生编译错误？

```csharp
int kind = int.Parse("1", System.Globalization.CultureInfo.InvariantCulture);
switch (kind)
{
    case 1: Console.WriteLine("one");
    case 2: Console.WriteLine("two"); break;
}
```

- A. Console.WriteLine 不能写在 case 内。
- B. case 1 执行 WriteLine 后不能隐式继续到 case 2；需用 break、return、throw 或合法的显式跳转等结束该分支。
- C. case 只能接受字符串常量。
- D. 同一 switch 只能有一个 case。
