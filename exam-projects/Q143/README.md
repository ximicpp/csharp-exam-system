# 第 143 题 · Q143 · 并发字典保证工厂只执行一次吗

原题号：`Q58`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

两个线程同时对空 ConcurrentDictionary<string, object> 的同一键调用 GetOrAdd(key, factory)。用阶段信号确保两个 factory 都已进入，才让它们分别返回各自 new object()；过程中没有删除或其他写入。

在这个受控交错下，哪项描述正确？

- A. 这个前提不可能发生，GetOrAdd 会在字典内部锁下串行执行 factory。
- B. factory 共运行两次，但只存入一个值；两个 GetOrAdd 调用返回同一个获胜对象。
- C. factory 共运行两次，字典会为同一个键保留两个不同的对象。
- D. 只存入一个值，但两个 GetOrAdd 一定分别返回各自工厂创建的对象。
