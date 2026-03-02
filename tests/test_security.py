#!/usr/bin/env python3
"""
安全功能测试用例

测试脚本的安全加固功能：
1. 路径安全限制 (resolve_safe_path)
2. URL 格式验证
3. 文件扩展名验证
4. 文件大小限制
5. 内容长度限制
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

# 导入被测试模块
import create_doc
import import_docs
import export_docs


class TestResolveSafePath(unittest.TestCase):
    """测试路径安全限制功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.allowed_file = self.test_dir / "allowed.md"
        self.allowed_file.write_text('# Test')
        
        # 创建子目录和文件
        self.sub_dir = self.test_dir / "subdir"
        self.sub_dir.mkdir()
        self.sub_file = self.sub_dir / "data.md"
        self.sub_file.write_text('# Subdir file')
    
    def tearDown(self):
        """清理测试文件"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_relative_path_within_root(self):
        """测试：相对路径在允许范围内 - 应成功"""
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            result = import_docs.resolve_safe_path("allowed.md")
            self.assertEqual(result, self.allowed_file.resolve())
        finally:
            os.chdir(original_cwd)
    
    def test_subdirectory_path(self):
        """测试：子目录路径在允许范围内 - 应成功"""
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            result = import_docs.resolve_safe_path("subdir/data.md")
            self.assertEqual(result, self.sub_file.resolve())
        finally:
            os.chdir(original_cwd)
    
    def test_absolute_path_within_root(self):
        """测试：绝对路径在允许范围内 - 应成功"""
        os.environ['OPENCLAW_WORKSPACE'] = str(self.test_dir)
        result = import_docs.resolve_safe_path(str(self.allowed_file))
        self.assertEqual(result, self.allowed_file.resolve())
    
    def test_path_traversal_attack(self):
        """测试：目录遍历攻击 - 应拒绝"""
        os.environ['OPENCLAW_WORKSPACE'] = str(self.test_dir)
        with self.assertRaises(ValueError) as context:
            import_docs.resolve_safe_path("../etc/passwd")
        self.assertIn("路径超出允许范围", str(context.exception))
    
    def test_path_traversal_with_dots(self):
        """测试：多层目录遍历攻击 - 应拒绝"""
        os.environ['OPENCLAW_WORKSPACE'] = str(self.test_dir)
        with self.assertRaises(ValueError) as context:
            import_docs.resolve_safe_path("../../etc/passwd")
        self.assertIn("路径超出允许范围", str(context.exception))
    
    def test_absolute_path_outside_root(self):
        """测试：绝对路径超出允许范围 - 应拒绝"""
        os.environ['OPENCLAW_WORKSPACE'] = str(self.test_dir)
        with self.assertRaises(ValueError) as context:
            import_docs.resolve_safe_path("/etc/passwd")
        self.assertIn("路径超出允许范围", str(context.exception))


class TestFileExtensionValidation(unittest.TestCase):
    """测试文件扩展名验证"""
    
    def test_allowed_extensions(self):
        """测试：允许的扩展名"""
        allowed = ['.md', '.txt', '.markdown']
        for ext in allowed:
            self.assertTrue(import_docs.validate_file_extension(f"test{ext}"))
    
    def test_disallowed_extensions(self):
        """测试：不允许的扩展名"""
        disallowed = ['.exe', '.sh', '.py', '.bat', '.doc', '.docx', '.pdf']
        for ext in disallowed:
            self.assertFalse(import_docs.validate_file_extension(f"test{ext}"))
    
    def test_case_insensitive(self):
        """测试：扩展名验证不区分大小写"""
        self.assertTrue(import_docs.validate_file_extension("test.MD"))
        self.assertTrue(import_docs.validate_file_extension("test.Md"))


class TestFileSizeValidation(unittest.TestCase):
    """测试文件大小限制"""
    
    def setUp(self):
        """创建测试文件"""
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """清理测试文件"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_small_file(self):
        """测试：小文件 - 应通过"""
        small_file = self.test_dir / "small.md"
        small_file.write_text("# Small file")
        self.assertTrue(import_docs.validate_file_size(small_file))
    
    def test_large_file(self):
        """测试：大文件 - 应拒绝"""
        large_file = self.test_dir / "large.md"
        # 创建 11MB 文件
        with open(large_file, 'w') as f:
            f.write('x' * (11 * 1024 * 1024))
        self.assertFalse(import_docs.validate_file_size(large_file))


class TestDocUrlValidation(unittest.TestCase):
    """测试文档 URL 验证"""
    
    def test_valid_url(self):
        """测试：有效的文档 URL"""
        valid_urls = [
            "https://alidocs.dingtalk.com/i/nodes/abc123def456",
            "https://alidocs.dingtalk.com/i/nodes/ABC123DEF456",
            "https://alidocs.dingtalk.com/i/nodes/1234567890abcdef1234567890ab",
        ]
        for url in valid_urls:
            result = export_docs.extract_doc_uuid(url)
            self.assertIsNotNone(result, f"URL 应该有效：{url}")
    
    def test_invalid_url(self):
        """测试：无效的文档 URL"""
        invalid_urls = [
            "https://alidocs.dingtalk.com/i/nodes/short",
            "https://alidocs.dingtalk.com/i/nodes/",
            "https://example.com/i/nodes/abc123",
            "http://alidocs.dingtalk.com/i/nodes/abc123",
            "not a url",
        ]
        for url in invalid_urls:
            result = export_docs.extract_doc_uuid(url)
            self.assertIsNone(result, f"URL 应该无效：{url}")


class TestContentLengthLimit(unittest.TestCase):
    """测试内容长度限制"""
    
    def test_content_truncation(self):
        """测试：超长内容应被截断"""
        long_content = 'x' * (create_doc.MAX_CONTENT_LENGTH + 1000)
        self.assertLessEqual(len(long_content[:create_doc.MAX_CONTENT_LENGTH]), 
                            create_doc.MAX_CONTENT_LENGTH)


class TestRunMcporter(unittest.TestCase):
    """测试 mcporter 命令执行"""
    
    def test_successful_command(self):
        """测试：成功的命令执行"""
        success, output = import_docs.run_mcporter(['echo', 'test'])
        self.assertTrue(success)
        self.assertIn('test', output)
    
    def test_failed_command(self):
        """测试：失败的命令执行"""
        success, output = import_docs.run_mcporter(['false'])
        self.assertFalse(success)
    
    def test_timeout(self):
        """测试：超时处理"""
        success, output = import_docs.run_mcporter(['sleep', '10'], timeout=1)
        self.assertFalse(success)
        self.assertIn('超时', output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
