# 第 10 题 · Q10 · 局部变量的赋值要求

原题号：`Q130`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

以下完整程序为什么不能编译？

```csharp
int result;
Console.WriteLine(result);
```

- A. int 类型不能作为局部变量。
- B. Console.WriteLine 只接受 string。
- C. 顶级语句必须显式返回整数退出码。
- D. 局部变量 result 在被读取前没有赋值。
