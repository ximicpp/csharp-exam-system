# 00 · 环境与工程

目标：看懂项目配置并运行示例。

## 先看一个实际项目

[LanguageTour.csproj](../samples/LanguageTour/LanguageTour.csproj) 的完整内容：

<!-- source: samples/LanguageTour/LanguageTour.csproj -->
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
  </PropertyGroup>
</Project>
```

这个项目生成可执行程序，SDK 默认收集项目目录内的 `.cs` 文件；本例代码在同目录的 [Program.cs](../samples/LanguageTour/Program.cs)。项目类似 CMake target，解决方案聚合多个项目。

本仓库的公共编译配置来自上级目录的 [Directory.Build.props](../Directory.Build.props)，不是写在每个 `.csproj` 中：

<!-- source: Directory.Build.props -->
```xml
<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <LangVersion>14.0</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <Deterministic>true</Deterministic>
  </PropertyGroup>
</Project>
```

`TargetFramework` 选择目标框架和 API，`LangVersion` 限定语法版本；`Nullable` 启用可空分析，`TreatWarningsAsErrors` 将警告视为构建失败。`ImplicitUsings` 自动引入常用命名空间，所以示例使用 `Console` 时无需逐个写 `using System;`。

SDK 版本单独由 [global.json](../global.json) 选择：

<!-- source: global.json -->
```json
{
  "sdk": {
    "version": "11.0.100-rc.1.26425.128",
    "rollForward": "disable",
    "allowPrerelease": true,
    "paths": [ ".tools/dotnet", "$host$" ]
  }
}
```

SDK 提供构建工具，Runtime 负责运行。默认编译路径是 `.cs → IL + 元数据 → JIT → 机器码`，见[第 12 章](12-runtime.md)。

`paths` 让支持该功能的 .NET 10 或更新 host 优先查找仓库局部 SDK，`$host$` 表示当前 dotnet 的安装目录；路径相对于 `global.json`。IDE 与 SDK 仍须版本兼容，Visual Studio 的配置见[环境搭建](setup.md#使用-visual-studio)。

当前开发工具使用 .NET 11 RC1 SDK，显式允许并固定这个候选版本；课程的 `net10.0 / C# 14` 仍由上面的公共配置决定。较新 SDK 可以构建旧目标框架，但不会自动把旧应用改为 .NET 11 应用，setup 因而保留 .NET 10 运行时。独立的 [EnvironmentCheck 项目](../samples/EnvironmentCheck/EnvironmentCheck.csproj)显式使用 `net11.0`，用于确认 .NET 11 编译和运行链路。

`namespace` 组织类型名；`using` 简化名称，不等于 Python 的模块加载。程序集通常为 DLL，可包含库或托管入口；解决方案只聚合项目。

## 迁移误区

- `global.json` 只约束 SDK；[setup 脚本](setup.md)负责安装并验证。
- 现代 .NET 与 .NET Framework 4.x 是不同的目标框架。
- `dotnet run` 默认构建项目；`--` 后的参数才传给程序。

## 可运行入口

```sh
dotnet --version
dotnet run --project samples/EnvironmentCheck
dotnet run --project samples/LanguageTour -- 01
```

SDK 应匹配 `global.json`；环境检查输出包含 `framework=.NETCoreApp,Version=v11.0` 和 `PASS: .NET 11 environment`；最后一条运行 `Syntax()`，输出包含 `division=3; real=3.5`。先按[环境说明](setup.md)加载工具；所有命令在仓库根目录执行。

## 练习与验收

可选练习：读取 [Directory.Build.props](../Directory.Build.props)，找出可空检查和“警告视为错误”的设置；不用修改文件。再从仓库根目录检查项目实际采用的值：

```sh
dotnet msbuild samples/LanguageTour/LanguageTour.csproj -getProperty:Nullable,TreatWarningsAsErrors
dotnet run --project samples/LanguageTour -- 01
```

验收：第一条命令的 `Properties` 中，`Nullable` 为 `enable`、`TreatWarningsAsErrors` 为 `true`；第二条输出包含 `division=3; real=3.5`。两条命令退出码均为 0。

下一章：[语法](01-syntax.md)。
