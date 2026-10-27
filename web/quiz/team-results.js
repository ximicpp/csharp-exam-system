"use strict";
(async () => {
  const team = window.quizTeam;
  const app = document.getElementById("app");
  function node(tag, text, className) {
    const value = document.createElement(tag);
    if (text !== undefined) value.textContent = text;
    if (className) value.className = className;
    return value;
  }
  function table(headings, rows) {
    const wrapper = node("div", undefined, "team-table-scroll");
    const table = node("table", undefined, "team-table");
    const header = node("thead"); const heading = node("tr");
    headings.forEach(text => heading.append(node("th", text))); header.append(heading);
    const body = node("tbody");
    rows.forEach(row => {
      const tr = node("tr");
      row.forEach(value => { const td = node("td"); td.append(value instanceof Element ? value : document.createTextNode(String(value ?? "—"))); tr.append(td); });
      body.append(tr);
    });
    table.append(header, body); wrapper.append(table); return wrapper;
  }
  const paperName = id => id === "combined" ? "基础与扩展 · 160 题" : id === "microsoft" ? "基础题（旧卷）" : "扩展题（旧卷）";
  const attributionName = value => ({ matched: "已归属名单", unmatched: "未归属", legacy: "原账号" })[value || "legacy"];
  const sourceName = value => ({ domain: "域认证", self_reported: "自报身份", password: "账号密码" })[value || "password"];
  try {
    await team.initialize();
    const admin = window.location.pathname === "/admin";
    if (admin && team.user().role !== "admin") throw new Error("只有管理员可以查看成绩汇总。");
    const shell = node("section", undefined, "team-dashboard");
    shell.append(node("h1", admin ? "成绩汇总" : "我的成绩与考试记录"), node("p", "当前为基础与扩展合并的 160 题考试。旧卷及不同版本的成绩分别汇总，保留原分数。日期筛选使用 UTC。"));
    const filters = node("form", undefined, "team-filters");
    const controls = {};
    for (const [name, label, options] of [
      ["paper", "题库", [["all", "全部记录"], ["combined", "基础与扩展 · 160 题"], ["microsoft", "基础题（旧卷）"], ["extension", "扩展题（旧卷）"]]],
      ["policy", "重复作答口径", [["first", "首次"], ["latest", "最近"], ["best", "最高正确率"], ["all", "所有轮次"]]],
      ...(admin ? [["attribution", "用户归属", [["all", "全部记录（分别统计）"], ["matched", "已归属名单"], ["unmatched", "未归属"], ["legacy", "原账号"]]]] : []),
    ]) {
      const wrapper = node("label", label), select = node("select"); select.name = name;
      options.forEach(([value, text]) => { const option = node("option", text); option.value = value; select.append(option); });
      controls[name] = select; wrapper.append(select); filters.append(wrapper);
    }
    for (const [name, text, type] of [["version", "题库版本（可空）", "text"], ["from", "开始日期", "date"], ["to", "结束日期", "date"]]) {
      const wrapper = node("label", text), input = node("input"); input.name = name; input.type = type;
      if (name === "version") { input.maxLength = 64; input.placeholder = "完整版本哈希"; }
      controls[name] = input; wrapper.append(input); filters.append(wrapper);
    }
    const submit = node("button", "查询", "button primary"); submit.type = "submit";
    const csv = node("a", "下载当前筛选 CSV", "button secondary");
    filters.append(submit, csv);
    const error = node("p", "", "error-text"); error.setAttribute("role", "alert");
    const content = node("div"); shell.append(filters, error, content); app.replaceChildren(shell);
    let requestNumber = 0;
    async function load() {
      const serial = ++requestNumber;
      submit.disabled = true; error.textContent = "";
      const query = new URLSearchParams({ scope: admin ? "all" : "self" });
      Object.entries(controls).forEach(([name, input]) => { if (input.value) query.set(name, input.value); });
      csv.href = "/api/results?" + query + "&format=csv";
      try {
        const result = await team.request("/api/results?" + query);
        if (serial !== requestNumber) return;
        content.replaceChildren(node("p", `本次筛选 ${result.records.length} 条成绩。分数和正确率的分母均为本卷全部题数，错答与漏答计 0 分。`));
        result.summaries.forEach(summary => {
          const card = node("section", undefined, "team-summary");
          card.append(node("h2", `${paperName(summary.paper)}${admin ? " · " + attributionName(summary.identity_status) : ""} · 考试`),
            node("p", `${summary.people} 人 · ${summary.attempts} 轮 · 平均正确率 ${summary.average_percent ?? "—"}%`),
            node("p", `版本：${summary.version}`));
          const groups = node("details"); groups.append(node("summary", "分组表现"), table(["方向 / 单元", "答对 / 计入题次", "正确率"],
            summary.groups.map(group => [group.label, `${group.correct}/${group.total}`, `${(group.correct / group.total * 100).toFixed(1)}%`])));
          const questions = node("details"); questions.append(node("summary", "逐题错答与漏答"), table(["题号", "题目", "答对", "答错", "漏答", "计入题次", "错答率"],
            summary.questions.map(q => [q.id, q.title, q.correct, q.wrong, q.unanswered, q.total, `${(q.wrong / q.total * 100).toFixed(1)}%`])));
          card.append(groups, questions); content.append(card);
        });
        const identityHeadings = admin ? ["输入账号", "姓名", "归属", "身份来源", "IP", "计算机名（自报）"] : ["账号"];
        content.append(table([...identityHeadings, "题库", "时间", "正确 / 题数", "正确率", "错答", "漏答", "版本", "记录"], result.records.map(row => {
          const download = node("a", "下载 JSON"); download.href = "/api/attempts/" + row.attempt_id;
          download.download = `quiz-${row.attempt_id}.json`;
          const identity = admin ? [row.input_account || row.username, row.display_name, attributionName(row.identity_status), sourceName(row.identity_source),
            row.client_ip || "—", row.computer_name || "—"] : [row.input_account || row.username];
          return [...identity, paperName(row.paper),
            new Date(row.time).toLocaleString(), `${row.correct}/${row.total}`, row.percent === null ? "—" : `${row.percent}%`,
            row.wrong, row.unanswered, row.version.slice(0, 12), admin && row.username !== team.user().username ? "个人记录由本人下载" : download];
        })));
      } catch (exception) { error.textContent = exception.message; }
      finally { if (serial === requestNumber) submit.disabled = false; }
    }
    filters.addEventListener("submit", event => { event.preventDefault(); load(); });
    await load();
    if (!admin) {
      const history = await team.request("/api/history");
      const section = node("section"); section.append(node("h2", "全部考试记录（含历史草稿）"));
      section.append(table(["题库", "时间", "状态", "已答", "版本", "记录"], history.attempts.map(row => {
        const link = node("a", "下载 JSON"); link.href = "/api/attempts/" + row.attempt_id; link.download = `quiz-${row.attempt_id}.json`;
        return [paperName(row.paper), new Date(row.time).toLocaleString(), row.submitted ? "已交卷" : "草稿", row.answered, row.version.slice(0, 12), link];
      })));
      shell.append(section);
    }
    if (admin) {
      const section = node("section"); section.append(node("h2", "名单与独立记录"), node("p", "已归属名单、未归属账号和原密码账号分别列出。手填账号与计算机名属于自报信息，IP 仅作辅助。"));
      const form = node("form", undefined, "team-account-form");
      const nameLabel = node("label", "账号"), displayLabel = node("label", "显示姓名");
      const name = node("input"), display = node("input"); name.required = display.required = true;
      name.maxLength = 64; display.maxLength = 80;
      nameLabel.append(name); displayLabel.append(display);
      const create = node("button", "创建学习者账号", "button primary"); create.type = "submit";
      const message = node("p"); message.setAttribute("role", "status");
      const users = node("div");
      async function refreshUsers() {
        const result = await team.request("/api/admin/users");
        users.replaceChildren();
        for (const kind of ["matched", "unmatched", "legacy"]) {
          const list = result.users.filter(u => (u.attribution || "legacy") === kind);
          const block = node("section"); block.append(node("h3", `${attributionName(kind)} · ${list.length} 人 / 账号`));
          block.append(table(["姓名 / 显示名", "输入账号", "最近身份来源", "最近 IP", "计算机名（自报）", "角色", "状态"], list.map(u => {
            const identity = u.last_identity;
            return [u.display_name, identity?.account || (kind === "matched" ? "尚未登录" : u.username),
              identity ? sourceName(identity.source) : "—", identity?.client_ip || "—", identity?.computer_name || "—",
              u.role === "admin" ? "管理员" : "学习者", u.disabled ? "已停用" : "启用"];
          })));
          users.append(block);
        }
      }
      form.append(nameLabel, displayLabel, create, message);
      form.addEventListener("submit", async event => {
        event.preventDefault(); create.disabled = true;
        try {
          const result = await team.request("/api/admin/users", { username: name.value, display_name: display.value });
          message.className = "team-credentials";
          message.textContent = `账号：${result.user.username}\n初始密码：${result.initial_password}\n请单独交给本人，不要提交到仓库。离开或刷新后此处不再显示。`;
          name.value = display.value = ""; await refreshUsers();
        } catch (exception) { message.textContent = exception.message; }
        finally { create.disabled = false; }
      });
      section.append(users);
      if (team.rosterOnly()) section.append(node("p", "仅名单中的学员可以登录。增减名单请维护 data/quiz-team-roster.json 并重启服务，历史记录继续保留。"));
      else section.append(node("h3", "分配原模式的密码账号"), form);
      shell.append(section); await refreshUsers();
    }
  } catch (error) { app.replaceChildren(node("p", error.message, "error-text")); }
})();
