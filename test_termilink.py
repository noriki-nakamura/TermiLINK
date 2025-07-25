import os
import platform
import tempfile
import textwrap
import unittest
from unittest.mock import patch, mock_open, Mock

from TermiLINK import (
    load_yaml_data,
    start_rdp_connection,
    platform_check,
    on_tree_double_click,
)


class TestLoadYamlData(unittest.TestCase):
    def setUp(self):
        self.valid_yaml_content = "Group1:\n  - name: Server1\n    host: 1.1.1.1"
        self.invalid_yaml_content = "key: value:"

        self.valid_yaml_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, encoding='utf-8', suffix=".yaml"
        )
        self.valid_yaml_file.write(self.valid_yaml_content)
        self.valid_yaml_file.close()

        self.invalid_yaml_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, encoding='utf-8', suffix=".yaml"
        )
        self.invalid_yaml_file.write(self.invalid_yaml_content)
        self.invalid_yaml_file.close()

    def tearDown(self):
        os.remove(self.valid_yaml_file.name)
        os.remove(self.invalid_yaml_file.name)

    def test_load_valid_yaml(self):
        data = load_yaml_data(self.valid_yaml_file.name)
        expected_data = {'Group1': [{'name': 'Server1', 'host': '1.1.1.1'}]}
        self.assertEqual(data, expected_data)

    def test_load_file_not_found(self):
        filepath = "non_existent_file.yaml"
        data = load_yaml_data(filepath)
        self.assertIn('Error', data)
        self.assertIn('が見つかりません', data['Error'][0]['name'])

    def test_load_yaml_error(self):
        data = load_yaml_data(self.invalid_yaml_file.name)
        self.assertIn('Error', data)
        self.assertIn('YAMLの解析に失敗しました', data['Error'][0]['name'])


class TestRdpConnection(unittest.TestCase):
    @patch('TermiLINK.os.path.exists', return_value=True)
    @patch('TermiLINK.os.remove')
    @patch('TermiLINK.subprocess.Popen')
    @patch('builtins.open', new_callable=mock_open)
    def test_start_rdp_connection(self, mock_open, mock_popen, mock_remove, mock_exists):
        host = "test.server.com"
        user = "testuser"
        rdp_path = "tmp_termilink.rdp"

        start_rdp_connection(host, user)

        mock_open.assert_called_once_with(rdp_path, "w", encoding="utf-8")
        handle = mock_open()
        expected_content = textwrap.dedent(
            f"""full address:s:{host}
            username:s:{user}
            prompt for credentials:i:0
        """).strip()
        handle.write.assert_called_once_with(expected_content)

        mock_popen.assert_called_once_with(['mstsc', rdp_path])

        mock_exists.assert_called_once_with(rdp_path)

        mock_remove.assert_called_once_with(rdp_path)

    @patch('TermiLINK.subprocess.Popen')
    def test_start_rdp_with_no_host(self, mock_popen):
        start_rdp_connection("", "user")
        mock_popen.assert_not_called()


class TestPlatformCheck(unittest.TestCase):
    @patch('TermiLINK.platform.system', return_value='Windows')
    def test_platform_check_on_windows(self, mock_system):
        try:
            platform_check()
        except SystemExit:
            self.fail("platform_check() raised SystemExit unexpectedly on Windows")

    @patch('TermiLINK.platform.system', return_value='Linux')
    @patch('builtins.print')
    def test_platform_check_on_non_windows(self, mock_print, mock_system):
        with self.assertRaises(SystemExit):
            platform_check()
        mock_print.assert_called_once()


class TestGuiInteraction(unittest.TestCase):
    @patch('TermiLINK.start_rdp_connection')
    def test_on_tree_double_click(self, mock_start_rdp):
        mock_event = Mock()
        mock_tree = Mock()
        mock_event.widget = mock_tree

        item_id = 'item1'
        item_values = ('192.168.1.1', 'test_user')
        mock_tree.selection.return_value = [item_id]
        mock_tree.item.return_value = item_values

        on_tree_double_click(mock_event)

        mock_tree.item.assert_called_once_with(item_id, 'values')
        mock_start_rdp.assert_called_once_with(item_values[0], item_values[1])

    @patch('TermiLINK.start_rdp_connection')
    def test_on_tree_double_click_no_selection(self, mock_start_rdp):
        mock_event = Mock()
        mock_tree = Mock()
        mock_event.widget = mock_tree
        mock_tree.selection.return_value = []

        on_tree_double_click(mock_event)

        mock_start_rdp.assert_not_called()


if __name__ == '__main__':
    unittest.main()