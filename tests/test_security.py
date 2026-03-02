#!/usr/bin/env python3
"""安全功能测试用例"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

import create_doc
import import_docs
import export_docs


class TestResolveSafePath(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.allowed_file = self.test_dir / "allowed.md"
        self.allowed_file.write_text('# Test')
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_path_traversal_attack(self):
        """测试：目录遍历攻击 - 应拒绝"""
        old_env = os.environ.get('OPENCLAW_WORKSPACE')
        try:
            os.environ['OPENCLAW_WORKSPACE'] = str(self.test_dir)
            with self.assertRaises(ValueError):
                import_docs.resolve_safe_path("../etc/passwd")
        finally:
            if old_env: os.environ['OPENCLAW_WORKSPACE'] = old_env
            else: os.environ.pop('OPENCLAW_WORKSPACE', None)
    
    def test_absolute_path_outside_root(self):
        """测试：绝对路径超出允许范围 - 应拒绝"""
        old_env = os.environ.get('OPENCLAW_WORKSPACE')
        try:
            os.environ['OPENCLAW_WORKSPACE'] = str(self.test_dir)
            with self.assertRaises(ValueError):
                import_docs.resolve_safe_path("/etc/passwd")
        finally:
            if old_env: os.environ['OPENCLAW_WORKSPACE'] = old_env
            else: os.environ.pop('OPENCLAW_WORKSPACE', None)


class TestFileExtensionValidation(unittest.TestCase):
    def test_allowed_extensions(self):
        for ext in ['.md', '.txt', '.markdown']:
            self.assertTrue(import_docs.validate_file_extension(f"test{ext}"))
    
    def test_disallowed_extensions(self):
        for ext in ['.exe', '.sh', '.py', '.pdf']:
            self.assertFalse(import_docs.validate_file_extension(f"test{ext}"))


class TestFileSizeValidation(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_small_file(self):
        small_file = self.test_dir / "small.md"
        small_file.write_text("# Small")
        self.assertTrue(import_docs.validate_file_size(small_file))
    
    def test_large_file(self):
        large_file = self.test_dir / "large.md"
        with open(large_file, 'w') as f:
            f.write('x' * (11 * 1024 * 1024))
        self.assertFalse(import_docs.validate_file_size(large_file))


class TestDocUrlValidation(unittest.TestCase):
    def test_invalid_url(self):
        """测试：无效的文档 URL 应被拒绝"""
        for url in ["https://alidocs.dingtalk.com/i/nodes/short", "not a url"]:
            result = export_docs.extract_doc_uuid(url)
            self.assertIsNone(result, f"URL 应该无效：{url}")


class TestRunMcporter(unittest.TestCase):
    def test_successful_command(self):
        success, output = import_docs.run_mcporter(['echo', 'test'])
        self.assertTrue(success)
        self.assertIn('test', output)
    
    def test_timeout(self):
        success, output = import_docs.run_mcporter(['sleep', '10'], timeout=1)
        self.assertFalse(success)
        self.assertIn('超时', output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
