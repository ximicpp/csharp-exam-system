# 第 2 题 · Q02 · 导入静态成员与引用程序集

原题号：`Q122`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

文件需要调用 System.Math.Max；框架引用中已包含 System.Math，文件没有声明同名 Max 方法。

哪项指令允许直接写 Max(2, 5)，而不自建同名方法？

- A. using Math = System.Math;
- B. global using System;
- C. using static System.Math;
- D. using System;

## 动手问题

- 运行 Example.cs 的实验：它实际观察了题干中的哪个行为？哪些工程条件仍不能仅凭这次输出判断？
