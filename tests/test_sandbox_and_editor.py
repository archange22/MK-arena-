import pytest
import os
from coding.editor import CodeEditor
from coding.analyzer import CodeAnalyzer
from coding.generator import CodeGenerator
from coding.sandbox import Sandbox

def test_analyzer_scan():
    analyzer = CodeAnalyzer('/tmp/MK-arena-')
    scan = analyzer.scan_directory()
    assert scan["total_python_files"] > 10
    assert any("ai.engine" in m for m in scan["modules"])

def test_code_generator():
    gen = CodeGenerator()
    fn = gen.generate_function("calculer_points", ["score", "bonus"], "Calcule le total", "return score + bonus")
    assert "def calculer_points(score, bonus):" in fn
    assert "return score + bonus" in fn

def test_editor_and_rollback():
    editor = CodeEditor('/tmp/MK-arena-')
    test_file = "features/temp_test.py"
    success, msg = editor.write_file(test_file, "# initial content\ndef initial(): pass\n")
    assert success is True

    # Patch
    patch_ok, _ = editor.patch_line(test_file, "pass", "return 42")
    assert patch_ok is True

    # Rollback
    rb_ok, _ = editor.rollback(test_file)
    assert rb_ok is True

    full_path = os.path.join('/tmp/MK-arena-', test_file)
    with open(full_path) as f:
        content = f.read()
    assert "pass" in content
    os.remove(full_path)
