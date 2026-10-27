# 第 117 题 · Q117 · Release 下的条件编译

原题号：`Q237`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

本题按仓库 Release 配置编译，未定义 DEBUG 符号。调用 Q237()，返回的字符串是什么？

```csharp
private static string Q237()
{
    #if DEBUG
    return "debug";
    #else
    return "release";
    #endif
}
```

- A. `debug`
- B. `debug,release`
- C. 编译失败。
- D. `release`

## 动手问题

- 分别用 Debug 和 Release 构建运行，比较输出与 #if 分支。本题作答采用题干指定的 Release；可选择 Release 调试配置，或在本目录运行 dotnet run --project Q117 -c Release。
