# C# 迁移能力考试系统

面向熟悉 C++ / Python 的开发者的中文 C# 自测系统。浏览器考试有基础 120 题、扩展 40 题，交卷后显示评分和逐题解析；另有保存账号、草稿和成绩的多人服务。题目为自编练习，不是 Microsoft 官方考试。

本仓库公开题目、答案、解析和评分源码，适合学习自测，不能用于保密考试。

## 克隆与准备

先安装 Git 和 [Python](https://www.python.org/downloads/) 3.12 或更新版。Windows 安装 Python 时可同时安装 Python Launcher；Linux / macOS 的 `python3` 须指向 3.12 或更新版。下载代码并进入仓库：

```sh
git clone https://github.com/ximicpp/csharp-exam-system.git
cd csharp-exam-system
```

后续命令均从仓库根目录开始；题目工程章节会明确要求进入 `exam-projects`。Windows 命令使用 PowerShell。如果没有 Python Launcher，可用已加入 PATH 的 `python` 代替 `py -3`，先用 `python --version` 检查版本。

## 本机考试

本机版只使用 Python 标准库，不需要 .NET 或额外安装 Python 依赖。

Windows PowerShell：

```powershell
py -3 --version
py -3 scripts/quiz.py exam
```

Linux / macOS：

```sh
python3 --version
python3 scripts/quiz.py exam
```

保持终端运行，访问 `http://127.0.0.1:8765/`，结束时按 Ctrl+C。若不希望自动打开浏览器，在命令末尾加 `--no-browser`；端口被占用时加 `--port 8766`，并访问对应端口。草稿保存在当前浏览器，报告保存在 `artifacts/quiz-reports/`；清除浏览器数据或删除报告会丢失相应记录。

## 每题一个 C# 工程

[题目索引](exam-projects/README.md)包含与考试显示号一致的 Q01–Q160。每题是独立工程，提供题面、可编辑源码和 VS Code 配置。11 道题保留原始编译错误；构建整个解决方案会报告这些错误，不影响其他题单独运行。

在仓库根目录进入 `exam-projects`。Windows PowerShell：

```powershell
cd exam-projects
./setup.cmd
./.tools/dotnet11/dotnet.exe run --project Q04
./.tools/dotnet11/dotnet.exe run --project Q117 -c Release
```

Q04 预期输出 `-2,-1`，Q117 预期输出 `release`；两条命令应以退出码 0 结束。Windows 初始化会下载固定的 .NET 11 RC1 SDK，并在缺少时安装 VS Code 和推荐扩展；退出码为 0 且显示 `PASS: environment ready` 才算完成。网络和磁盘空间须足以下载 SDK。脚本在子进程中设置环境，因此外部终端使用上述 SDK 路径，无须依赖系统 `dotnet`。

Linux / macOS：

```sh
cd exam-projects
bash setup.sh
./.tools/dotnet11/dotnet run --project Q04
./.tools/dotnet11/dotnet run --project Q117 -c Release
```

该脚本安装固定 SDK 和运行时，成功时显示 `PASS: .NET 11 SDK and runtime ready`；VS Code 和扩展需自行安装。[推荐扩展](exam-projects/.vscode/extensions.json)包括 C#、C# Dev Kit 和 ILSpy。Windows、Linux 或 macOS 中均可在 VS Code **打开 `exam-projects` 文件夹**，打开题目的 `Example.cs`，按 Ctrl+Shift+B 构建当前题、F5 调试；完成后在终端运行 `cd ..` 回到仓库根目录。项目本身只展示程序的实际行为，不评分、不附答案。

## 多人服务

多人服务需要 Flask 和 Waitress。以下命令在仓库根目录执行，虚拟环境与运行数据不会提交 Git。

Windows PowerShell：

```powershell
py -3 -m venv .venv
./.venv/Scripts/python.exe -m pip install --require-hashes -r scripts/team-requirements.lock
./.venv/Scripts/python.exe scripts/quiz_team.py add-user admin --name 管理员 --admin
./.venv/Scripts/python.exe scripts/quiz_team.py serve
```

Linux / macOS：

```sh
python3 -m venv .venv
./.venv/bin/python -m pip install --require-hashes -r scripts/team-requirements.lock
./.venv/bin/python scripts/quiz_team.py add-user admin --name 管理员 --admin
./.venv/bin/python scripts/quiz_team.py serve
```

如果 Linux 报错说无法创建虚拟环境，请安装与所用 Python 版本匹配的 venv 支持包后重试。

创建管理员时按提示输入两次相同的 12–128 字符密码；密码不会显示。看到 `PASS: created admin admin` 后启动服务，保持终端运行并访问 `http://127.0.0.1:8768/`。管理员登录后进入“成绩汇总 / 账号”，创建学员账号；初始密码只显示一次，须单独交给学员，学员首次登录后修改密码。按 Ctrl+C 停止服务。

数据库默认为 `artifacts/quiz-team/team.sqlite3`，不会随 Git 同步。可用以下命令创建一致的在线备份，目标文件必须不存在：

```powershell
./.venv/Scripts/python.exe scripts/quiz_team.py backup artifacts/quiz-team/backup.sqlite3
```

Linux / macOS 将命令中的 Python 路径换为 `./.venv/bin/python`。备份应另存于受控位置。

### 可选：名单免密登录

复制 `data/quiz-team-roster.example.json` 为 `data/quiz-team-roster.json`，将示例替换为自己的名单；每个人的 `id` 要保持稳定。实际名单已被 Git 忽略。先停止服务，再在上述 `serve` 命令末尾加 `--roster data/quiz-team-roster.json` 启动。名单在启动时读取，修改后须重启；名单模式下管理员不能通过网页创建密码学员。姓名只是自报，其他人可以冒名，不是身份认证。

### 可选：Windows 局域网部署

先完成多人服务的虚拟环境、依赖和名单配置；运行数据库与上面的本机验证数据库分开。下面的 IP 仅为示例，须替换为服务器自身的内网 IPv4：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./scripts/quiz_team_windows.ps1 -Action Prepare -Address 192.168.1.20
./scripts/quiz_team_windows.ps1 -Action Start
./scripts/quiz_team_windows.ps1 -Action Status
```

`Prepare` 下载并校验 Caddy，在当前用户的 `CSharpQuizPublic-data` 目录生成配置、数据库和 `initial-admin.json`；其中包含随机管理员密码，须妥善保管。其他电脑使用 `http://192.168.1.20:8080/`，实际地址以服务器 IP 为准。

在同一部署用户的**管理员 PowerShell**中，从仓库根目录执行 `./scripts/quiz_team_windows.ps1 -Action Firewall`，开放本机域/专用网络配置的同网段网页端口；用另一台机器实际验证访问。若需要开机启动和故障恢复，在管理员 PowerShell 执行 `./scripts/quiz_team_windows.ps1 -Action InstallTask`。若提升时换用了其他 Windows 账号，须用 `-DataDirectory` 指向原部署用户的实际数据目录。`-Action Stop` 停止服务，`-Action DefaultAdmin` 会生成新随机管理员密码并注销原会话。

默认 HTTP 不加密，名单姓名也不能验证身份；不要把默认配置直接暴露在互联网。正式部署应使用 HTTPS、可信身份认证、访问控制，并备份数据库。

## 题库维护与验证

题库数据位于 `exercises/quiz/`，题目使用的 C# 示例位于 `tests/Quiz.Checks/`；[完整题库归档](docs/quiz/question-bank.md)包含答案。附带章节供解析参考，章节中提到的完整课程项目未包含在本仓库。

多人依赖安装完成后，在仓库根目录运行 Python 回归检查，Windows 用 `./.venv/Scripts/python.exe -m unittest discover -s tests -p "quiz_*checks.py"`，Linux / macOS 用 `./.venv/bin/python -m unittest discover -s tests -p "quiz_*checks.py"`。使用同一虚拟环境的 Python 运行 `scripts/quiz.py render` 可重新生成题库文档。

`scripts/quiz.py check` 调用 PATH 中的 `dotnet`，其安装位置须同时提供根目录 `global.json` 指定的 .NET 11 RC1 SDK 和 .NET 10 运行时。题目工程初始化只保证 .NET 11 运行时，不能单独满足该检查。

浏览器界面回归另需 Node.js 18+ 和 npm。在仓库根目录，Windows PowerShell 执行：

```powershell
npm.cmd install --prefix .tools/ui-tests jsdom@26.1.0
$env:PYTHON = (Resolve-Path ./.venv/Scripts/python.exe).Path
node --test tests/quiz_ui_checks.cjs tests/quiz_team_ui_checks.cjs
```

Linux / macOS 执行：

```sh
npm install --prefix .tools/ui-tests jsdom@26.1.0
PYTHON="$PWD/.venv/bin/python" node --test tests/quiz_ui_checks.cjs tests/quiz_team_ui_checks.cjs
```

成绩、报告、真实名单、密码和部署数据不要提交到仓库。
