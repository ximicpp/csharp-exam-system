"""Render, verify, or take the choice-question bank; run from the repository root."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import locale
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from textwrap import dedent
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "exercises/quiz"
DOCS = ROOT / "docs/quiz"
GROUPS = {"types": "类型与建模", "execution": "资源与执行", "runtime": "运行时与性能",
          "foundations": "语法与数据", "modeling": "对象模型与 API", "queries": "查询与元数据"}
# These groups describe the full topic bank, not the selected extension paper.
COMBINED_GROUPS = tuple(GROUPS)
GROUPS["microsoft"] = "Microsoft Learn 配套自测"
# Stable, consecutive ranges; adding a paper requires updating this manifest.
GROUP_RANGES = {group: range(index * 20 + 1, index * 20 + 21)
                for index, group in enumerate(COMBINED_GROUPS)}
GROUP_RANGES["microsoft"] = range(121, 241)
QUESTION_ID = r"Q(?:0[1-9]|[1-9]\d{1,2})"
LETTERS = set("ABCD")
KINDS = {"single": "单选"}
TIERS = {"core": "核心", "deep": "深入"}
EVIDENCE = {"runtime": "运行断言", "compile-error": "编译诊断", "documentation": "官方契约"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def local_path(relative: str) -> Path:
    require(isinstance(relative, str) and bool(relative), "Missing local path")
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), f"Invalid local path: {relative}")
    return path


def excerpt(block: dict) -> str:
    require(set(block) == {"path", "region"}, f"Invalid code reference: {block}")
    path = local_path(block["path"])
    region = block["region"]
    require(isinstance(region, str) and bool(region), "Empty region")
    source = path.read_text(encoding="utf-8-sig")
    starts = list(re.finditer(r"^[ \t]*#region " + re.escape(region) + r"[ \t]*$",
                             source, re.MULTILINE))
    require(len(starts) == 1, f"{path.name}: expected one region {region}")
    tail = source[starts[0].end():].lstrip("\n")
    end = re.search(r"^[ \t]*#endregion\b[^\n]*$", tail, re.MULTILINE)
    require(end is not None, f"{path.name}: unterminated region {region}")
    code = dedent(tail[:end.start()]).strip("\n")
    require(bool(code) and "#region" not in code, f"Empty/nested region: {region}")
    require("QuizAssert." not in code, f"{region}: assertion leaks the answer into the question")
    return code


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_question(q: dict) -> None:
    fields = {"id", "title", "kind", "tier", "topics", "scenario", "prompt", "code", "options",
              "answers", "rationale", "explanation", "takeaway", "learn", "sources", "verification"}
    require(isinstance(q, dict) and set(q) == fields, "Unexpected/missing question fields")
    qid = q["id"]
    require(isinstance(qid, str) and re.fullmatch(QUESTION_ID, qid) is not None, "Invalid question id")
    for key in ("title", "prompt", "takeaway"):
        require(nonempty(q[key]), f"{qid}: empty {key}")
    require(isinstance(q["scenario"], str)
            and (q["scenario"] == "" or nonempty(q["scenario"])), f"{qid}: invalid scenario")
    require(q["kind"] in KINDS and q["tier"] in TIERS, f"{qid}: invalid kind/tier")
    for key in ("options", "rationale"):
        require(isinstance(q[key], dict) and set(q[key]) == LETTERS
                and all(nonempty(v) for v in q[key].values()), f"{qid}: incomplete {key}")
    require(len(set(q["options"].values())) == 4, f"{qid}: duplicate options")
    explanation = q["explanation"]
    require(isinstance(explanation, dict) and set(explanation) == {"principle", "steps", "boundary"}
            and nonempty(explanation["principle"]) and nonempty(explanation["boundary"]),
            f"{qid}: missing explanation rule/boundary")
    steps = explanation["steps"]
    require(isinstance(steps, list) and len(steps) >= 2 and all(nonempty(step) for step in steps)
            and len(set(steps)) == len(steps), f"{qid}: explanation needs distinct reasoning steps")
    answers = q["answers"]
    require(isinstance(answers, list) and all(isinstance(a, str) for a in answers)
            and len(set(answers)) == len(answers) and set(answers) <= LETTERS,
            f"{qid}: invalid answer set")
    require(len(answers) == 1, f"{qid}: answer count must be exactly one")
    for key in ("topics", "learn"):
        require(isinstance(q[key], list) and q[key] and all(nonempty(v) for v in q[key])
                and len(set(q[key])) == len(q[key]), f"{qid}: invalid {key}")
    for path in q["learn"]:
        local_path(path)
    require(isinstance(q["sources"], list) and bool(q["sources"]), f"{qid}: missing sources")
    for source in q["sources"]:
        require(isinstance(source, dict) and set(source) == {"title", "url"}
                and nonempty(source["title"]) and nonempty(source["url"]), f"{qid}: invalid source")
        url = urlparse(source["url"])
        require(url.scheme == "https" and bool(url.netloc), f"{qid}: invalid source URL")
    require(isinstance(q["code"], list), f"{qid}: invalid code list")
    for block in q["code"]:
        excerpt(block)
    v = q["verification"]
    require(isinstance(v, dict) and v.get("kind") in EVIDENCE and nonempty(v.get("note")),
            f"{qid}: missing evidence scope")
    if v["kind"] == "runtime":
        require(set(v) == {"kind", "checks", "note"} and v["checks"] == [qid],
                f"{qid}: runtime check must identify this question")
        require(all(b["path"].startswith("tests/Quiz.Checks/") for b in q["code"]),
                f"{qid}: runtime excerpt is not in the compiled project")
    elif v["kind"] == "compile-error":
        require(set(v) == {"kind", "path", "diagnostics", "note"}, f"{qid}: invalid compile evidence")
        require(v["path"] == f"exercises/quiz/compile/{qid}.cs", f"{qid}: invalid compile path")
        local_path(v["path"])
        require(isinstance(v["diagnostics"], list) and v["diagnostics"]
                and all(isinstance(d, str) and re.fullmatch(r"CS\d{4}", d) for d in v["diagnostics"]),
                f"{qid}: missing expected compiler diagnostics")
        require(any(b["path"] == v["path"] for b in q["code"]), f"{qid}: missing failing source excerpt")
    else:
        require(set(v) == {"kind", "note"}, f"{qid}: invalid documentation evidence")


def load_bank() -> dict[str, list[dict]]:
    groups = {}
    for group in GROUPS:
        questions = json.loads((BANK / f"{group}.json").read_text(encoding="utf-8-sig"),
                               object_pairs_hook=unique_object)
        require(isinstance(questions, list), f"{group}: expected question array")
        for q in questions:
            validate_question(q)
        require([q["id"] for q in questions] == [f"Q{i:02}" for i in GROUP_RANGES[group]],
                f"{group}: expected {len(GROUP_RANGES[group])} unique, ordered IDs")
        groups[group] = questions
    return groups


def load_migration_exam(groups: dict[str, list[dict]]) -> dict:
    manifest = json.loads((BANK / "migration-exam.json").read_text(encoding="utf-8-sig"),
                          object_pairs_hook=unique_object)
    require(isinstance(manifest, dict) and set(manifest) == {"title", "intro", "groups"}
            and nonempty(manifest["title"]) and nonempty(manifest["intro"]),
            "Invalid migration exam heading")
    require(isinstance(manifest["groups"], list) and bool(manifest["groups"]),
            "Missing migration exam groups")
    seen_groups, seen_ids = set(), set()
    for section in manifest["groups"]:
        require(isinstance(section, dict) and set(section) == {"id", "focus", "questions"},
                "Invalid migration exam group")
        group = section["id"]
        require(isinstance(group, str) and group in COMBINED_GROUPS and group in groups
                and group not in seen_groups and nonempty(section["focus"]),
                "Invalid/duplicate migration exam group")
        seen_groups.add(group)
        ids = section["questions"]
        allowed = {q["id"] for q in groups[group]}
        require(isinstance(ids, list) and bool(ids)
                and all(isinstance(qid, str) and qid in allowed and qid not in seen_ids for qid in ids)
                and len(set(ids)) == len(ids), "Invalid/duplicate migration exam question")
        seen_ids.update(ids)
    require(len(seen_ids) == 40, "Migration exam must select exactly 40 questions")
    return manifest


def migration_questions(groups: dict[str, list[dict]], manifest: dict) -> dict[str, list[dict]]:
    selected = {}
    for section in manifest["groups"]:
        by_id = {q["id"]: q for q in groups[section["id"]]}
        selected[section["id"]] = [by_id[qid] for qid in section["questions"]]
    return selected


def validate_lesson(lesson: dict, group: str, questions: list[dict]) -> None:
    require(isinstance(lesson, dict) and set(lesson) == {"group", "title", "intro", "sections"},
            f"{group}: invalid lesson fields")
    require(lesson["group"] == group and nonempty(lesson["title"]) and nonempty(lesson["intro"]),
            f"{group}: invalid lesson heading")
    require(isinstance(lesson["sections"], list) and bool(lesson["sections"]),
            f"{group}: missing lesson sections")
    if group == "microsoft":
        require(len(lesson["sections"]) == 12, "microsoft: expected twelve learning units")
        for index, section in enumerate(lesson["sections"]):
            require(isinstance(section, dict) and section.get("questions") ==
                    [f"Q{i}" for i in range(121 + index * 10, 131 + index * 10)],
                    "microsoft: unit must match its ten ordered questions")
    by_id = {q["id"]: q for q in questions}
    covered = []
    for section in lesson["sections"]:
        require(isinstance(section, dict) and set(section) ==
                {"title", "questions", "code", "result", "explanation", "takeaway"},
                f"{group}: invalid lesson section")
        require(all(nonempty(section[key]) for key in ("title", "result", "takeaway")),
                f"{group}: empty lesson text")
        ids = section["questions"]
        require(isinstance(ids, list) and bool(ids)
                and all(isinstance(qid, str) and qid in by_id for qid in ids),
                f"{group}: invalid lesson question references")
        covered.extend(ids)
        require(isinstance(section["explanation"], list) and bool(section["explanation"])
                and all(nonempty(p) for p in section["explanation"]), f"{group}: missing explanation")
        require(isinstance(section["code"], list), f"{group}: invalid lesson code")
        allowed = [block for qid in ids for block in by_id[qid]["code"]]
        for block in section["code"]:
            require(block in allowed, f"{group}: lesson code must reference an associated question")
            excerpt(block)
    require(sorted(covered) == sorted(by_id), f"{group}: lesson must cover every question exactly once")


def load_lessons(groups: dict[str, list[dict]], lesson_dir: Path | None = None) -> dict[str, dict]:
    lesson_dir = BANK / "lessons" if lesson_dir is None else lesson_dir
    lessons = {}
    for group, questions in groups.items():
        lesson = json.loads((lesson_dir / f"{group}.json").read_text(encoding="utf-8-sig"),
                            object_pairs_hook=unique_object)
        validate_lesson(lesson, group, questions)
        lessons[group] = lesson
    return lessons


def resolved_lessons(groups: dict[str, list[dict]], lesson_dir: Path | None = None) -> dict[str, dict]:
    lessons = load_lessons(groups, lesson_dir)
    for group, lesson in lessons.items():
        questions = {q["id"]: q for q in groups[group]}
        for section in lesson["sections"]:
            section["code_sources"] = [block["path"] for block in section["code"]]
            section["code"] = [excerpt(block) for block in section["code"]]
            sources = {}
            for qid in section["questions"]:
                for source in questions[qid]["sources"]:
                    sources.setdefault(source["url"], source)
            section["sources"] = list(sources.values())
    return lessons


def migration_numbering(selected: dict[str, list[dict]]) -> dict[str, str]:
    """Number the selected paper without changing stable source/evidence IDs."""
    return {q["id"]: f"Q{index:02}" for index, q in enumerate(
        (q for questions in selected.values() for q in questions), 1)}


def lesson_lines(lesson: dict, level: int = 2, local_links: bool = False,
                 display_ids: dict[str, str] | None = None) -> list[str]:
    lines = [f"{'#' * level} {lesson['title']}", "", lesson["intro"], ""]
    for section in lesson["sections"]:
        ids = []
        for qid in section["questions"]:
            label = (display_ids or {}).get(qid, qid)
            page = "question-bank.md" if display_ids else f"{lesson['group']}-answers.md"
            ids.append(f"[{label}]({page}#{qid.lower()})" if local_links else label)
        ids = " · ".join(ids)
        lines += [f"{'#' * (level + 1)} {section['title']}", "", f"相关题目：{ids}", ""]
        for index, code in enumerate(section["code"]):
            fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", code)), default=3))
            if local_links:
                lines.append(f"<!-- source: {section['code_sources'][index]} -->")
            lines += [fence + "csharp", code, fence, ""]
        lines += [f"**观察与边界：** {section['result']}", ""]
        for paragraph in section["explanation"]:
            lines += [paragraph, ""]
        lines += [f"**工程判断：** {section['takeaway']}", "",
                  "**官方依据：** " + " · ".join(f"[{s['title']}]({s['url']})" for s in section["sources"]), ""]
    return lines


def label(q: dict) -> str:
    return f"{KINDS[q['kind']]} · {TIERS[q['tier']]} · {' / '.join(q['topics'])}"


def relative_link(path: str) -> str:
    return "../../" + path


def explanation_lines(explanation: dict) -> list[str]:
    return ["**知识点规则**", "", explanation["principle"], "", "**本题推导**", "",
            *[f"{index}. {step}" for index, step in enumerate(explanation["steps"], 1)], "",
            f"**适用边界：** {explanation['boundary']}", ""]


def render_questions(group: str, questions: list[dict]) -> str:
    lines = [f"# {GROUPS[group]} · 选择题", "", "<!-- Generated by scripts/quiz.py; edit exercises/quiz/*.json and C# regions. -->", "",
             f"[题库入口](index.md) · [本组解析]({group}-answers.md)", "",
             "基线为 .NET 10 / C# 14，启用 nullable 与隐式 using；警告视为错误。每题只有一个正确选项。",
             "代码块是同一题的类型定义与调用片段；题面指定调用的方法由验证程序执行。编译诊断题会单独标注。", ""]
    for q in questions:
        lines += [f"<a id=\"{q['id'].lower()}\"></a>", "", f"## {q['id']} · {q['title']}", "", label(q), ""]
        lines += question_lines(q)
        lines += ["", f"[查看解析]({group}-answers.md#{q['id'].lower()})", ""]
    return "\n".join(lines)


def question_lines(q: dict) -> list[str]:
    lines = [q["scenario"], ""] if q["scenario"] else []
    lines += [q["prompt"], ""]
    if q["verification"]["kind"] == "compile-error":
        lines += ["**编译判断题：以下源码是故意保留的负向样例，不加入正常项目构建。**", ""]
    for block in q["code"]:
        lines += [f"<!-- source: {block['path']} -->", "```csharp", excerpt(block), "```", ""]
    lines += [f"- {letter}. {q['options'][letter]}" for letter in "ABCD"]
    return lines


def answer_lines(q: dict) -> list[str]:
    qid = q["id"]
    v = q["verification"]
    lines = [f"**答案：{'、'.join(sorted(q['answers']))}**（{KINDS[q['kind']]}）", ""]
    lines += explanation_lines(q["explanation"])
    lines += ["**逐项辨析**", ""]
    lines += [f"- **{letter} {'正确' if letter in q['answers'] else '错误'}**：{q['rationale'][letter]}" for letter in "ABCD"]
    lines += ["", f"**学习方向：** {q['takeaway']}", "", f"**验证：{EVIDENCE[v['kind']]}。** {v['note']}", ""]
    if v["kind"] == "runtime":
        lines += ["```sh", f"dotnet run --project tests/Quiz.Checks -c Release -- {qid}", "```", "",
                  f"验收：输出 `PASS: {qid}`，退出码 0。", ""]
    elif v["kind"] == "compile-error":
        lines += ["```sh", f"python scripts/quiz.py check --id {qid}", "```", "",
                  f"验收：捕获预期诊断 `{'、'.join(v['diagnostics'])}` 后检查器退出码 0；被测编译本身须失败。", ""]
    lines += ["**继续阅读：** " + " · ".join(f"[{Path(p).stem}]({relative_link(p)})" for p in q["learn"]), "",
              "**官方依据：** " + " · ".join(f"[{s['title']}]({s['url']})" for s in q["sources"]), ""]
    return lines


def render_answers(group: str, questions: list[dict]) -> str:
    lines = [f"# {GROUPS[group]} · 答案与学习方向", "", "<!-- Generated by scripts/quiz.py; edit exercises/quiz/*.json and C# regions. -->", "",
             f"[题库入口](index.md) · [返回题面]({group}.md) · [本套讲解]({group}-lesson.md)", "",
             "运行或编译证据只覆盖说明中的可观测结论；库契约和运行时策略还须核对官方来源。", ""]
    for q in questions:
        qid = q["id"]
        lines += [f"<a id=\"{qid.lower()}\"></a>", "", f"## {qid} · {q['title']}", ""]
        lines += answer_lines(q)
        lines += [f"[返回题面]({group}.md#{qid.lower()})", ""]
    return "\n".join(lines)


def render_coverage(groups: dict[str, list[dict]]) -> str:
    questions = [q for qs in groups.values() for q in qs]
    tiers = Counter(q["tier"] for q in questions)
    evidence = Counter(q["verification"]["kind"] for q in questions)
    lines = ["# 选择题覆盖索引", "", "<!-- Generated by scripts/quiz.py; edit exercises/quiz/*.json and C# regions. -->", "",
             "[题库入口](index.md)", "",
             f"共 {len(questions)} 题，全部为单选；"
             f"{tiers['core']} 道核心、{tiers['deep']} 道深入。", "",
             f"证据分为 {evidence['runtime']} 道运行断言、{evidence['compile-error']} 道编译诊断、"
             f"{evidence['documentation']} 道官方契约核对。数量描述覆盖方式，不代表能力评分或学习完成度。", ""]
    for group, qs in groups.items():
        lines += [f"## {GROUPS[group]}", "", "| 题号 | 决策主题 | 层次 | 题型 | 证据 |", "| --- | --- | --- | --- | --- |"]
        for q in qs:
            title = q["title"].replace("|", "\\|")
            lines += [f"| [{q['id']}]({group}.md#{q['id'].lower()}) | {title} | {TIERS[q['tier']]} | {KINDS[q['kind']]} | {EVIDENCE[q['verification']['kind']]} |"]
        lines += [""]
    return "\n".join(lines)


def load_curriculum(groups: dict[str, list[dict]], filename: str = "curriculum.json") -> list[dict]:
    if filename == "curriculum.json":
        groups = {group: questions for group, questions in groups.items() if group in COMBINED_GROUPS}
    topics = json.loads((BANK / filename).read_text(encoding="utf-8-sig"),
                        object_pairs_hook=unique_object)
    require(isinstance(topics, list) and bool(topics), "Missing knowledge map")
    ids = {q["id"] for questions in groups.values() for q in questions}
    covered = []
    for topic in topics:
        require(isinstance(topic, dict) and set(topic) == {"title", "questions", "summary", "learn"}
                and nonempty(topic["title"]), "Invalid knowledge topic")
        for key in ("questions", "summary", "learn"):
            require(isinstance(topic[key], list) and bool(topic[key])
                    and all(nonempty(value) for value in topic[key]), f"Knowledge topic: invalid {key}")
        require(set(topic["questions"]) <= ids, "Knowledge topic references unknown question")
        covered.extend(topic["questions"])
        for path in topic["learn"]:
            local_path(path)
    require(sorted(covered) == sorted(ids), "Knowledge map must cover every question exactly once")
    return topics


def render_curriculum(groups: dict[str, list[dict]]) -> str:
    groups = {group: questions for group, questions in groups.items() if group in COMBINED_GROUPS}
    topics = load_curriculum(groups)
    by_id = {q["id"]: (group, q) for group, questions in groups.items() for q in questions}
    lines = ["# C# 知识主干与题目映射", "",
             "<!-- Generated by scripts/quiz.py; edit exercises/quiz/curriculum.json. -->", "",
             "[题库入口](index.md) · [逐题证据](coverage.md)", "",
             "按 [Microsoft Learn C# 文档](https://learn.microsoft.com/zh-cn/dotnet/csharp/)"
             "的基础、概念、高级主题与语言参考归纳；核对日期：2026-10-01。"
             "基线为 .NET 10 / C# 14，排除预览特性。", "",
             f"共 {len(topics)} 个知识主题，对应 {len(by_id)} 道单选；题号各映射一次，"
             "相近机制可结合各套讲解交叉学习。题目检验具体边界，不能替代整个主题的练习。", "",
             "范围是通用 C# 语言与工程机制。ASP.NET、桌面／移动 UI、游戏、云服务、"
             "每个类库 API、完整 Roslyn 开发和所有本机 ABI 不在本轮题库范围。"
             "XML 文档、预处理指令、unsafe 指针、文件应用和工具配置只作延伸阅读，"
             "没有独立专项题；这份映射不声称逐页读完官方全站。", ""]
    for index, topic in enumerate(topics, 1):
        lines += [f"## {index:02} · {topic['title']}", ""]
        lines += [paragraph + "\n" for paragraph in topic["summary"]]
        links = [f"[{qid}]({by_id[qid][0]}.md#{qid.lower()})" for qid in topic["questions"]]
        lines += ["**对应题目：** " + " · ".join(links), "",
                  "**课程阅读：** " + " · ".join(f"[{Path(p).stem}]({relative_link(p)})" for p in topic["learn"]), ""]
        # Individual answer pages retain the full official evidence for every claim.
        sources = {}
        for qid in topic["questions"]:
            for source in by_id[qid][1]["sources"]:
                sources.setdefault(source["url"], source)
        lines += ["**官方入口：** " + " · ".join(f"[{s['title']}]({s['url']})" for s in list(sources.values())[:3]), "",
                  "其余具体规则的来源与验证范围见对应题目的解析。", ""]
    lines += ["## 延伸阅读", "",
              "- [程序结构与文件应用](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/program-structure/)",
              "- [语言参考：语法、预处理与文档注释](https://learn.microsoft.com/zh-cn/dotnet/csharp/language-reference/)",
              "- [unsafe 代码与指针](https://learn.microsoft.com/zh-cn/dotnet/csharp/language-reference/unsafe-code)",
              "- [Roslyn SDK](https://learn.microsoft.com/zh-cn/dotnet/csharp/roslyn-sdk/)", ""]
    return "\n".join(lines)


def render_microsoft_curriculum(groups: dict[str, list[dict]]) -> str:
    topics = load_curriculum({"microsoft": groups["microsoft"]}, "microsoft.curriculum.json")
    questions = {q["id"]: q for q in groups["microsoft"]}
    lesson = load_lessons({"microsoft": groups["microsoft"]})["microsoft"]
    lines = ["# Microsoft Learn C# 配套学习与覆盖表", "",
             "<!-- Generated by scripts/quiz.py; edit exercises/quiz/microsoft.curriculum.json and lessons/microsoft.json. -->", "",
             "[题库入口](index.md) · [独立题面](microsoft.md) · [逐题解析](microsoft-answers.md) · [交卷后讲解](microsoft-lesson.md)", "",
             "依据 [Microsoft C# 文档](https://learn.microsoft.com/zh-cn/dotnet/csharp/)的入门、基础、"
             "编程概念、高级主题与语言参考编写。核对日期：2026-10-01；.NET 10 / C# 14。"
             "这是本课程自编配套题，不是 Microsoft 官方试题或认证模拟卷。", "",
             f"独立 120 道四选一，12 个学习单元、{len(topics)} 个知识主题，Q121–Q240 各归属一次。"
             "先沿表中的官方文章学习，再参加包含基础 120 题与扩展 40 题的合并考试，交卷后结合章节成绩和讲解复习。", "",
             "范围覆盖通用 C# 语言主干及常用工程边界。ASP.NET、EF Core、桌面、移动、游戏与云平台"
             "教程另属专项；不是对 Microsoft 全站每页、每个 API 或所有语言参考条目的穷举。"
             "完整 unsafe/ABI、完整 Roslyn 开发、所有编译器选项和性能诊断工具只覆盖通用边界。"
             "每个主题有题目不等于已穷尽该主题，也不代表学习者掌握。", "",
             "## 12 个学习单元", "", "| 单元 | 题号 | 重点 |", "| --- | --- | --- |"]
    for index, section in enumerate(lesson["sections"], 1):
        ids = section["questions"]
        lines.append(f"| {index:02} | {ids[0]}–{ids[-1]} | {section['title']} |")
    lines += ["", "## 官方文章与知识点对照", ""]
    for index, topic in enumerate(topics, 1):
        lines += [f"### {index:02} · {topic['title']}", "",
                  "**对应题目：** " + " · ".join(f"[{qid}](microsoft.md#{qid.lower()})" for qid in topic["questions"]), ""]
        lines += [paragraph + "\n" for paragraph in topic["summary"]]
        sources = {source["url"]: source for qid in topic["questions"] for source in questions[qid]["sources"]}
        lines += ["**配套官方阅读：** " + " · ".join(f"[{s['title']}]({s['url']})" for s in sources.values()), ""]
    return "\n".join(lines)


def render_migration_exam(groups: dict[str, list[dict]]) -> str:
    manifest = load_migration_exam(groups)
    selected = migration_questions(groups, manifest)
    numbering = migration_numbering(selected)
    # Validate the tailored teaching alongside the selected question list.
    load_lessons(selected, BANK / "lessons/migration")
    lines = [f"# {manifest['title']} · 40 题", "",
             "<!-- Generated by scripts/quiz.py; edit exercises/quiz/migration-exam.json and lessons/migration/*.json. -->", "",
             "[题库入口](index.md) · [扩展卷讲解](migration-lesson.md) · [Microsoft Learn 基础配套卷](microsoft-map.md) · [考试与练习](exam.md)", "",
             manifest["intro"], "",
             "类型与建模、运行时与性能、对象模型与 API 合计 32 题，占 80%；资源与执行补充 8 题。"
             "基础语法、普通集合操作及基础元数据留给 Microsoft Learn 配套卷。", "",
             "网页将基础 120 题与本扩展部分 40 题合为一套 160 题考试，章节名带基础 / 扩展前缀。本文按扩展部分顺序编号 Q01–Q40；"
             "原题号仅用于源码验证、旧记录与归档对照，不改变答案或已有作答版本。"
             "合并考试每题 1 分，原始满分 160 分，另显示百分制；交卷后显示全部解析，历史独立卷的原分数保留。", "",
             "| 分组 | 题数 | 工程判断 |", "| --- | --- | --- |"]
    for section in manifest["groups"]:
        lines.append(f"| {GROUPS[section['id']]} | {len(section['questions'])} | {section['focus']} |")
    for section in manifest["groups"]:
        group = section["id"]
        lines += ["", f"## {GROUPS[group]}", "", "| 扩展卷题号 | 题库原号 | 题目与完整解析 |",
                  "| --- | --- | --- |"]
        for q in selected[group]:
            anchor = q["id"].lower()
            title = q["title"].replace("|", "\\|")
            lines.append(f"| {numbering[q['id']]} | {q['id']} | [{title}](question-bank.md#{anchor}) |")
    return "\n".join(lines) + "\n"


def render_question_bank(groups: dict[str, list[dict]]) -> str:
    manifest = load_migration_exam(groups)
    selected = migration_questions(groups, manifest)
    numbering = migration_numbering(selected)
    lines = ["# C# 完整单选题库归档", "",
             "<!-- Generated by scripts/quiz.py; edit exercises/quiz/*.json and C# regions. -->", "",
             "[题库入口](index.md) · [考试与练习](exam.md) · [扩展卷讲解](migration-lesson.md) · [Microsoft Learn 配套讲解](microsoft-lesson.md)", "",
             "收录全部 240 道单选及完整解析，每题只归档一次：扩展卷 40 题、Microsoft Learn 配套卷 120 题、未入选的迁移题 80 题。"
             "网页将前两部分合为一套 160 题考试，按基础、扩展顺序排列。基线为 .NET 10 / C# 14，启用 nullable 与隐式 using，警告视为错误。", "",
             "扩展卷的作答编号连续为 Q01–Q40，题库原号用于源码验证与历史记录；两者对照见下表。"
             "Microsoft Learn 配套卷保留 Q121–Q240。归档中的锚点与验证命令均使用题库原号。", "",
             "运行或编译证据只覆盖给定源码与输入；官方契约题有人工核对记录，不能将其算作运行验证。", "",
             "## 扩展卷编号对照", "", "| 扩展卷题号 | 题库原号 | 分组 | 题目 |", "| --- | --- | --- | --- |"]
    for group, questions in selected.items():
        for q in questions:
            title = q["title"].replace("|", "\\|")
            lines.append(f"| {numbering[q['id']]} | {q['id']} | {GROUPS[group]} | [{title}](#{q['id'].lower()}) |")

    def append_questions(questions: list[dict], display_ids: dict[str, str], archived: bool = False) -> None:
        for q in questions:
            title_id = f"原 {q['id']}" if archived else display_ids.get(q["id"], q["id"])
            lines.extend([f"<a id=\"{q['id'].lower()}\"></a>", "", f"#### {title_id} · {q['title']}", "",
                          f"题库原号：{q['id']} · {label(q)}", ""])
            lines.extend(question_lines(q))
            lines.extend(["", *answer_lines(q)])

    lines += ["", "## 迁移工程扩展卷 · 40 题", "", manifest["intro"], ""]
    for section in manifest["groups"]:
        lines += [f"### {GROUPS[section['id']]} · {len(section['questions'])} 题", "", section["focus"], ""]
        append_questions(selected[section["id"]], numbering)
    lines += ["## Microsoft Learn 配套卷 · 120 题", "",
              "自编配套题，按官方学习资料组织；不属于 Microsoft 官方试题。覆盖范围见[知识映射](microsoft-map.md)。", ""]
    companion = {q["id"]: q for q in groups["microsoft"]}
    for section in load_lessons({"microsoft": groups["microsoft"]})["microsoft"]["sections"]:
        lines += [f"### {section['title']}", ""]
        append_questions([companion[qid] for qid in section["questions"]], {})
    lines += ["## 未入选的迁移题 · 80 题", "", "保留完整题面、答案与依据供查阅，不在页面提供独立试卷。", ""]
    for group in COMBINED_GROUPS:
        remaining = [q for q in groups[group] if q["id"] not in numbering]
        lines += [f"### {GROUPS[group]} · {len(remaining)} 题", ""]
        append_questions(remaining, {}, archived=True)
    return "\n".join(lines)


def generated_files(groups: dict[str, list[dict]]) -> dict[Path, str]:
    files = {DOCS / "coverage.md": render_coverage(groups),
             DOCS / "knowledge-map.md": render_curriculum(groups),
             DOCS / "microsoft-map.md": render_microsoft_curriculum(groups),
             DOCS / "migration-exam.md": render_migration_exam(groups),
             DOCS / "question-bank.md": render_question_bank(groups)}
    manifest = load_migration_exam(groups)
    selected = migration_questions(groups, manifest)
    extension_lessons = resolved_lessons(selected, BANK / "lessons/migration")
    files[DOCS / "migration-lesson.md"] = "\n".join([
        f"# {manifest['title']} · 讲解", "",
        "<!-- Generated by scripts/quiz.py; edit exercises/quiz/lessons/migration/*.json and C# regions. -->", "",
        "[选题与分配](migration-exam.md) · [题库入口](index.md)", "", manifest["intro"], "",
        *[line for lesson in extension_lessons.values()
          for line in lesson_lines(lesson, local_links=True, display_ids=migration_numbering(selected))]])
    lessons = resolved_lessons(groups)
    for group, questions in groups.items():
        files[DOCS / f"{group}.md"] = render_questions(group, questions)
        files[DOCS / f"{group}-answers.md"] = render_answers(group, questions)
        files[DOCS / f"{group}-lesson.md"] = "\n".join([
            "<!-- Generated by scripts/quiz.py; edit exercises/quiz/lessons/*.json and C# regions. -->", "",
            f"[题库入口](index.md) · [逐题解析]({group}-answers.md)", "",
            *lesson_lines(lessons[group], level=1, local_links=True)])
    return files


def command(*args: str, success: bool = True) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, encoding=locale.getpreferredencoding(False),
                            errors="replace", capture_output=True, timeout=180)
    output = result.stdout + result.stderr
    require((result.returncode == 0) == success,
            f"Unexpected exit {result.returncode}: {' '.join(args)}\n{output}")
    return output


def check_links() -> None:
    for path in DOCS.glob("*.md"):
        for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", path.read_text(encoding="utf-8")):
            if urlparse(link).scheme or link.startswith("#"):
                continue
            target, _, anchor = unquote(link).partition("#")
            destination = (path.parent / target).resolve()
            require(destination.is_file(), f"{path.name}: broken link {link}")
            if destination.parent == DOCS and re.fullmatch(QUESTION_ID.lower(), anchor):
                require(f'id="{anchor}"' in destination.read_text(encoding="utf-8"),
                        f"{path.name}: missing question anchor {link}")


def verify_compile_errors(questions: list[dict]) -> None:
    negative = [q for q in questions if q["verification"]["kind"] == "compile-error"]
    if not negative:
        return
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    # Constrain the temporary directory to this workspace before its automatic cleanup.
    with tempfile.TemporaryDirectory(prefix="quiz-compile-", dir=artifacts) as folder:
        work = Path(folder).resolve()
        require(work.is_relative_to(artifacts.resolve()), "Compile probe escaped artifacts")
        project = work / "Probe.csproj"
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                           '<OutputType>Exe</OutputType></PropertyGroup></Project>', encoding="utf-8")
        source = work / "Program.cs"
        source.write_text('System.Console.WriteLine("control");\n', encoding="utf-8")
        command("dotnet", "build", str(project), "-c", "Release", "--nologo")
        for q in negative:
            v = q["verification"]
            source.write_text(local_path(v["path"]).read_text(encoding="utf-8-sig"), encoding="utf-8")
            output = command("dotnet", "build", str(project), "-c", "Release", "--no-restore", "--nologo",
                             success=False)
            # Include infrastructure/restore failures and unclassified errors, not just CS codes.
            diagnostics = set(re.findall(r"\berror(?:\s+([A-Z]+\d+))?\s*:", output))
            require(diagnostics == set(v["diagnostics"]),
                    f"{q['id']}: expected {v['diagnostics']}, got {sorted(diagnostics)}\n{output}")
            print(f"PASS: {q['id']} expected compiler diagnostics {','.join(sorted(diagnostics))}", flush=True)


def check(groups: dict[str, list[dict]], no_build: bool, selected: str | None) -> None:
    for path, expected in generated_files(groups).items():
        require(path.is_file() and path.read_text(encoding="utf-8") == expected,
                f"Stale generated file: {path.relative_to(ROOT)}; run python scripts/quiz.py render")
    check_links()
    all_questions = [q for qs in groups.values() for q in qs]
    require(selected is None or any(q["id"] == selected for q in all_questions), f"Unknown question: {selected}")
    questions = [q for q in all_questions if selected is None or q["id"] == selected]
    print(f"PASS: {sum(map(len, groups.values()))} questions, {len(groups)} lessons, "
          "source excerpts, generated pages and local links", flush=True)
    if not no_build:
        print(command("dotnet", "build", "tests/Quiz.Checks", "-c", "Release", "--nologo"), end="")
    runner = ("dotnet", str(ROOT / "tests/Quiz.Checks/bin/Release/net10.0/Quiz.Checks.dll"))
    registered = command(*runner, "--list").splitlines()
    expected = [q["id"] for q in all_questions if q["verification"]["kind"] == "runtime"]
    require(registered == expected, f"Runtime check registration mismatch: {registered} != {expected}")
    runtime_ids = [q["id"] for q in questions if q["verification"]["kind"] == "runtime"]
    if runtime_ids:
        output = command(*runner, *runtime_ids)
        require(re.findall(r"^PASS: (" + QUESTION_ID + r")$", output, re.MULTILINE) == runtime_ids,
                "Runtime runner did not execute the requested checks")
        print(output, end="")
    verify_compile_errors(questions)
    docs = [q["id"] for q in questions if q["verification"]["kind"] == "documentation"]
    if docs:
        print(f"DOCUMENTATION: {','.join(docs)} (human-reviewed contracts; no automated semantic proof)")
    print("PASS: quiz verification", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("render", help="Generate question and answer Markdown from reviewed data")
    checker = sub.add_parser("check", help="Verify bank and execute runtime/compiler evidence")
    checker.add_argument("--no-build", action="store_true", help="Use an already built Release runner")
    checker.add_argument("--id", help="Run evidence for one question; still validate all metadata/pages")
    exam = sub.add_parser("exam", help="Take the single-choice exam in a local browser")
    exam.add_argument("--port", type=int, default=8765, help="Local port (default: 8765)")
    exam.add_argument("--no-browser", action="store_true", help="Print the URL without opening a browser")
    args = parser.parse_args()
    if args.action == "exam":
        if not 0 <= args.port <= 65535:
            parser.error("--port must be between 0 and 65535")
        from quiz_exam import serve
        serve(port=args.port, open_browser=not args.no_browser)
        return
    groups = load_bank()
    if args.action == "render":
        DOCS.mkdir(parents=True, exist_ok=True)
        for path, content in generated_files(groups).items():
            path.write_text(content, encoding="utf-8", newline="\n")
        print(f"PASS: rendered {sum(map(len, groups.values()))} questions, separate explanations, "
              f"{len(groups)} topic lessons, 40-question extension with 4 lessons, complete archive, and coverage index")
    else:
        check(groups, args.no_build, args.id)


if __name__ == "__main__":
    os.environ.setdefault("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
    os.environ.setdefault("DOTNET_CLI_UI_LANGUAGE", "en-US")
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
