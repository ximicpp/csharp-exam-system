"""Exam scoring, persistence, and localhost HTTP boundaries; never write learner reports."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import http.client
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz  # noqa: E402
import quiz_exam as exam  # noqa: E402


class ExamChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="quiz-exam-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.exam = exam.Exam(self.directory / "reports")

    def payload(self, answers=None):
        return {"version": self.exam.version, "attempt_id": str(uuid4()),
                "answers": {} if answers is None else answers, "elapsed_seconds": 135}

    def all_correct(self):
        return {q["id"]: q["answers"][0] for q in self.exam.questions}

    def legacy_manifest(self, bank):
        return {"title": "旧迁移综合卷", "intro": "历史报告回归",
                "groups": [{"id": g, "focus": "历史题库",
                            "questions": [q["id"] for q in qs]} for g, qs in bank.items()]}

    def assert_counts(self, report):
        self.assertEqual(report["total"], report["correct"] + report["wrong"] + report["unanswered"])
        self.assertEqual(report["score"], report["correct"])
        self.assertEqual(report["percent"], round(report["correct"] / report["total"] * 100, 1))
        for key in ("total", "correct", "wrong", "unanswered"):
            self.assertEqual(report[key], sum(group[key] for group in report["groups"]))
        for group in report["groups"]:
            self.assertEqual(group["total"], group["correct"] + group["wrong"] + group["unanswered"])
            self.assertEqual(group["percent"], round(group["correct"] / group["total"] * 100, 1))

    def test_extension_is_forty_selected_singles_with_no_private_fields(self):
        public = self.exam.public()
        self.assertEqual(public["total"], 40)
        self.assertEqual(public["groups"], [
            {"id": "types", "label": "类型与建模", "count": 10},
            {"id": "runtime", "label": "运行时与性能", "count": 14},
            {"id": "modeling", "label": "对象模型与 API", "count": 8},
            {"id": "execution", "label": "资源与执行", "count": 8},
        ])
        bank = quiz.load_bank()
        selected = quiz.migration_questions(bank, quiz.load_migration_exam(bank))
        singles = [q for questions in selected.values() for q in questions]
        self.assertEqual([q["id"] for q in public["questions"]], [q["id"] for q in singles])
        self.assertEqual(len(self.exam.question_ids), 40)
        self.assertNotIn("Q04", self.exam.question_ids)
        self.assertIn("Q98", self.exam.question_ids)
        self.assertEqual((public["bank_total"], public["combined_total"]), (240, 40))
        self.assertEqual([(p["id"], p["count"]) for p in public["papers"]], [("microsoft", 120), (None, 40)])
        self.assertEqual([q["display_id"] for q in public["questions"]], [f"Q{i:02}" for i in range(1, 41)])
        fields = set(exam.PUBLIC_FIELDS) | {"group", "group_label", "code", "compile_error", "display_id"}
        for actual, source in zip(public["questions"], singles, strict=True):
            self.assertEqual(set(actual), fields)
            self.assertEqual(actual["kind"], "single")
            self.assertEqual(actual["code"], [quiz.excerpt(block) for block in source["code"]])
            for code in actual["code"]:
                self.assertNotIn("QuizAssert.", code)
        public["questions"][0]["options"]["A"] = "changed"
        self.assertNotEqual(self.exam.public()["questions"][0]["options"]["A"], "changed")

    def test_version_is_stable_but_answers_and_source_change_it(self):
        self.assertEqual(self.exam.version, exam.Exam(self.directory).version)
        bank = quiz.load_bank()
        bank["types"][0]["answers"] = ["D"]
        with patch.object(quiz, "load_bank", return_value=bank):
            self.assertNotEqual(self.exam.version, exam.Exam(self.directory).version)
        original = quiz.excerpt
        with patch.object(quiz, "excerpt", side_effect=lambda block: original(block) + "\n// Changed source"):
            self.assertNotEqual(self.exam.version, exam.Exam(self.directory).version)

    def test_display_numbering_is_consistent_without_changing_submission_ids(self):
        report = self.exam.grade(self.payload({"Q38": self.all_correct()["Q38"]}))
        last = report["questions"][-1]
        self.assertEqual((last["id"], last["display_id"], last["status"]), ("Q38", "Q40", "correct"))
        self.assertIn(f"### Q40 · {last['title']}", report["markdown"])
        self.assertNotIn(f"### Q38 · {last['title']}", report["markdown"])
        self.assertIn("相关题目：Q40\n", report["markdown"])
        feedback = self.exam.practice({"version": self.exam.version, "question_id": "Q38", "answer": last["answer"]})
        self.assertEqual(feedback["question"]["display_id"], "Q40")
        # A saved report without display metadata keeps its original numbering.
        historical = deepcopy(report)
        for q in historical["questions"]:
            q.pop("display_id")
        self.assertIn(f"### Q38 · {last['title']}", exam.markdown_report(historical))
        self.assertNotIn(f"### Q40 · {last['title']}", exam.markdown_report(historical))

    def test_unselected_topic_changes_do_not_change_the_extension_or_companion(self):
        companion = exam.Exam(self.directory, "microsoft")
        full_types = exam.Exam(self.directory, "types")
        bank = quiz.load_bank()
        next(q for q in bank["types"] if q["id"] == "Q04")["prompt"] += " Changed wording"
        with patch.object(quiz, "load_bank", return_value=bank):
            self.assertEqual(self.exam.version, exam.Exam(self.directory).version)
            self.assertEqual(companion.version, exam.Exam(self.directory, "microsoft").version)
            self.assertNotEqual(full_types.version, exam.Exam(self.directory, "types").version)
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.grade(self.payload({"Q04": "A"}))
        self.assertEqual(caught.exception.status, 400)

    def test_wording_changes_reject_old_answers_and_preserve_submitted_snapshots(self):
        payload = self.payload(self.all_correct())
        snapshot = self.exam.submit(payload)
        for field in ("title", "scenario", "prompt", "options"):
            bank = quiz.load_bank()
            q = bank["types"][0]
            if field == "options":
                q[field]["A"] += " Changed wording"
            else:
                q[field] += " Changed wording"
            with self.subTest(field=field), patch.object(quiz, "load_bank", return_value=bank):
                revised = exam.Exam(self.exam.report_dir)
                self.assertNotEqual(self.exam.version, revised.version)
                with self.assertRaises(exam.ExamError) as caught:
                    revised.grade(payload)
                self.assertEqual(caught.exception.status, 409)
                saved = self.exam.report_dir / f"{payload['attempt_id']}.json"
                self.assertEqual(json.loads(saved.read_text(encoding="utf-8")), snapshot)
                self.assertEqual(saved.with_suffix(".md").read_text(encoding="utf-8"), snapshot["markdown"])

    def test_reviewed_practice_continuation_is_scoped_to_exact_paper_and_target(self):
        manifest = json.loads((quiz.BANK / "practice-compatibility.json").read_text(encoding="utf-8"))
        self.assertEqual({paper["group"] for paper in manifest["papers"]}, {None, *quiz.GROUPS})
        for entry in manifest["papers"]:
            with self.subTest(group=entry["group"]):
                paper = exam.Exam(self.directory, entry["group"])
                expected = [entry["from"]] if paper.version == entry["to"] else []
                self.assertEqual(paper.public()["practice_compatible_versions"], expected)
                self.assertEqual(exam.compatible_practice_versions(entry["group"], entry["to"]), [entry["from"]])
                self.assertEqual(exam.compatible_practice_versions(entry["group"], "0" * 64), [])
                other = "microsoft" if entry["group"] != "microsoft" else None
                self.assertEqual(exam.compatible_practice_versions(other, entry["to"]), [])

    def test_future_question_or_source_changes_disable_reviewed_practice_continuation(self):
        for field in ("title", "scenario", "prompt", "options", "answers"):
            bank = quiz.load_bank()
            q = bank["types"][0]
            if field == "options":
                q[field]["A"] += " Future wording"
            elif field == "answers":
                q[field] = [next(letter for letter in "ABCD" if letter != q[field][0])]
            else:
                q[field] += " Future wording"
            with self.subTest(field=field), patch.object(quiz, "load_bank", return_value=bank):
                self.assertEqual(exam.Exam(self.directory).practice_compatible_versions, [])
        original = quiz.excerpt
        with patch.object(quiz, "excerpt", side_effect=lambda block: original(block) + "\n// Future source"):
            self.assertEqual(exam.Exam(self.directory).practice_compatible_versions, [])

    def test_reviewed_old_versions_still_cannot_score_or_check_with_old_requests(self):
        manifest = json.loads((quiz.BANK / "practice-compatibility.json").read_text(encoding="utf-8"))
        old_version = next(p["from"] for p in manifest["papers"] if p["group"] is None)
        for action, payload in (
            (self.exam.grade, self.payload() | {"version": old_version}),
            (self.exam.practice, {"version": old_version, "question_id": "Q01", "answer": "A"}),
        ):
            with self.subTest(action=action.__name__), self.assertRaises(exam.ExamError) as caught:
                action(payload)
            self.assertEqual(caught.exception.status, 409)
        self.assertFalse(list(self.directory.rglob("*.json")))

    def test_malformed_practice_compatibility_manifest_is_rejected(self):
        original = json.loads((quiz.BANK / "practice-compatibility.json").read_text(encoding="utf-8"))
        invalid = [original | {"extra": True}, original | {"note": ""}]
        for field, value in (("group", "unknown"), ("from", "not-a-hash"), ("to", original["papers"][0]["from"])):
            revised = deepcopy(original)
            revised["papers"][0][field] = value
            invalid.append(revised)
        invalid.append(original | {"papers": original["papers"] + [original["papers"][0]]})
        for manifest in invalid:
            with self.subTest(manifest=manifest), patch.object(Path, "read_text", return_value=json.dumps(manifest)):
                with self.assertRaises(ValueError):
                    exam.compatible_practice_versions(None, self.exam.version)

    def test_all_correct(self):
        report = self.exam.grade(self.payload(self.all_correct()))
        self.assertEqual((report["score"], report["percent"], report["wrong"], report["unanswered"]), (40, 100.0, 0, 0))
        self.assertTrue(all(q["status"] == "correct" for q in report["questions"]))
        self.assert_counts(report)
        for q in report["questions"]:
            self.assertEqual(set(q["rationale"]), set("ABCD"))
            self.assertTrue(q["takeaway"])
            self.assertTrue(q["sources"])
            self.assertTrue(all(link["url"].startswith(exam.GITHUB) for link in q["learn"]))
        self.assertIn("值", report["questions"][0]["learn"][0]["title"])
        self.assertIn("40 / 40", report["markdown"])
        self.assertIn("## 逐题复盘", report["markdown"])
        self.assertIn("正确答案：", report["markdown"])

    def test_lessons_are_in_reports_but_not_the_public_paper(self):
        self.assertNotIn("lessons", self.exam.public())
        report = self.exam.grade(self.payload())
        self.assertEqual([lesson["group"] for lesson in report["lessons"]], [g["id"] for g in self.exam.groups])
        ids = [qid for lesson in report["lessons"] for section in lesson["sections"] for qid in section["questions"]]
        self.assertEqual(sorted(ids), sorted(self.exam.question_ids))
        for lesson in report["lessons"]:
            self.assertIn(lesson["intro"], report["markdown"])
            self.assertNotIn(lesson["intro"], exam.encode_json(self.exam.public()).decode())
            for section in lesson["sections"]:
                self.assertTrue(section["sources"])
                self.assertIn(section["takeaway"], report["markdown"])

    def test_lesson_changes_preserve_drafts_and_saved_report_snapshots(self):
        payload = self.payload()
        report = self.exam.submit(payload)
        bank = quiz.load_bank()
        lessons = quiz.resolved_lessons(quiz.migration_questions(bank, quiz.load_migration_exam(bank)),
                                        quiz.BANK / "lessons/migration")
        lessons["types"]["intro"] = "Updated explanation"
        with patch.object(quiz, "resolved_lessons", return_value=lessons):
            restarted = exam.Exam(self.exam.report_dir)
        self.assertEqual(restarted.version, self.exam.version)
        self.assertEqual(restarted.submit(payload), report)
        self.assertEqual(restarted.grade(self.payload())["lessons"][0]["intro"], "Updated explanation")

    def test_teaching_changes_refresh_practice_without_changing_score_versions_or_reports(self):
        payload = self.payload(self.all_correct())
        original = self.exam.submit(payload)
        paths = [self.exam.report_dir / f"{payload['attempt_id']}.{ext}" for ext in ("json", "md")]
        snapshots = [path.read_bytes() for path in paths]
        bank = quiz.load_bank()
        bank["types"][0]["explanation"]["principle"] = "修订后的机制讲解"
        with patch.object(quiz, "load_bank", return_value=bank):
            revised = exam.Exam(self.exam.report_dir)
        self.assertEqual(revised.version, self.exam.version)
        self.assertNotEqual(revised.explanation_version, self.exam.explanation_version)
        self.assertEqual(revised.submit(payload), original)
        self.assertEqual([path.read_bytes() for path in paths], snapshots)
        result = revised.practice({"version": revised.version, "question_id": "Q01", "answer": "A"})["question"]
        self.assertEqual(result["explanation"]["principle"], "修订后的机制讲解")
        self.assertEqual(result["explanation_version"], revised.public()["explanation_version"])
        self.assertEqual(revised.grade(payload)["score"], original["score"])

    def test_teaching_is_private_until_checked_and_in_new_report_exports(self):
        for group in (None, *quiz.GROUPS):
            paper = exam.Exam(self.directory, selected_group=group)
            public = exam.encode_json(paper.public()).decode()
            report = paper.grade(self.payload() | {"version": paper.version})
            for question in report["questions"]:
                with self.subTest(group=group, id=question["id"]):
                    teaching = question["explanation"]
                    self.assertNotIn(teaching["principle"], public)
                    for text in [teaching["principle"], *teaching["steps"], teaching["boundary"]]:
                        self.assertIn(text, report["markdown"])
            self.assertNotIn('"explanation":', public)

    def test_old_report_can_read_lessons_without_rewriting_files(self):
        payload = self.payload()
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.lesson_supplement(payload)
        self.assertEqual(caught.exception.status, 404)
        self.assertFalse(self.exam.report_dir.exists())
        old = self.exam.grade(payload)
        del old["lessons"]
        old["markdown"] = exam.markdown_report(old)
        self.exam.report_dir.mkdir()
        path = self.exam.report_dir / f"{payload['attempt_id']}.json"
        path.write_bytes(exam.encode_json(old))
        path.with_suffix(".md").write_text(old["markdown"], encoding="utf-8")
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.exam.report_dir.iterdir()}
        supplement = self.exam.lesson_supplement(payload)
        self.assertEqual(len(supplement["lessons"]), 4)
        self.assertIn("类型与建模讲解", supplement["markdown"])
        changed = deepcopy(payload)
        changed["answers"] = self.all_correct()
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.lesson_supplement(changed)
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual({p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.exam.report_dir.iterdir()}, before)

    def test_all_wrong(self):
        answers = {key: next(letter for letter in "ABCD" if letter != value)
                   for key, value in self.all_correct().items()}
        report = self.exam.grade(self.payload(answers))
        self.assertEqual((report["score"], report["wrong"], report["unanswered"]), (0, 40, 0))
        self.assertTrue(all(q["status"] == "wrong" for q in report["questions"]))
        self.assert_counts(report)

    def test_all_unanswered(self):
        report = self.exam.grade(self.payload())
        self.assertEqual((report["score"], report["wrong"], report["unanswered"]), (0, 0, 40))
        self.assertTrue(all(q["selected"] is None and q["status"] == "unanswered" for q in report["questions"]))
        self.assert_counts(report)

    def test_mixed_answers_and_group_rounding(self):
        answers = self.all_correct()
        wrong = next(letter for letter in "ABCD" if letter != answers["Q02"])
        report = self.exam.grade(self.payload({"Q01": answers["Q01"], "Q02": wrong}))
        self.assertEqual((report["correct"], report["wrong"]), (1, 1))
        self.assertEqual(report["unanswered"], 38)
        self.assert_counts(report)
        self.assertEqual(report["groups"][0]["percent"], 10.0)
        self.assertEqual(report["percent"], 2.5)

    def test_unequal_groups_keep_one_point_per_question(self):
        answers = self.all_correct()
        report = self.exam.grade(self.payload({"Q41": answers["Q41"], "Q22": answers["Q22"]}))
        groups = {g["id"]: g for g in report["groups"]}
        self.assertEqual((report["score"], report["total"], report["percent"]), (2, 40, 5.0))
        self.assertEqual(groups["runtime"]["percent"], 7.1)
        self.assertEqual(groups["execution"]["percent"], 12.5)
        self.assert_counts(report)

    def test_invalid_submissions(self):
        cases = [{"answers": {"Q999": "A"}}, {"answers": {"Q00": "A"}},
                 {"answers": {"Q01": "AB"}}, {"answers": {"Q01": ""}}, {"answers": {"Q01": None}},
                 {"answers": {"Q01": ["A"]}}, {"answers": {"Q01": True}}, {"answers": []},
                 {"answers": {"Q01": "a"}}, {"attempt_id": "../escape"},
                 {"attempt_id": str(uuid4()).upper()}, {"attempt_id": 12},
                 {"elapsed_seconds": -1}, {"elapsed_seconds": True}, {"elapsed_seconds": 2.5},
                 {"elapsed_seconds": exam.MAX_ELAPSED + 1}, {"elapsed_seconds": "20"},
                 {"extra": "not accepted"}, {"score": 120}]
        for fields in cases:
            with self.subTest(fields=fields):
                payload = self.payload()
                payload.update(fields)
                with self.assertRaises(exam.ExamError) as caught:
                    self.exam.submit(payload)
                self.assertEqual(caught.exception.status, 400)
        self.assertFalse(self.exam.report_dir.exists())

    def test_version_mismatch(self):
        payload = self.payload()
        payload["version"] = "old"
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.submit(payload)
        self.assertEqual(caught.exception.status, 409)
        self.assertFalse(self.exam.report_dir.exists())

    def test_each_paper_grades_only_its_twenty_questions_and_lesson(self):
        for group in quiz.COMBINED_GROUPS:
            with self.subTest(group=group):
                paper = exam.Exam(self.directory / group, selected_group=group)
                public = paper.public()
                self.assertEqual((public["total"], public["bank_total"], public["combined_total"]), (20, 240, 40))
                self.assertEqual(public["selected_group"], group)
                self.assertEqual([p["id"] for p in public["papers"]], ["microsoft", None])
                self.assertEqual({q["group"] for q in public["questions"]}, {group})
                answers = {q["id"]: q["answers"][0] for q in paper.questions}
                payload = self.payload(answers) | {"version": paper.version}
                report = paper.submit(payload)
                self.assertEqual((report["score"], report["total"], report["percent"]), (20, 20, 100.0))
                self.assertEqual([lesson["group"] for lesson in report["lessons"]], [group])
                self.assert_counts(report)
                self.assertEqual(exam.Exam(paper.report_dir, group).submit(payload), report)
                with self.assertRaises(exam.ExamError) as caught:
                    self.exam.grade(payload)
                self.assertEqual(caught.exception.status, 409)
                alien = next(q["id"] for q in self.exam.questions if q["group"] != group)
                with self.assertRaises(exam.ExamError) as caught:
                    paper.grade(payload | {"answers": {alien: "A"}})
                self.assertEqual(caught.exception.status, 400)

    def test_companion_paper_is_independent_and_reports_twelve_units(self):
        paper = exam.Exam(self.directory / "companion", "microsoft")
        public = paper.public()
        self.assertEqual(public["title"], "Microsoft Learn C# 配套自测")
        self.assertEqual(public["total"], 120)
        self.assertEqual([q["id"] for q in public["questions"]], [f"Q{i}" for i in range(121, 241)])
        self.assertEqual([g["count"] for g in public["groups"]], [10] * 12)
        self.assertTrue(paper.question_ids.isdisjoint(self.exam.question_ids))
        bank = quiz.load_bank()
        bank["microsoft"][0]["prompt"] = "Changed companion question"
        with patch.object(quiz, "load_bank", return_value=bank):
            self.assertEqual(self.exam.version, exam.Exam(self.directory).version)
            self.assertNotEqual(paper.version, exam.Exam(self.directory, "microsoft").version)
        for field in ("answers", "rationale", "sources", "verification", "lessons"):
            self.assertNotIn(f'"{field}"', exam.encode_json(public).decode())
        answers = {q["id"]: q["answers"][0] for q in paper.questions[:10]}
        answers[paper.questions[10]["id"]] = next(c for c in "ABCD" if c != paper.questions[10]["answers"][0])
        payload = self.payload(answers) | {"version": paper.version}
        report = paper.submit(payload)
        self.assertEqual((report["score"], report["wrong"], report["unanswered"], report["percent"]), (10, 1, 109, 8.3))
        self.assert_counts(report)
        self.assertEqual((report["groups"][0]["correct"], report["groups"][0]["percent"]), (10, 100.0))
        self.assertEqual(report["groups"][1]["wrong"], 1)
        self.assertEqual([l["group"] for l in report["lessons"]], ["microsoft"])
        self.assertEqual(len(report["lessons"][0]["sections"]), 12)
        self.assertTrue(paper.lesson_supplement(payload)["markdown"].startswith(
            "# Microsoft Learn C# 配套自测 · 套题讲解\n"))
        self.assertEqual(exam.Exam(paper.report_dir, "microsoft").submit(payload), report)
        all_answers = {q["id"]: q["answers"][0] for q in paper.questions}
        self.assertEqual(paper.grade(self.payload(all_answers) | {"version": paper.version})["score"], 120)
        for changed in ({"version": self.exam.version}, {"answers": {"Q01": "A"}}):
            with self.assertRaises(exam.ExamError):
                paper.grade(payload | changed)

    def test_practice_checks_one_question_for_every_paper_without_reports(self):
        before = list(self.directory.rglob("*.json"))
        for group in (None, *quiz.GROUPS):
            with self.subTest(group=group):
                paper = exam.Exam(self.directory, group)
                for question in (paper.questions[0], paper.questions[-1]):
                    correct = question["answers"][0]
                    for selected in (correct, next(letter for letter in "ABCD" if letter != correct)):
                        payload = {"version": paper.version, "question_id": question["id"], "answer": selected}
                        result = paper.practice(payload)
                        expected = next(q for q in paper.grade(self.payload({question["id"]: selected}) |
                                                              {"version": paper.version})["questions"] if q["id"] == question["id"])
                        self.assertEqual(result, {"version": paper.version, "question": expected})
                        self.assertEqual(set(result["question"]["rationale"]), set("ABCD"))
                        self.assertNotIn("lessons", result)
                        self.assertNotIn("questions", result)
        self.assertEqual(list(self.directory.rglob("*.json")), before)

    def test_practice_rejects_invalid_choices_ids_and_versions(self):
        payload = {"version": self.exam.version, "question_id": "Q01", "answer": "A"}
        invalid = [None, [], {}, payload | {"extra": True}, payload | {"question_id": "Q121"},
                   payload | {"question_id": []}, payload | {"answer": "AB"}, payload | {"answer": "a"},
                   payload | {"answer": None}, payload | {"answer": ["A"]}, payload | {"answer": True}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(exam.ExamError) as caught:
                self.exam.practice(value)
            self.assertEqual(caught.exception.status, 400)
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.practice(payload | {"version": "outdated"})
        self.assertEqual(caught.exception.status, 409)

    def test_practice_result_does_not_mutate_exam_or_report(self):
        payload = {"version": self.exam.version, "question_id": "Q01", "answer": "A"}
        original = self.exam.practice(payload)
        changed = self.exam.practice(payload)
        changed["question"]["rationale"]["A"] = "changed"
        changed["question"]["options"]["A"] = "changed"
        self.assertEqual(self.exam.practice(payload), original)
        self.assertNotIn("answers", self.exam.public()["questions"][0])

    def test_legacy_sixty_question_snapshot_is_not_rewritten(self):
        bank = {g: qs for g, qs in quiz.load_bank().items() if g in ("types", "execution", "runtime")}
        with patch.object(quiz, "load_bank", return_value=bank), \
                patch.object(quiz, "load_migration_exam", return_value=self.legacy_manifest(bank)), \
                patch.object(quiz, "resolved_lessons", return_value={}):
            old = exam.Exam(self.exam.report_dir)
        payload = self.payload({q["id"]: q["answers"][0] for q in old.questions}) | {"version": old.version}
        report = old.submit(payload)
        path = old.report_dir / f"{payload['attempt_id']}.json"
        snapshot = path.read_bytes()
        self.assertEqual((report["score"], report["total"]), (60, 60))
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.submit(payload)
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(path.read_bytes(), snapshot)

    def test_legacy_40_question_report_keeps_original_score(self):
        converted = {"Q07", "Q08", "Q10", "Q11", "Q15", "Q22", "Q27", "Q30", "Q34", "Q35",
                     "Q37", "Q38", "Q39", "Q40", "Q41", "Q46", "Q48", "Q50", "Q53", "Q54"}
        old_bank = {group: [q for q in questions if q["id"] not in converted]
                    for group, questions in quiz.load_bank().items() if group in ("types", "execution", "runtime")}
        with patch.object(quiz, "load_bank", return_value=old_bank), \
                patch.object(quiz, "load_migration_exam", return_value=self.legacy_manifest(old_bank)), \
                patch.object(quiz, "resolved_lessons", return_value={}):
            legacy = exam.Exam(self.exam.report_dir)
        payload = self.payload({q["id"]: q["answers"][0] for q in legacy.questions})
        payload["version"] = legacy.version
        old_report = legacy.submit(payload)
        path = self.exam.report_dir / f"{payload['attempt_id']}.json"
        original_bytes = path.read_bytes()
        self.assertEqual((old_report["score"], old_report["total"], old_report["percent"]), (40, 40, 100.0))
        with self.assertRaises(exam.ExamError) as caught:
            self.exam.submit(payload)
        self.assertEqual(caught.exception.status, 409)
        new_report = self.exam.submit(self.payload(self.all_correct()))
        self.assertEqual((new_report["score"], new_report["total"], new_report["percent"]), (40, 40, 100.0))
        self.assertEqual(path.read_bytes(), original_bytes)
        self.assertEqual(path.with_suffix(".md").read_text(encoding="utf-8"), old_report["markdown"])

    def test_legacy_120_report_and_version_stay_distinct_from_the_extension(self):
        bank = {g: qs for g, qs in quiz.load_bank().items() if g in quiz.COMBINED_GROUPS}
        lessons = quiz.resolved_lessons(bank)
        with patch.object(quiz, "load_migration_exam", return_value=self.legacy_manifest(bank)), \
                patch.object(quiz, "resolved_lessons", return_value=lessons):
            old = exam.Exam(self.exam.report_dir)
        self.assertEqual(old.version, "b29670f7cde6deda2227425d6277f45348a1e4e5fd06c9a47c1db3984696923b")
        payload = self.payload({q["id"]: q["answers"][0] for q in old.questions}) | {"version": old.version}
        snapshot = old.submit(payload)
        before = {p.name: p.read_bytes() for p in self.exam.report_dir.iterdir()}
        self.assertEqual((snapshot["score"], snapshot["total"]), (120, 120))
        self.assertEqual(self.exam.practice_compatible_versions, [])
        for action, request in ((self.exam.submit, payload),
                                (self.exam.practice, {"version": old.version, "question_id": "Q01", "answer": "B"})):
            with self.subTest(action=action.__name__), self.assertRaises(exam.ExamError) as caught:
                action(request)
            self.assertEqual(caught.exception.status, 409)
        self.assertEqual({p.name: p.read_bytes() for p in self.exam.report_dir.iterdir()}, before)

    def test_json_rejects_duplicate_keys_and_invalid_values(self):
        cases = [b'{"answers":{},"answers":{}}', b'{"answers":{"Q01":"A","Q01":"B"}}',
                 b'{"elapsed_seconds": NaN}', b'[]', b'null', b'{', b'\xff', b'[' * 2000]
        for body in cases:
            with self.subTest(body=body[:50]), self.assertRaises(exam.ExamError):
                exam.parse_submission(body)

    def test_reports_saved_and_same_submission_reuses_after_restart(self):
        payload = self.payload(self.all_correct())
        report = self.exam.submit(payload)
        json_path = self.exam.report_dir / f"{payload['attempt_id']}.json"
        markdown_path = json_path.with_suffix(".md")
        saved = json_path.read_bytes()
        modified = json_path.stat().st_mtime_ns
        self.assertEqual(json.loads(saved), report)
        self.assertEqual(markdown_path.read_text(encoding="utf-8"), report["markdown"])
        self.assertEqual(report["files"]["json"], f"artifacts/quiz-reports/{payload['attempt_id']}.json")
        self.assertEqual(self.exam.submit(payload), report)
        restarted = exam.Exam(self.exam.report_dir)
        self.assertEqual(restarted.submit(payload), report)
        self.assertEqual(json_path.read_bytes(), saved)
        self.assertEqual(json_path.stat().st_mtime_ns, modified)
        self.assertEqual(len(list(self.exam.report_dir.iterdir())), 2)
        changed = deepcopy(payload)
        changed["answers"] = {}
        with self.assertRaises(exam.ExamError) as caught:
            restarted.submit(changed)
        self.assertEqual(caught.exception.status, 409)
        changed = deepcopy(payload)
        changed["elapsed_seconds"] += 1
        with self.assertRaises(exam.ExamError):
            restarted.submit(changed)
        self.assertEqual(json_path.read_bytes(), saved)

    def test_concurrent_retries_publish_one_report(self):
        payload = self.payload(self.all_correct())
        instances = [exam.Exam(self.exam.report_dir) for _ in range(3)]
        with ThreadPoolExecutor(max_workers=3) as pool:
            reports = list(pool.map(lambda instance: instance.submit(payload), instances))
        self.assertTrue(all(report == reports[0] for report in reports))
        self.assertEqual(len(list(self.exam.report_dir.iterdir())), 2)

    def test_markdown_failure_is_recoverable_after_restart(self):
        payload = self.payload()
        original = exam.publish_once

        def fail_markdown(path, content):
            if path.suffix == ".md":
                raise OSError("simulated disk error")
            return original(path, content)

        with patch.object(exam, "publish_once", side_effect=fail_markdown), self.assertRaises(OSError):
            self.exam.submit(payload)
        json_path = self.exam.report_dir / f"{payload['attempt_id']}.json"
        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        restarted = exam.Exam(self.exam.report_dir)
        self.assertEqual(restarted.submit(payload), persisted)
        self.assertEqual(json_path.with_suffix(".md").read_text(encoding="utf-8"), persisted["markdown"])
        self.assertEqual(len(list(self.exam.report_dir.iterdir())), 2)

    def test_failed_json_publish_leaves_no_partial_report(self):
        with patch.object(exam.os, "link", side_effect=OSError("simulated disk error")), self.assertRaises(OSError):
            self.exam.submit(self.payload())
        self.assertEqual(list(self.exam.report_dir.iterdir()), [])

    def test_concurrent_conflicting_submissions_do_not_overwrite(self):
        payload = self.payload(self.all_correct())
        changed = deepcopy(payload)
        changed["answers"] = {}
        other = exam.Exam(self.exam.report_dir)

        def try_submit(arguments):
            instance, content = arguments
            try:
                return instance.submit(content)
            except exam.ExamError as error:
                return error.status

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(try_submit, [(self.exam, payload), (other, changed)]))
        self.assertEqual(sum(result == 409 for result in results), 1)
        winner = next(result for result in results if isinstance(result, dict))
        json_path = self.exam.report_dir / f"{payload['attempt_id']}.json"
        self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), winner)
        self.assertEqual(json_path.with_suffix(".md").read_text(encoding="utf-8"), winner["markdown"])

    def test_elapsed_seconds_endpoints_are_accepted(self):
        for elapsed in (0, exam.MAX_ELAPSED):
            payload = self.payload()
            payload["elapsed_seconds"] = elapsed
            self.assertEqual(self.exam.grade(payload)["elapsed_seconds"], elapsed)


class CombinedChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper = exam.Exam(selected_group="combined")

    def payload(self, answers):
        return {"version": self.paper.version, "attempt_id": str(uuid4()), "answers": answers, "elapsed_seconds": 0}

    def test_combined_order_numbering_chapters_and_legacy_versions(self):
        paper, public = self.paper, self.paper.public()
        self.assertEqual((public["total"], public["bank_total"]), (160, 240))
        self.assertEqual([p["id"] for p in public["papers"]], ["combined"])
        self.assertEqual([g["count"] for g in public["groups"]], [10] * 12 + [10, 14, 8, 8])
        self.assertTrue(all(g["label"].startswith("基础 · ") for g in paper.groups[:12]))
        self.assertTrue(all(g["label"].startswith("扩展 · ") for g in paper.groups[12:]))
        self.assertEqual([q["display_id"] for q in public["questions"]], [f"Q{i:02}" for i in range(1, 161)])
        basic, extension = paper.parts.values()
        self.assertFalse(basic.question_ids & extension.question_ids)
        self.assertEqual([q["id"] for q in paper.questions], [q["id"] for q in basic.questions + extension.questions])
        self.assertEqual(public["previous_versions"], {"microsoft": exam.Exam(selected_group="microsoft").version,
                                                      "extension": exam.Exam().version})
        self.assertFalse(extension.groups[0]["label"].startswith("扩展 · "))
        self.assertTrue(all("answers" not in q and "rationale" not in q for q in public["questions"]))

    def test_combined_scoring_and_complete_prefixed_explanations(self):
        correct = {q["id"]: q["answers"][0] for q in self.paper.questions}
        report = self.paper.grade(self.payload(correct))
        self.assertEqual((report["score"], report["total"], report["percent"]), (160, 160, 100.0))
        self.assertEqual(len(report["groups"]), 16)
        self.assertEqual(sum(g["correct"] for g in report["groups"]), 160)
        lesson_ids = [qid for lesson in report["lessons"] for section in lesson["sections"] for qid in section["questions"]]
        self.assertEqual(set(lesson_ids), self.paper.question_ids)
        self.assertEqual(len(lesson_ids), 160)
        self.assertTrue(all(section["title"].startswith(("基础 · ", "扩展 · "))
                            for lesson in report["lessons"] for section in lesson["sections"]))
        self.assertIn("160 / 160", report["markdown"])
        self.assertEqual(report["markdown"].count("正确答案："), 160)
        partial = {self.paper.questions[0]["id"]: correct[self.paper.questions[0]["id"]],
                   self.paper.questions[120]["id"]: correct[self.paper.questions[120]["id"]],
                   self.paper.questions[-1]["id"]: next(c for c in "ABCD" if c != self.paper.questions[-1]["answers"][0])}
        result = self.paper.grade(self.payload(partial))
        self.assertEqual((result["correct"], result["wrong"], result["unanswered"], result["percent"]), (2, 1, 157, 1.2))
        self.assertEqual(self.paper.grade(self.payload({}))["unanswered"], 160)


class HttpChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="quiz-exam-http-")
        cls.directory = Path(cls.temporary.name)
        static = cls.directory / "web"
        static.mkdir()
        for filename in ("index.html", "app.js", "styles.css"):
            (static / filename).write_text(f"test {filename}", encoding="utf-8")
        cls.server = exam.make_server(port=0, report_dir=cls.directory / "reports", static_dir=static)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temporary.cleanup()

    def request(self, path, method="GET", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def payload(self):
        return {"version": self.server.exam.version, "attempt_id": str(uuid4()), "answers": {}, "elapsed_seconds": 1}

    def headers(self):
        return {"Content-Type": "application/json", "X-Exam-Token": self.server.exam.token,
                "Origin": self.server.origin, "Sec-Fetch-Site": "same-origin"}

    def test_binds_only_loopback_and_serves_public_exam(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("/api/exam")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["total"], 160)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertNotIn('"rationale"', body.decode())
        self.assertNotIn('"answers"', body.decode())
        self.assertNotIn('"lessons"', body.decode())

    def test_old_page_links_redirect_to_combined_without_changing_legacy_api(self):
        for group, count in (("microsoft", 120), ("extension", 40)):
            status, headers, _ = self.request("/?group=" + group)
            self.assertEqual(status, 302)
            self.assertEqual(headers["Location"], "/")
            data = json.loads(self.request("/api/exam?group=" + group)[2])
            self.assertEqual(data["total"], count)
            self.assertEqual(data["version"], self.server.exam.public()["previous_versions"][group])

    def test_static_allowlist_blocks_private_repository_files(self):
        for path in ("/", "/index.html", "/app.js", "/styles.css"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 200)
        for path in ("/exercises/quiz/types.json", "/scripts/quiz.py", "/docs/quiz/types-answers.md",
                     "/artifacts/quiz-reports/", "/../exercises/quiz/types.json", "/%2e%2e/exercises/quiz/types.json",
                     "/web/quiz/", "/favicon.ico"):
            with self.subTest(path=path):
                status, _, body = self.request(path)
                self.assertEqual(status, 404)
                self.assertIn("error", json.loads(body))
        host = self.server.origin.removeprefix("http://")
        self.assertEqual(self.request("http://evil.example/api/exam", headers={"Host": host})[0], 404)

    def test_archive_download_is_the_generated_markdown_with_all_answers(self):
        status, headers, body = self.request("/question-bank.md")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/markdown; charset=utf-8")
        self.assertEqual(body, (quiz.DOCS / "question-bank.md").read_bytes())
        self.assertEqual(body.decode("utf-8").count("**答案："), 240)

    def test_valid_submission_and_retry(self):
        payload = exam.encode_json(self.payload())
        status, _, body = self.request("/api/submit", "POST", payload, self.headers())
        self.assertEqual(status, 200)
        report = json.loads(body)
        self.assertEqual(report["unanswered"], 160)
        self.assertEqual(self.request("/api/submit", "POST", payload, self.headers())[2], body)
        self.assertTrue((self.server.exam.report_dir / f"{report['attempt_id']}.md").is_file())

    def test_selected_paper_http_token_scoring_and_lessons(self):
        status, _, body = self.request("/api/exam?group=queries")
        self.assertEqual(status, 200)
        public = json.loads(body)
        self.assertEqual(public["total"], 20)
        self.assertEqual([q["id"] for q in public["questions"]], [f"Q{i}" for i in range(101, 121)])
        self.assertEqual(self.request("/api/exam?group=queries")[2], body)
        self.assertNotEqual(public["token"], self.server.exam.token)
        payload = self.payload() | {"version": public["version"], "answers": {"Q101": "A"}}
        encoded = exam.encode_json(payload)
        self.assertEqual(self.request("/api/submit?group=queries", "POST", encoded, self.headers())[0], 403)
        headers = self.headers() | {"X-Exam-Token": public["token"]}
        status, _, result = self.request("/api/submit?group=queries", "POST", encoded, headers)
        self.assertEqual(status, 200)
        report = json.loads(result)
        self.assertEqual((report["total"], report["unanswered"]), (20, 19))
        self.assertEqual(self.request("/api/submit?group=queries", "POST", encoded, headers)[2], result)
        self.assertEqual(self.request("/api/submit", "POST", encoded, self.headers())[0], 409)
        status, _, result = self.request("/api/lessons?group=queries", "POST", encoded, headers)
        self.assertEqual(status, 200)
        self.assertEqual([lesson["group"] for lesson in json.loads(result)["lessons"]], ["queries"])

    def test_companion_http_is_scoped_and_requires_submission_before_lessons(self):
        status, _, body = self.request("/api/exam?group=microsoft")
        self.assertEqual(status, 200)
        paper = json.loads(body)
        self.assertEqual(paper["total"], 120)
        self.assertEqual(len(paper["groups"]), 12)
        payload = self.payload() | {"version": paper["version"], "answers": {"Q121": "A"}}
        encoded = exam.encode_json(payload)
        headers = self.headers() | {"X-Exam-Token": paper["token"]}
        self.assertEqual(self.request("/api/lessons?group=microsoft", "POST", encoded, headers)[0], 404)
        self.assertEqual(self.request("/api/submit?group=microsoft", "POST", encoded, self.headers())[0], 403)
        status, _, result = self.request("/api/submit?group=microsoft", "POST", encoded, headers)
        self.assertEqual(status, 200)
        report = json.loads(result)
        self.assertEqual(report["unanswered"], 119)
        self.assertEqual(len(report["groups"]), 12)
        self.assertEqual(self.request("/api/lessons?group=microsoft", "POST", encoded, headers)[0], 200)
        self.assertEqual(self.request("/api/submit", "POST", encoded, self.headers())[0], 409)



    def test_removed_practice_http_cannot_reveal_answers(self):
        for group in (None, "microsoft"):
            query = "" if group is None else "?group=" + group
            status, _, body = self.request("/api/practice" + query, "POST", b"{}", self.headers())
            self.assertEqual(status, 404)
            self.assertNotIn("question", json.loads(body))

    def test_unknown_or_ambiguous_paper_query_is_rejected(self):
        for query in ("group=unknown", "group=", "group=types&group=queries", "group=types&extra=x"):
            with self.subTest(query=query):
                self.assertEqual(self.request("/api/exam?" + query)[0], 404)
                self.assertEqual(self.request("/api/submit?" + query, "POST", b"{}", self.headers())[0], 404)

    def test_lessons_require_an_existing_submission_and_token(self):
        payload = exam.encode_json(self.payload())
        self.assertEqual(self.request("/api/lessons")[0], 404)
        self.assertEqual(self.request("/api/lessons", "POST", payload, self.headers())[0], 404)
        self.assertEqual(self.request("/api/submit", "POST", payload, self.headers())[0], 200)
        status, _, body = self.request("/api/lessons", "POST", payload, self.headers())
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)["lessons"]), 5)
        headers = self.headers() | {"X-Exam-Token": "wrong"}
        self.assertEqual(self.request("/api/lessons", "POST", payload, headers)[0], 403)

    def test_origin_host_and_token_validation(self):
        for changes in ({"Host": "evil.example"}, {"Origin": "https://evil.example"},
                        {"Origin": "null"}, {"Sec-Fetch-Site": "cross-site"},
                        {"X-Exam-Token": "wrong"}, {"X-Exam-Token": ""}):
            with self.subTest(changes=changes):
                headers = self.headers() | changes
                status, _, body = self.request("/api/submit", "POST", exam.encode_json(self.payload()), headers)
                self.assertEqual(status, 403)
                self.assertIn("error", json.loads(body))
        self.assertEqual(self.request("/api/exam", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request("/api/exam", headers={"Origin": "https://evil.example"})[0], 403)

    def test_invalid_json_media_type_and_length(self):
        for body in (b'{"answers":{},"answers":{}}', b'null', b'not-json'):
            self.assertEqual(self.request("/api/submit", "POST", body, self.headers())[0], 400)
        headers = self.headers() | {"Content-Type": "text/plain"}
        self.assertEqual(self.request("/api/submit", "POST", b"{}", headers)[0], 415)
        headers = self.headers() | {"Content-Length": str(exam.MAX_BODY + 1)}
        self.assertEqual(self.request("/api/submit", "POST", b"{}", headers)[0], 413)
        headers = self.headers() | {"Transfer-Encoding": "chunked"}
        self.assertEqual(self.request("/api/submit", "POST", b"{}", headers)[0], 400)
        self.assertEqual(self.request("/unknown", "POST", b"{}", self.headers())[0], 404)
        status, _, body = self.request("/api/submit", "OPTIONS")
        self.assertEqual(status, 501)
        self.assertIn("error", json.loads(body))

    def test_http_reports_validation_and_write_failure_without_stack(self):
        payload = self.payload()
        payload["answers"] = {"Q999": "A"}
        self.assertEqual(self.request("/api/submit", "POST", exam.encode_json(payload), self.headers())[0], 400)
        payload = self.payload()
        payload["version"] = "stale"
        self.assertEqual(self.request("/api/submit", "POST", exam.encode_json(payload), self.headers())[0], 409)
        with patch.object(exam, "publish_once", side_effect=OSError("secret implementation detail")):
            status, _, body = self.request("/api/submit", "POST", exam.encode_json(self.payload()), self.headers())
        self.assertEqual(status, 500)
        self.assertIn("error", json.loads(body))
        self.assertNotIn(b"secret", body)
        self.assertNotIn(b"Traceback", body)

    def test_duplicate_host_header_is_rejected(self):
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=5) as connection:
            host = self.server.origin.removeprefix("http://")
            connection.sendall(f"GET /api/exam HTTP/1.0\r\nHost: {host}\r\nHost: evil.example\r\n\r\n".encode())
            response = http.client.HTTPResponse(connection)
            response.begin()
            self.assertEqual(response.status, 403)
            self.assertIn("error", json.loads(response.read()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
