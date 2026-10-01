"""Regression cases for CI scope and Git event comparisons."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ci_changes.py"
spec = importlib.util.spec_from_file_location("ci_changes", SCRIPT)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class ScopeTests(unittest.TestCase):
    def selected(self, *paths):
        return {name for name, enabled in ci.classify(paths).items() if enabled}

    def test_documentation_does_not_build(self):
        self.assertEqual(self.selected("README.md", "documentation/development.md",
                                       "specimen/README.md", "specimen/PERFORMANCE.md"), set())

    def test_cover_edit_only_renders_artwork(self):
        self.assertEqual(self.selected("scripts/make_specimen_image.py",
                                       "documentation/specimen.svg", "make/artwork.mk"), {"artwork"})

    def test_check_script_does_not_recompile_fonts(self):
        self.assertEqual(self.selected("scripts/check_fonts.py"), {"fonts"})

    def test_source_edit_preserves_rebuild_and_validation(self):
        self.assertEqual(self.selected("sources/Metropolis.glyphs"), {"fonts", "rebuild"})

    def test_font_binary_edit_cannot_bypass_source_comparison(self):
        self.assertEqual(self.selected("fonts/ttf/Metropolis-Regular.ttf"), {"fonts", "rebuild"})

    def test_variable_font_edit_also_refreshes_artwork(self):
        self.assertEqual(self.selected("fonts/variable/Metropolis[wght].ttf"),
                         {"fonts", "rebuild", "artwork"})

    def test_only_site_variable_webfonts_rebuild_the_site(self):
        self.assertEqual(self.selected("fonts/webfonts/Metropolis-Regular.woff2"),
                         {"fonts", "rebuild"})
        self.assertEqual(self.selected("fonts/webfonts/Metropolis[wght].woff2"),
                         {"fonts", "rebuild", "site"})

    def test_site_recipe_and_runtime_do_not_rebuild_fonts(self):
        self.assertEqual(self.selected("make/specimen.mk", ".bun-version",
                                       "specimen/src/css/main.css"), {"site"})

    def test_markdown_and_text_inside_site_source_are_inputs(self):
        self.assertEqual(self.selected("specimen/src/about.md", "specimen/src/data.txt"), {"site"})

    def test_new_build_scripts_and_make_fragments_fail_safe(self):
        self.assertEqual(self.selected("scripts/new_font_step.py", "make/new-font-format.mk"),
                         {"fonts", "rebuild"})

    def test_dependency_scopes(self):
        self.assertEqual(self.selected("requirements-artwork.txt"), {"artwork"})
        self.assertEqual(self.selected("requirements-check.txt"), {"fonts", "rebuild", "artwork"})

    def test_workflow_edit_does_not_force_fontmake(self):
        self.assertEqual(self.selected(".github/workflows/build.yml"), set())


class GitDiffTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(os.chdir, self.cwd)
        self.git("init", "-q")
        self.git("config", "user.name", "CI test")
        self.git("config", "user.email", "ci@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        # Fixture commits must not invoke the developer's global Git hooks.
        self.git("config", "core.hooksPath", str(Path(self.directory.name) / "hooks"))
        self.git("commit", "--allow-empty", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.check_output(["git", *args]).decode().strip()

    def commit(self, path):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("sample")
        self.git("add", "--", path)
        self.git("commit", "-qm", "change")
        return self.git("rev-parse", "HEAD")

    def test_entire_push_not_just_last_commit(self):
        self.commit("sources/Metropolis.glyphs")
        head = self.commit("documentation/cover-city.jpg")
        paths = ci.changed_paths("push", {"before": self.base, "after": head})
        self.assertIn("sources/Metropolis.glyphs", paths)
        self.assertIn("documentation/cover-city.jpg", paths)

    def test_more_than_300_files_and_unusual_names(self):
        for i in range(350):
            Path(f"doc-{i}.md").write_text("text")
        self.git("add", ".")
        head = self.commit("sources/font with\nnewline.glyphs")
        paths = ci.changed_paths("push", {"before": self.base, "after": head})
        self.assertIn("sources/font with\nnewline.glyphs", paths)
        self.assertEqual(len(paths), 351)

    def test_renaming_a_source_keeps_the_deleted_input(self):
        base = self.commit("sources/font.glyphs")
        Path("documentation").mkdir()
        self.git("mv", "sources/font.glyphs", "documentation/font.glyphs")
        self.git("commit", "-qm", "move")
        paths = ci.changed_paths("push", {"before": base, "after": self.git("rev-parse", "HEAD")})
        self.assertIn("sources/font.glyphs", paths)

    def test_force_push_compares_actual_trees(self):
        old = self.commit("documentation/old.md")
        self.git("checkout", "-q", "--detach", self.base)
        new = self.commit("documentation/new.md")
        paths = ci.changed_paths("push", {"before": old, "after": new})
        self.assertEqual(ci.classify(paths), dict.fromkeys(ci.JOBS, False))

    def test_manual_and_new_branch_runs_validate_everything(self):
        self.assertIsNone(ci.changed_paths("workflow_dispatch", {}))
        self.assertIsNone(ci.changed_paths("push", {"before": "0" * 40, "after": self.base}))

    def test_pull_request_uses_merge_base(self):
        head = self.commit("documentation/pr.md")
        self.git("checkout", "-q", "--detach", self.base)
        base = self.commit("sources/main.glyphs")
        paths = ci.changed_paths("pull_request", {"pull_request": {
            "base": {"sha": base}, "head": {"sha": head},
        }})
        self.assertEqual(paths, ["documentation/pr.md"])

    def test_readme_does_not_invalidate_pending_site_deployment(self):
        head = self.commit("README.md")
        self.assertFalse(ci.classify(ci.diff_paths(self.base, head))["site"])

    def test_new_site_inputs_invalidate_pending_deployment(self):
        head = self.commit("specimen/src/index.html")
        self.assertTrue(ci.classify(ci.diff_paths(self.base, head))["site"])


if __name__ == "__main__":
    unittest.main()
