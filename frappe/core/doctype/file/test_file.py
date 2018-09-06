# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import os
import unittest
from frappe import _
from frappe.core.doctype.file.file import move_file, get_files_path
# test_records = frappe.get_test_records('File')

test_content1 = 'Hello'
test_content2 = 'Hello World'

def make_test_doc():
	d = frappe.new_doc('ToDo')
	d.description = 'Test'
	d.save()
	return d.doctype, d.name


class TestSimpleFile(unittest.TestCase):

	def setUp(self):
		self.attached_to_doctype, self.attached_to_docname = make_test_doc()
		self.test_content = test_content1
		_file = frappe.get_doc({"doctype": "File",
			"file_name": "hello.txt",
			"attached_to_doctype": self.attached_to_doctype,
			"attached_to_name": self.attached_to_docname})
		self.saved_file = _file.save_file(content=self.test_content)
		self.saved_filename = get_files_path(self.saved_file.file_name)

	def test_save(self):
		_file = frappe.get_doc("File", {"file_name": self.saved_file.file_name})
		content = _file.get_content()
		self.assertEqual(content, self.test_content)

	def tearDown(self):
		# File gets deleted on rollback, so blank
		pass


class TestSameFileName(unittest.TestCase):

	def setUp(self):
		self.attached_to_doctype, self.attached_to_docname = make_test_doc()
		self.test_content1 = test_content1
		self.test_content2 = test_content2
		_file1 = frappe.get_doc({"doctype": "File",
			"file_name": "hello.txt",
			"attached_to_doctype": self.attached_to_doctype,
			"attached_to_name": self.attached_to_docname})
		_file2 = frappe.get_doc({"doctype": "File",
			"file_name": "hello.txt",
			"attached_to_doctype": self.attached_to_doctype,
			"attached_to_name": self.attached_to_docname})
		self.saved_file1 = _file1.save_file(content=self.test_content1)
		self.saved_file2 = _file2.save_file(content=self.test_content2)
		self.saved_filename1 = get_files_path(self.saved_file1.file_name)
		self.saved_filename2 = get_files_path(self.saved_file2.file_name)

	def test_saved_content(self):
		_file = frappe.get_doc("File", {"file_name": self.saved_file1.file_name})
		content1 = _file.get_content()
		self.assertEqual(content1, self.test_content1)
		_file = frappe.get_doc("File", {"file_name": self.saved_file2.file_name})
		content2 = _file.get_content()
		self.assertEqual(content2, self.test_content2)

	def tearDown(self):
		# File gets deleted on rollback, so blank
		pass


class TestSameContent(unittest.TestCase):

	def setUp(self):
		self.attached_to_doctype1, self.attached_to_docname1 = make_test_doc()
		self.attached_to_doctype2, self.attached_to_docname2 = make_test_doc()
		self.test_content1 = test_content1
		self.test_content2 = test_content1
		self.orig_filename = 'hello.txt'
		self.dup_filename = 'hello2.txt'
		_file1 = frappe.get_doc({"doctype": "File",
			"file_name": self.orig_filename,
			"attached_to_doctype": self.attached_to_doctype1,
			"attached_to_name": self.attached_to_docname1})
		_file2 = frappe.get_doc({"doctype": "File",
			"file_name": self.dup_filename,
			"attached_to_doctype": self.attached_to_doctype2,
			"attached_to_name": self.attached_to_docname2})
		self.saved_file1 = _file1.save_file(content=self.test_content1)
		self.saved_file2 = _file2.save_file(content=self.test_content2)
		self.saved_filename1 = get_files_path(self.saved_file1.file_name)
		self.saved_filename2 = get_files_path(self.saved_file2.file_name)

	def test_saved_content(self):
		_file1 = frappe.get_doc("File", {"file_name": self.saved_file1.file_name})
		filename1 =  _file1.file_name
		_file2 = frappe.get_doc("File", {"file_name": self.saved_file2.file_name})
		filename2 =  _file2.file_name
		self.assertEqual(filename1, filename2)
		self.assertFalse(os.path.exists(get_files_path(self.dup_filename)))

	def tearDown(self):
		# File gets deleted on rollback, so blank
		pass

class TestFile(unittest.TestCase):
	def setUp(self):
		self.delete_test_data()
		self.upload_file()

	def tearDown(self):
		try:
			frappe.get_doc("File", {"file_name": "file_copy.txt"}).delete()
		except frappe.DoesNotExistError:
			pass

	def delete_test_data(self):
		for f in frappe.db.sql('''select name, file_name from tabFile where
			is_home_folder = 0 and is_attachments_folder = 0 order by rgt-lft asc'''):
			frappe.delete_doc("File", f[0])

	def upload_file(self):
		_file = frappe.get_doc({"doctype": "File",
			"file_name": "file_copy.txt",
			"attached_to_name": "",
			"attached_to_doctype": "",
			"folder": self.get_folder("Test Folder 1", "Home").name})
		self.saved_file = _file.save_file(content="Testing file copy example.")
		self.saved_filename = get_files_path(self.saved_file.file_name)

	def get_folder(self, folder_name, parent_folder="Home"):
		return frappe.get_doc({
			"doctype": "File",
			"file_name": _(folder_name),
			"is_folder": 1,
			"folder": _(parent_folder)
		}).insert()

	def tests_after_upload(self):
		self.assertEqual(self.saved_file.folder, _("Home/Test Folder 1"))

		folder_size = frappe.db.get_value("File", _("Home/Test Folder 1"), "file_size")
		saved_file_size = frappe.db.get_value("File", self.saved_file.name, "file_size")

		self.assertEqual(folder_size, saved_file_size)

	def test_file_copy(self):
		folder = self.get_folder("Test Folder 2", "Home")

		file = frappe.get_doc("File", {"file_name": "file_copy.txt"})
		move_file([{"name": file.name}], folder.name, file.folder)
		file = frappe.get_doc("File", {"file_name": "file_copy.txt"})

		self.assertEqual(_("Home/Test Folder 2"), file.folder)
		self.assertEqual(frappe.db.get_value("File", _("Home/Test Folder 2"), "file_size"), file.file_size)
		self.assertEqual(frappe.db.get_value("File", _("Home/Test Folder 1"), "file_size"), 0)

	def test_folder_copy(self):
		folder = self.get_folder("Test Folder 2", "Home")
		folder = self.get_folder("Test Folder 3", "Home/Test Folder 2")
		_file = frappe.get_doc({"doctype": "File",
			"file_name": "folder_copy.txt",
			"attached_to_name": "",
			"attached_to_doctype": "",
			"folder": folder.name})
		self.saved_file = _file.save_file(content="Testing folder copy example")

		move_file([{"name": folder.name}], 'Home/Test Folder 1', folder.folder)

		file = frappe.get_doc("File", {"file_name":"folder_copy.txt"})
		file_copy_txt = frappe.get_value("File", {"file_name":"file_copy.txt"})
		if file_copy_txt:
			frappe.get_doc("File", file_copy_txt).delete()

		self.assertEqual(_("Home/Test Folder 1/Test Folder 3"), file.folder)
		self.assertEqual(frappe.db.get_value("File", _("Home/Test Folder 1"), "file_size"), file.file_size)
		self.assertEqual(frappe.db.get_value("File", _("Home/Test Folder 2"), "file_size"), 0)

	def test_non_parent_folder(self):
		d = frappe.get_doc({
			"doctype": "File",
			"file_name": _("Test_Folder"),
			"is_folder": 1
		})

		self.assertRaises(frappe.ValidationError, d.save)

	def test_on_delete(self):
		file = frappe.get_doc("File", {"file_name": "file_copy.txt"})
		file.delete()

		self.assertEqual(frappe.db.get_value("File", _("Home/Test Folder 1"), "file_size"), 0)

		folder = self.get_folder("Test Folder 3", "Home/Test Folder 1")
		_file = frappe.get_doc({"doctype": "File",
			"file_name": "folder_copy.txt",
			"attached_to_name": "",
			"attached_to_doctype": "",
			"folder": folder.name})
		self.saved_file = _file.save_file(content="Testing folder copy example")

		folder = frappe.get_doc("File", "Home/Test Folder 1/Test Folder 3")
		self.assertRaises(frappe.ValidationError, folder.delete)

	def test_file_upload_limit(self):
		from frappe.core.doctype.file.file import MaxFileSizeReachedError
		from frappe.limits import update_limits, clear_limit
		from frappe import _dict

		update_limits({
			'space': 1,
			'space_usage': {
				'files_size': (1024 ** 2),
				'database_size': 0,
				'backup_size': 0,
				'total': (1024 ** 2)
			}
		})

		# Rebuild the frappe.local.conf to take up the changes from site_config
		frappe.local.conf = _dict(frappe.get_site_config())

		_file = frappe.get_doc({"doctype": "File",
			"file_name": "_test_max_space.txt",
			"attached_to_name": "",
			"attached_to_doctype": "",
			"folder": self.get_folder("Test Folder 2", "Home").name})
		self.assertRaises(MaxFileSizeReachedError,
			_file.save_file, content="This file tests for max space usage")

		# Scrub the site_config and rebuild frappe.local.conf
		clear_limit("space")
		frappe.local.conf = _dict(frappe.get_site_config())
