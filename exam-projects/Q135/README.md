# 第 135 题 · Q135 · Span 与异步挂起

原题号：`Q45`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

假定 data 长度至少为 4。以下代码在本仓库 C# 14 下不能编译；哪项正确指出根因，并给出保留异步等待的修复方向？

```csharp
public static class Parser
{
    public static async Task<int> ReadAsync(byte[] data)
    {
        Span<byte> header = data.AsSpan(0, 4);
        await Task.Yield();
        return header[0];
    }
}
```

- A. 问题是可写视图；只把 header 改成 ReadOnlySpan<byte>，保持声明和读取位置不变即可。
- B. 问题是 header 的值要跨 await 保留；可以保存 Memory 或数组，并在 await 后重新取得 Span。
- C. 问题是 C# 14 完全禁止 async 方法中声明 Span；所有 Span 使用都必须搬到另一个同步方法。
- D. 问题是数组可能被 GC 移动；在 await 后调用 GC.KeepAlive(data) 即可让原代码通过。
