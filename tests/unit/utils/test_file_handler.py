"""Unit tests for FileHandler utility."""

import os
import tempfile
import unittest
from pathlib import Path

from src.utils.file_handler import FileHandler


class TestFileHandler(unittest.TestCase):
    """Test cases for FileHandler utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        self.test_content = "This is test content."
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_directory_exists_creates_new(self):
        """Test ensure_directory_exists creates new directory."""
        new_dir = os.path.join(self.temp_dir, "new_directory")
        self.assertFalse(os.path.exists(new_dir))
        
        result = FileHandler.ensure_directory_exists(new_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
    
    def test_ensure_directory_exists_existing(self):
        """Test ensure_directory_exists with existing directory."""
        result = FileHandler.ensure_directory_exists(self.temp_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_ensure_directory_exists_nested(self):
        """Test ensure_directory_exists creates nested directories."""
        nested_dir = os.path.join(self.temp_dir, "level1", "level2", "level3")
        
        result = FileHandler.ensure_directory_exists(nested_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.isdir(nested_dir))
    
    def test_read_text_file_existing(self):
        """Test read_text_file with existing file."""
        # Create test file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        result = FileHandler.read_text_file(self.test_file)
        
        self.assertEqual(result, self.test_content)
    
    def test_read_text_file_nonexistent(self):
        """Test read_text_file with non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        
        result = FileHandler.read_text_file(nonexistent_file)
        
        self.assertIsNone(result)
    
    def test_read_text_file_different_encoding(self):
        """Test read_text_file with different encoding."""
        content = "Test content with special chars: éñ"
        
        # Write with latin-1 encoding
        with open(self.test_file, 'w', encoding='latin-1') as f:
            f.write(content)
        
        result = FileHandler.read_text_file(self.test_file, encoding='latin-1')
        
        self.assertEqual(result, content)
    
    def test_write_text_file_new(self):
        """Test write_text_file creates new file."""
        result = FileHandler.write_text_file(self.test_file, self.test_content)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_file))
        
        # Verify content
        with open(self.test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, self.test_content)
    
    def test_write_text_file_overwrite(self):
        """Test write_text_file overwrites existing file."""
        # Create initial file
        initial_content = "Initial content"
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        new_content = "New content"
        result = FileHandler.write_text_file(self.test_file, new_content)
        
        self.assertTrue(result)
        
        # Verify content was overwritten
        with open(self.test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, new_content)
    
    def test_write_text_file_creates_directory(self):
        """Test write_text_file creates parent directory."""
        nested_file = os.path.join(self.temp_dir, "subdir", "nested_file.txt")
        
        result = FileHandler.write_text_file(nested_file, self.test_content)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_file))
        self.assertTrue(os.path.exists(os.path.dirname(nested_file)))
    
    def test_append_text_file_existing(self):
        """Test append_text_file appends to existing file."""
        # Create initial file
        initial_content = "Initial content"
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        append_content = " Appended content"
        result = FileHandler.append_text_file(self.test_file, append_content)
        
        self.assertTrue(result)
        
        # Verify content was appended
        with open(self.test_file, 'r', encoding='utf-8') as f:
            final_content = f.read()
        
        self.assertEqual(final_content, initial_content + append_content)
    
    def test_append_text_file_new(self):
        """Test append_text_file creates new file."""
        result = FileHandler.append_text_file(self.test_file, self.test_content)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_file))
        
        # Verify content
        with open(self.test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, self.test_content)
    
    def test_copy_file_success(self):
        """Test copy_file successfully copies file."""
        # Create source file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        destination = os.path.join(self.temp_dir, "copied_file.txt")
        result = FileHandler.copy_file(self.test_file, destination)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(destination))
        
        # Verify both files exist with same content
        self.assertTrue(os.path.exists(self.test_file))
        with open(destination, 'r', encoding='utf-8') as f:
            copied_content = f.read()
        
        self.assertEqual(copied_content, self.test_content)
    
    def test_copy_file_creates_directory(self):
        """Test copy_file creates destination directory."""
        # Create source file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        destination = os.path.join(self.temp_dir, "subdir", "copied_file.txt")
        result = FileHandler.copy_file(self.test_file, destination)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(destination))
        self.assertTrue(os.path.exists(os.path.dirname(destination)))
    
    def test_copy_file_nonexistent_source(self):
        """Test copy_file with non-existent source file."""
        nonexistent_source = os.path.join(self.temp_dir, "nonexistent.txt")
        destination = os.path.join(self.temp_dir, "destination.txt")
        
        result = FileHandler.copy_file(nonexistent_source, destination)
        
        self.assertFalse(result)
        self.assertFalse(os.path.exists(destination))
    
    def test_move_file_success(self):
        """Test move_file successfully moves file."""
        # Create source file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        destination = os.path.join(self.temp_dir, "moved_file.txt")
        result = FileHandler.move_file(self.test_file, destination)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(destination))
        self.assertFalse(os.path.exists(self.test_file))
        
        # Verify content
        with open(destination, 'r', encoding='utf-8') as f:
            moved_content = f.read()
        
        self.assertEqual(moved_content, self.test_content)
    
    def test_move_file_creates_directory(self):
        """Test move_file creates destination directory."""
        # Create source file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        destination = os.path.join(self.temp_dir, "subdir", "moved_file.txt")
        result = FileHandler.move_file(self.test_file, destination)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(destination))
        self.assertTrue(os.path.exists(os.path.dirname(destination)))
        self.assertFalse(os.path.exists(self.test_file))
    
    def test_delete_file_existing(self):
        """Test delete_file removes existing file."""
        # Create test file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        self.assertTrue(os.path.exists(self.test_file))
        
        result = FileHandler.delete_file(self.test_file)
        
        self.assertTrue(result)
        self.assertFalse(os.path.exists(self.test_file))
    
    def test_delete_file_nonexistent(self):
        """Test delete_file with non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        
        result = FileHandler.delete_file(nonexistent_file)
        
        self.assertTrue(result)  # Should still return True
    
    def test_delete_directory_empty(self):
        """Test delete_directory removes empty directory."""
        empty_dir = os.path.join(self.temp_dir, "empty_dir")
        os.makedirs(empty_dir)
        
        self.assertTrue(os.path.exists(empty_dir))
        
        result = FileHandler.delete_directory(empty_dir)
        
        self.assertTrue(result)
        self.assertFalse(os.path.exists(empty_dir))
    
    def test_delete_directory_recursive(self):
        """Test delete_directory removes directory recursively."""
        nested_dir = os.path.join(self.temp_dir, "parent", "child")
        os.makedirs(nested_dir)
        
        # Create a file in nested directory
        nested_file = os.path.join(nested_dir, "file.txt")
        with open(nested_file, 'w') as f:
            f.write("content")
        
        parent_dir = os.path.join(self.temp_dir, "parent")
        result = FileHandler.delete_directory(parent_dir, recursive=True)
        
        self.assertTrue(result)
        self.assertFalse(os.path.exists(parent_dir))
    
    def test_get_file_size_existing(self):
        """Test get_file_size returns correct size for existing file."""
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
        
        expected_size = len(self.test_content.encode('utf-8'))
        result = FileHandler.get_file_size(self.test_file)
        
        self.assertEqual(result, expected_size)
    
    def test_get_file_size_nonexistent(self):
        """Test get_file_size returns None for non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        
        result = FileHandler.get_file_size(nonexistent_file)
        
        self.assertIsNone(result)
    
    def test_list_files_existing_directory(self):
        """Test list_files returns files in directory."""
        # Create test files
        file1 = os.path.join(self.temp_dir, "file1.txt")
        file2 = os.path.join(self.temp_dir, "file2.py")
        subdir = os.path.join(self.temp_dir, "subdir")
        
        with open(file1, 'w') as f:
            f.write("content1")
        with open(file2, 'w') as f:
            f.write("content2")
        os.makedirs(subdir)
        
        result = FileHandler.list_files(self.temp_dir)
        
        self.assertIn(file1, result)
        self.assertIn(file2, result)
        self.assertNotIn(subdir, result)  # Directories should not be included
    
    def test_list_files_with_pattern(self):
        """Test list_files with pattern filter."""
        # Create test files
        txt_file = os.path.join(self.temp_dir, "file.txt")
        py_file = os.path.join(self.temp_dir, "file.py")
        
        with open(txt_file, 'w') as f:
            f.write("content1")
        with open(py_file, 'w') as f:
            f.write("content2")
        
        result = FileHandler.list_files(self.temp_dir, "*.txt")
        
        self.assertIn(txt_file, result)
        self.assertNotIn(py_file, result)
    
    def test_list_files_nonexistent_directory(self):
        """Test list_files returns empty list for non-existent directory."""
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        
        result = FileHandler.list_files(nonexistent_dir)
        
        self.assertEqual(result, [])
    
    def test_get_file_extension(self):
        """Test get_file_extension returns correct extension."""
        self.assertEqual(FileHandler.get_file_extension("file.txt"), ".txt")
        self.assertEqual(FileHandler.get_file_extension("file.tar.gz"), ".gz")
        self.assertEqual(FileHandler.get_file_extension("file"), "")
        self.assertEqual(FileHandler.get_file_extension("/path/to/file.py"), ".py")
    
    def test_get_filename_without_extension(self):
        """Test get_filename_without_extension returns correct name."""
        self.assertEqual(FileHandler.get_filename_without_extension("file.txt"), "file")
        self.assertEqual(FileHandler.get_filename_without_extension("file.tar.gz"), "file.tar")
        self.assertEqual(FileHandler.get_filename_without_extension("file"), "file")
        self.assertEqual(FileHandler.get_filename_without_extension("/path/to/file.py"), "file")
    
    def test_create_unique_filename_nonexistent(self):
        """Test create_unique_filename returns original name if file doesn't exist."""
        nonexistent_file = os.path.join(self.temp_dir, "unique.txt")
        
        result = FileHandler.create_unique_filename(nonexistent_file)
        
        self.assertEqual(result, nonexistent_file)
    
    def test_create_unique_filename_existing(self):
        """Test create_unique_filename creates unique name for existing file."""
        # Create test file
        with open(self.test_file, 'w') as f:
            f.write("content")
        
        result = FileHandler.create_unique_filename(self.test_file)
        
        self.assertNotEqual(result, self.test_file)
        self.assertIn("test_file_1.txt", result)
        self.assertFalse(os.path.exists(result))
    
    def test_create_unique_filename_multiple_existing(self):
        """Test create_unique_filename handles multiple existing files."""
        base_name = os.path.join(self.temp_dir, "test.txt")
        
        # Create original and first duplicate
        with open(base_name, 'w') as f:
            f.write("content")
        
        dup1_name = os.path.join(self.temp_dir, "test_1.txt")
        with open(dup1_name, 'w') as f:
            f.write("content")
        
        result = FileHandler.create_unique_filename(base_name)
        
        expected = os.path.join(self.temp_dir, "test_2.txt")
        self.assertEqual(result, expected)
        self.assertFalse(os.path.exists(result))
    
    def test_is_file_writable_existing_writable(self):
        """Test is_file_writable returns True for writable existing file."""
        with open(self.test_file, 'w') as f:
            f.write("content")
        
        result = FileHandler.is_file_writable(self.test_file)
        
        self.assertTrue(result)
    
    def test_is_file_writable_nonexistent_in_writable_dir(self):
        """Test is_file_writable returns True for non-existent file in writable directory."""
        nonexistent_file = os.path.join(self.temp_dir, "new_file.txt")
        
        result = FileHandler.is_file_writable(nonexistent_file)
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()