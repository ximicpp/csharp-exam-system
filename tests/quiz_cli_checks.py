"""Regression checks against false-positive quiz verification; never edit learner data."""
from __future__ import annotations

from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import quiz


class QuizVerificationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.groups = quiz.load_bank()

    def test_json_does_not_silently_replace_an_answer_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            json.loads('{"answers":["A"],"answers":["B"]}', object_pairs_hook=quiz.unique_object)

    def test_single_choice_rejects_two_correct_options(self) -> None:
        q = deepcopy(self.groups["types"][0])
        q["answers"] = ["A", "B"]
        with self.assertRaisesRegex(ValueError, "answer count"):
            quiz.validate_question(q)

    def test_scenario_can_be_omitted_without_weakening_the_prompt(self) -> None:
        q = deepcopy(self.groups["types"][0])
        q["scenario"] = ""
        quiz.validate_question(q)
        page = quiz.render_questions("types", [q])
        self.assertIn(q["prompt"], page)
        self.assertNotIn("\n\n\n", page)
        for value in (None, [], "   "):
            q["scenario"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "invalid scenario"):
                quiz.validate_question(q)
        q["scenario"] = ""
        q["prompt"] = ""
        with self.assertRaisesRegex(ValueError, "empty prompt"):
            quiz.validate_question(q)

    def test_multiple_choice_kind_cannot_reenter_bank(self) -> None:
        q = deepcopy(self.groups["types"][0])
        q["kind"] = "multiple"
        for answers in (["A"], ["A", "B"]):
            q["answers"] = answers
            with self.subTest(answers=answers), self.assertRaisesRegex(ValueError, "invalid kind"):
                quiz.validate_question(q)

    def test_explanation_requires_a_rule_reasoning_and_boundary(self) -> None:
        source = self.groups["types"][0]
        for value in ({}, None, {"principle": "", "steps": ["a", "b"], "boundary": "c"},
                      {"principle": "a", "steps": ["b"], "boundary": "c"},
                      {"principle": "a", "steps": ["b", "b"], "boundary": "c"},
                      {"principle": "a", "steps": ["b", ""], "boundary": "c"}):
            question = deepcopy(source)
            question["explanation"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "explanation"):
                quiz.validate_question(question)

    def test_all_explanations_are_rendered_before_option_rationales(self) -> None:
        for group, questions in self.groups.items():
            page = quiz.render_answers(group, questions)
            for q in questions:
                with self.subTest(id=q["id"]):
                    section = page.split(f'## {q["id"]} · ', 1)[1].split('\n## ', 1)[0]
                    for text in [q["explanation"]["principle"], *q["explanation"]["steps"], q["explanation"]["boundary"]]:
                        self.assertIn(text, section)
                    self.assertLess(section.index("**知识点规则**"), section.index("**逐项辨析**"))

    def test_lessons_cover_every_question_exactly_once(self) -> None:
        lesson = quiz.load_lessons(self.groups)["types"]
        for mutation in ("missing", "duplicate", "other-group"):
            changed = deepcopy(lesson)
            ids = changed["sections"][0]["questions"]
            if mutation == "missing":
                changed["sections"].pop()
            elif mutation == "duplicate":
                ids.append(ids[0])
            else:
                ids[0] = "Q21"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "question"):
                quiz.validate_lesson(changed, "types", self.groups["types"])

    def test_extension_selection_and_teaching_cover_exactly_forty_questions(self) -> None:
        manifest = quiz.load_migration_exam(self.groups)
        selected = quiz.migration_questions(self.groups, manifest)
        self.assertEqual({g: len(qs) for g, qs in selected.items()},
                         {"types": 10, "runtime": 14, "modeling": 8, "execution": 8})
        ids = [q["id"] for qs in selected.values() for q in qs]
        self.assertEqual(len(ids), len(set(ids)))
        lessons = quiz.load_lessons(selected, quiz.BANK / "lessons/migration")
        taught = [qid for lesson in lessons.values() for s in lesson["sections"] for qid in s["questions"]]
        self.assertEqual(sorted(taught), sorted(ids))
        page = quiz.render_migration_exam(self.groups)
        for qid in ids:
            self.assertIn(f"| {qid} |", page)
        for mutation in ("duplicate", "wrong-group", "missing", "companion", "duplicate-group"):
            changed = deepcopy(manifest)
            if mutation == "duplicate":
                changed["groups"][0]["questions"].append("Q01")
            elif mutation == "wrong-group":
                changed["groups"][0]["questions"][0] = "Q41"
            elif mutation == "missing":
                changed["groups"][0]["questions"].pop()
            elif mutation == "companion":
                changed["groups"][0]["id"] = "microsoft"
            else:
                changed["groups"].append(changed["groups"][0])
            with self.subTest(mutation=mutation), patch.object(quiz.json, "loads", return_value=changed), \
                    self.assertRaisesRegex(ValueError, "[Mm]igration exam"):
                quiz.load_migration_exam(self.groups)

    def test_complete_archive_contains_every_question_and_explanation_once(self) -> None:
        page = quiz.render_question_bank(self.groups)
        numbering = quiz.migration_numbering(quiz.migration_questions(self.groups, quiz.load_migration_exam(self.groups)))
        self.assertEqual(list(numbering.values()), [f"Q{i:02}" for i in range(1, 41)])
        self.assertEqual(page.count('<a id="q'), 240)
        self.assertEqual(page.count("**答案："), 240)
        for questions in self.groups.values():
            for q in questions:
                with self.subTest(id=q["id"]):
                    self.assertEqual(page.count(f'<a id="{q["id"].lower()}"></a>'), 1)
                    section = page.split(f'<a id="{q["id"].lower()}"></a>', 1)[1].split('<a id="q', 1)[0]
                    self.assertIn(q["prompt"], section)
                    self.assertIn(f"**答案：{q['answers'][0]}**", section)
                    for letter in "ABCD":
                        self.assertIn(f"- {letter}. {q['options'][letter]}", section)
                        self.assertIn(q["rationale"][letter], section)
                    for text in [q["explanation"]["principle"], *q["explanation"]["steps"], q["explanation"]["boundary"],
                                 q["verification"]["note"], *[s["url"] for s in q["sources"]]]:
                        self.assertIn(text, section)
                    for block in q["code"]:
                        self.assertIn(quiz.excerpt(block), section)
                    if q["id"] in numbering:
                        self.assertIn(f"#### {numbering[q['id']]} · {q['title']}", section)

    def test_lesson_cannot_use_unrelated_source(self) -> None:
        lesson = quiz.load_lessons(self.groups)["types"]
        lesson["sections"][0]["code"].append({"path": "scripts/quiz.py", "region": "Q01"})
        with self.assertRaisesRegex(ValueError, "associated question"):
            quiz.validate_lesson(lesson, "types", self.groups["types"])

    def test_three_digit_ids_are_canonical_and_numeric_order_is_retained(self) -> None:
        self.assertEqual([q["id"] for q in self.groups["queries"]], [f"Q{i}" for i in range(101, 121)])
        question = deepcopy(self.groups["queries"][0])
        for invalid in ("Q001", "Q00", "Q1", "Q0101", "Q1000", "q101"):
            question["id"] = invalid
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "question id"):
                quiz.validate_question(question)

    def test_knowledge_map_covers_all_ids_and_rejects_gaps_or_duplicates(self) -> None:
        topics = quiz.load_curriculum(self.groups)
        ids = [qid for topic in topics for qid in topic["questions"]]
        self.assertEqual(len(ids), 120)
        for mutation in ("missing", "duplicate", "unknown"):
            changed = deepcopy(topics)
            if mutation == "missing":
                changed.pop()
            elif mutation == "duplicate":
                changed[0]["questions"].append(changed[0]["questions"][0])
            else:
                changed[0]["questions"][0] = "Q999"
            with patch.object(quiz.json, "loads", return_value=changed), \
                    self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "[Kk]nowledge"):
                quiz.load_curriculum(self.groups)

    def test_companion_map_and_units_cannot_omit_or_mix_questions(self) -> None:
        companion = {"microsoft": self.groups["microsoft"]}
        topics = quiz.load_curriculum(companion, "microsoft.curriculum.json")
        ids = [qid for topic in topics for qid in topic["questions"]]
        self.assertEqual(sorted(ids), sorted(q["id"] for q in companion["microsoft"]))
        lesson = quiz.load_lessons(companion)["microsoft"]
        lesson["sections"][0]["questions"], lesson["sections"][1]["questions"] = \
            lesson["sections"][1]["questions"], lesson["sections"][0]["questions"]
        with self.assertRaisesRegex(ValueError, "unit"):
            quiz.validate_lesson(lesson, "microsoft", companion["microsoft"])
        topics[0]["questions"].append("Q01")
        with patch.object(quiz.json, "loads", return_value=topics), self.assertRaisesRegex(ValueError, "unknown"):
            quiz.load_curriculum(companion, "microsoft.curriculum.json")

    def test_changed_lesson_requires_page_regeneration(self) -> None:
        generated = quiz.generated_files(self.groups)
        generated[quiz.DOCS / "types-lesson.md"] += "changed\n"
        with patch.object(quiz, "generated_files", return_value=generated), \
                patch.object(quiz, "command") as command:
            with self.assertRaisesRegex(ValueError, "Stale generated file"):
                quiz.check(self.groups, no_build=True, selected=None)
            command.assert_not_called()

    def test_changed_source_requires_page_regeneration(self) -> None:
        generated = quiz.generated_files(self.groups)
        path = next(iter(generated))
        generated[path] += "changed\n"
        with patch.object(quiz, "generated_files", return_value=generated), \
                patch.object(quiz, "command") as command:
            with self.assertRaisesRegex(ValueError, "Stale generated file"):
                quiz.check(self.groups, no_build=True, selected=None)
            command.assert_not_called()

    def test_missing_registered_evidence_cannot_pass(self) -> None:
        with patch.object(quiz, "command", return_value="Q01\n"), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "registration mismatch"):
                quiz.check(self.groups, no_build=True, selected=None)

    def test_unrelated_compiler_error_is_not_expected_failure(self) -> None:
        question = next(q for q in self.groups["types"] if q["verification"]["kind"] == "compile-error")
        # A legal control builds, but the negative probe fails because its entry point is absent.
        with patch.object(quiz, "command", side_effect=["Build succeeded", "error CS5001: no Main"]), \
                redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "expected .*got.*CS5001"):
                quiz.verify_compile_errors([question])

    def test_expected_diagnostic_cannot_hide_build_failures(self) -> None:
        question = next(q for q in self.groups["types"] if q["verification"]["kind"] == "compile-error")
        expected = question["verification"]["diagnostics"][0]
        for extra in ("error MSB9999: build failure", "error NETSDK9999: SDK failure",
                      "error NU9999: restore failure", "error : unclassified failure"):
            with self.subTest(extra=extra), \
                    patch.object(quiz, "command", side_effect=["Build succeeded", f"error {expected}: expected\n{extra}"]), \
                    redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "expected .*got"):
                    quiz.verify_compile_errors([question])


if __name__ == "__main__":
    unittest.main(verbosity=2)
