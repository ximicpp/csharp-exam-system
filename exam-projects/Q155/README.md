# 第 155 题 · Q155 · IQueryable 的表达式在哪里执行

原题号：`Q30`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

数据库查询中的自定义 Normalize 方法不受提供方支持，团队准备把这一项筛选移到本地。

上游 IQueryable 查询受提供方支持。将含 Normalize 的筛选改为对 AsEnumerable() 的结果调用标准 Enumerable.Where 后，这一筛选会怎样执行？

- A. AsEnumerable 调用时立即完成筛选，并把结果缓存供后续重复使用。
- B. AsEnumerable 让提供方自动将 Normalize 翻译为数据库查询。
- C. Enumerable.Where 仍把谓词加入上游表达式树，交由原提供方执行。
- D. 枚举时消费上游查询结果，并在本地调用 Normalize 执行筛选。

## 动手问题

- 运行 Example.cs 的实验：它实际观察了题干中的哪个行为？哪些工程条件仍不能仅凭这次输出判断？
