# 使用项目

需要 .NET SDK 11.0.100-rc.1.26425.128（.NET 11 RC1）。首次使用，在本目录的 Windows 终端运行：

```powershell
./setup.cmd
```

本学习包包含考试系统展示的全部 160 题：基础 120 题与扩展 40 题。工程目录、`.csproj` 名称和程序集名称 Q01–Q160 与考试显示号一致。原题号保留在各题 README、根目录索引与 `manifest.json` 的 `original_id` 字段中；题目代码中的原有方法名与注释保持原样。

脚本准备项目局部 SDK 与运行时、安装缺少的 VS Code 用户版及 C#／C# Dev Kit／ILSpy 扩展、还原 160 个项目的依赖，再编译运行独立的环境检查。显示 `PASS: environment ready` 且退出码为 0 才表示初始化成功。可以重复运行，已就绪的 SDK、编辑器与扩展会复用。脚本不运行题目、不验证答案，也不修改题目源码或题面。

也可直接用 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./setup.ps1
```

初始化无需管理员权限：使用微软官方安装入口，把指定 SDK 与运行时准备到本目录 `.tools/dotnet11`；缺少 VS Code 时为当前用户安装。Windows 可用 `./setup.cmd -ExistingSdkRoot 已有SDK安装目录` 复用同版本 SDK；`./setup.cmd -OpenCode` 在成功后打开本文件夹。首次下载需要访问微软下载站点与 VS Code Marketplace。失败先查看报错，解决原因后再运行。

Linux／macOS 的 `bash setup.sh` 仅准备局部 SDK 与运行时；VS Code 和推荐扩展需自行安装。SDK 与局部工具不会提交 SVN。项目语言为 C# 14，启用 nullable、隐式 using 与警告视为错误；额外 using 位于各题源码。

在 VS Code 的“文件 → 打开文件夹”中选择本目录 `CSharpExam`。完成 setup 后新建终端；若此前已打开该目录，可执行 `Developer: Reload Window` 让语言服务重新识别 SDK。普通文件树显示题目源码；`C# Project Details` 显示项目分组和依赖。

题目与选项在 README，修改 Example.cs。打开某题源码后，Ctrl+Shift+B 默认构建本题 Debug；F5 调试。配置列表也有 Release。命令面板的 `Tasks: Run Task` → `Exam: run question` 可选择题目与编译配置。

从本目录运行：

```sh
dotnet run --project Q04 -c Debug
dotnet run --project Q117 -c Release
```

终端中的 `dotnet --version` 应为固定 SDK 版本。如果外部终端仍优先调用旧系统 dotnet，可直接使用 `.tools/dotnet11/dotnet.exe`（Windows）或 `.tools/dotnet11/dotnet`（Linux／macOS）。构建任务与 F5 已显式使用局部 SDK／运行时，其他项目的系统环境保持原样。

题干另有指定的环境或配置时按题干执行。11 道原题保留编译错误，直接构建会报告错误；修改后可重新构建运行。整体 `dotnet build CSharpExam.slnx` 也会报告这些错误，其余题目可单独构建。

程序只打印实际观察，不比较预期答案或评分。先预测，再运行，改变一个输入后重新观察。并发和工程契约题的某一次输出不等于对所有条件的证明。

例如考试第 4 题对应 `Q04/Q04.csproj`（原题号 Q124）；第 117 题对应 `Q117/Q117.csproj`（原题号 Q237，题干指定 Release）。

编译后可用 ILSpy 加载 `Q04/bin/Debug/net11.0/Q04.dll` 查看展开后的 C# 与 IL；修改、重建后 Reload。bin/obj 是本机构建产物，不提交 SVN。
