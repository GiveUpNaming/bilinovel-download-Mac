import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from frontend import cfg_utils


class ConfigMigrationTest(unittest.TestCase):
    def test_initialize_adds_browser_without_overwriting_existing_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'config.db')
            with sqlite3.connect(db_path) as connection:
                connection.execute(cfg_utils.CREATE_CONFIG_TABLE_SQL)
                connection.execute(
                    "INSERT INTO config (KEY, VALUE) VALUES (?, ?)",
                    ('theme', 'Dark'),
                )

            with patch.object(cfg_utils, 'DBPATH', db_path):
                cfg_utils.initialize_db()
                self.assertEqual(cfg_utils.read_config_dict('theme'), 'Dark')
                self.assertEqual(cfg_utils.read_config_dict('browser'), 'Auto')


if __name__ == '__main__':
    unittest.main()
