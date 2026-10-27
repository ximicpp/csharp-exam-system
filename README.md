# C# 迁移能力考试系统

面向熟悉 C++ / Python 的开发者的中文 C# 自测系统。浏览器考试包含基础 120 题和扩展 40 题；交卷后给出评分、逐题解析和学习资料。另有多人服务：账号、草稿、历史报告和成绩保存在服务器 SQLite 数据库中。题目为自编练习，不是 Microsoft 官方考试。

公开仓库包含题目、答案、解析和评分源码，适合学习自测，不能保证考试保密性。

## 本机考试

需要 Python 3.12 或以上；本机版仅依赖 Python 标准库。在仓库根目录执行：

```sh
python scripts/quiz.py exam
```

浏览器访问 `http://127.0.0.1:8765/`；按 Ctrl+C 停止。草稿保存在当前浏览器，报告在 `artifacts/quiz-reports/`。不要清理浏览器数据或报告目录，除非不再需要记录。

## 多人服务

在仓库根目录创建虚拟环境并安装哈希锁定的依赖：

```sh
python -m venv .venv
```

Windows PowerShell：

```powershell
. ./.venv/Scripts/Activate.ps1
python -m pip install --require-hashes -r scripts/team-requirements.lock
python scripts/quiz_team.py add-user admin --name 管理员 --admin
python scripts/quiz_team.py serve
```

Linux / macOS：

```sh
source .venv/bin/activate
python -m pip install --require-hashes -r scripts/team-requirements.lock
python scripts/quiz_team.py add-user admin --name 管理员 --admin
python scripts/quiz_team.py serve
```

按提示设置管理员密码，访问 `http://127.0.0.1:8768/`，登录管理员后创建学员账号。数据库位于 `artifacts/quiz-team/team.sqlite3`；备份需另行保存，不会随 Git 同步。可选名单模式：复制 `data/quiz-team-roster.example.json` 为 `data/quiz-team-roster.json`，用自己的名单替换示例并以 `python scripts/quiz_team.py serve --roster data/quiz-team-roster.json` 启动；服务启动时读取名单。姓名免密仅为自报身份，无法防止冒名。

Windows 局域网部署可执行 `./scripts/quiz_team_windows.ps1 -Action Prepare -Address 本机内网IPv4`，再执行 `-Action Start`。部署默认读取上述名单；首次准备在受限数据目录生成随机管理员密码 `initial-admin.json`。`-Action DefaultAdmin` 会为已有管理员生成新随机密码并注销原会话。`-Action Stop` 停止服务，`-Action Status` 查看状态。需要开机恢复时管理员执行 `-Action InstallTask`；防火墙与 HTTPS 须另行配置。HTTP 不加密，姓名免密不能验证身份，不应将默认配置直接暴露在互联网；正式部署需 HTTPS、可信身份认证、访问控制和备份。

## 题库与验证

题库数据在 `exercises/quiz/`，题目使用的 C# 示例在 `tests/Quiz.Checks/`。完整题目和答案见 [题库归档](docs/quiz/question-bank.md)。附带的章节供题目解析参考；章节中提到的完整课程项目不包含在本仓库中。

```sh
python -m unittest discover -s tests -p "quiz_*checks.py"
python scripts/quiz.py render
```

单人考试不需要 .NET。题库的 C# 运行和编译诊断验证需要 `global.json` 指定的 .NET 11 RC1 SDK 和 .NET 10 运行时，运行 `python scripts/quiz.py check`。浏览器界面测试另需 Node.js 和 jsdom：在 `.tools/ui-tests` 中安装 jsdom 后运行 `node --test tests/quiz_ui_checks.cjs tests/quiz_team_ui_checks.cjs`。成绩、报告、真实名单、密码和本机部署数据不要提交到仓库。
