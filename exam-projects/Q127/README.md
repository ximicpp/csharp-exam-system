# 第 127 题 · Q127 · 回调参数中变型的安全方向

原题号：`Q11`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

插件 API 将字符串序列交给回调，参数类型是 Action<IEnumerable<string>>；调用方已有不同输入类型的处理器，希望直接复用。

以下哪个现有委托变量可以隐式转换为该参数类型？不使用强制转换、lambda 包装或新建集合；只依据声明的类型判断。

- A. Action<List<string>>：要求输入是字符串列表的处理器。
- B. Action<IEnumerable<int>>：能处理整数序列的处理器。
- C. Action<IEnumerable<object>>：能处理对象序列的处理器。
- D. Action<List<object>>：要求输入是对象列表的处理器。

## 动手问题

- 运行 Example.cs 的实验：它实际观察了题干中的哪个行为？哪些工程条件仍不能仅凭这次输出判断？
