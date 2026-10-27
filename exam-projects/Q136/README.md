# 第 136 题 · Q136 · 池化缓冲区何时能归还

原题号：`Q46`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用者从 ArrayPool<byte> 租借数组，把一段 ReadOnlyMemory<byte> 交给 SendAsync，已取得尚未完成的 Task。约定发送在 Task 到达成功、故障或取消终态后停止访问缓冲区。调用者保留所有权，期间不再写入借出的区段。

调用者应把唯一一次 Return 安排在哪个位置，才能满足归还契约？

- A. 在 try 中 await 这个 Task，在对应 finally 中把数组归还给原池。
- B. 紧接取得 Task 之后归还；传入 ReadOnlyMemory 已使发送拥有独立的字节副本。
- C. 把数组引用存入发送状态对象后归还；强引用会阻止池把数组交给其他请求。
- D. CancellationTokenSource.Cancel() 返回后归还；无需等待发送 Task 到达终态。

## 动手问题

- 运行 Example.cs 的实验：它实际观察了题干中的哪个行为？哪些工程条件仍不能仅凭这次输出判断？
