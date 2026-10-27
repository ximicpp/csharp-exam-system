# 第 160 题 · Q160 · ConfigureAwait(false) 的精确边界

原题号：`Q38`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

对普通 Task，await task.ConfigureAwait(false) 相比 await task，改变的是哪项行为？

- A. 清除当前 ExecutionContext，使后续代码看不到原来的 AsyncLocal 值。
- B. 强制本次 await 挂起，并把后续代码切换到另一个线程池线程。
- C. 让调用方在等待这个方法返回的 Task 时，也不能捕获调用方自己的上下文。
- D. 本次等待挂起时，不要求将后续代码调度回原 SynchronizationContext 或非默认 TaskScheduler。

## 动手问题

- 运行已完成／未完成任务与两种 ConfigureAwait 参数的四组实验，记录任务状态、Post 次数、AsyncLocal 与上下文标志。这个自定义上下文实验能观察什么，尚未覆盖哪些调度环境？
