import textwrap
from unittest.mock import Mock
import pytest  # type: ignore


from TermiLINK import (
  load_yaml_data,
  start_rdp_connection,
  platform_check,
  on_tree_double_click,
)


@pytest.fixture
def valid_yaml_file(tmp_path):
    content = "Group1:\n  - name: Server1\n    host: 1.1.1.1"
    file_path = tmp_path / "valid.yaml"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def invalid_yaml_file(tmp_path):
    content = "key: value:"
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


class TestLoadYamlData:
    def test_load_valid_yaml(self, valid_yaml_file):
        data = load_yaml_data(valid_yaml_file)
        expected_data = {'Group1': [{'name': 'Server1', 'host': '1.1.1.1'}]}
        assert data == expected_data

    def test_load_file_not_found(self):
        filepath = "non_existent_file.yaml"
        data = load_yaml_data(filepath)
        assert 'Error' in data
        assert 'が見つかりません' in data['Error'][0]['name']

    def test_load_yaml_error(self, invalid_yaml_file):
        data = load_yaml_data(invalid_yaml_file)
        assert 'Error' in data
        assert 'YAMLの解析に失敗しました' in data['Error'][0]['name']


class TestRdpConnection:
    def test_start_rdp_connection(self, mocker):
        host = "test.server.com"
        user = "testuser"
        rdp_path = "tmp_termilink.rdp"

        mock_exists = mocker.patch(
            'TermiLINK.os.path.exists',
            return_value=True
        )
        mock_remove = mocker.patch('TermiLINK.os.remove')
        mock_popen = mocker.patch('TermiLINK.subprocess.Popen')
        mock_file_open = mocker.patch('builtins.open', mocker.mock_open())

        start_rdp_connection(host, user)

        # Assertions
        mock_file_open.assert_called_once_with(rdp_path, "w", encoding="utf-8")
        handle = mock_file_open()
        expected_content = textwrap.dedent(
            f"""full address:s:{host}
            username:s:{user}
            prompt for credentials:i:0
        """).strip()
        handle.write.assert_called_once_with(expected_content)

        mock_popen.assert_called_once_with(['mstsc', rdp_path])
        mock_exists.assert_called_once_with(rdp_path)
        mock_remove.assert_called_once_with(rdp_path)

    def test_start_rdp_with_no_host(self, mocker):
        mock_popen = mocker.patch('TermiLINK.subprocess.Popen')
        start_rdp_connection("", "user")
        mock_popen.assert_not_called()


@pytest.mark.parametrize(
    "platform_name, should_exit",
    [
        ("Windows", False),
        ("Linux", True),
        ("Darwin", True),
    ],
    ids=["on_windows", "on_linux", "on_macos"]
)
def test_platform_check(mocker, platform_name, should_exit):
    mocker.patch('TermiLINK.platform.system', return_value=platform_name)
    mock_print = mocker.patch('builtins.print')

    if should_exit:
        with pytest.raises(SystemExit):
            platform_check()
        mock_print.assert_called_once()
    else:
        platform_check()
        mock_print.assert_not_called()


class TestGuiInteraction:
    def test_on_tree_double_click(self, mocker):
        mock_start_rdp = mocker.patch('TermiLINK.start_rdp_connection')

        # Mock the event and the tree widget
        mock_event = Mock()
        mock_tree = Mock()
        mock_event.widget = mock_tree

        # Set up the return values for the mocked tree
        item_id = 'item1'
        item_values = ('192.168.1.1', 'test_user')
        mock_tree.selection.return_value = [item_id]
        mock_tree.item.return_value = item_values

        # Call the function to be tested
        on_tree_double_click(mock_event)

        # Assert that the correct functions were called
        mock_tree.item.assert_called_once_with(item_id, 'values')
        mock_start_rdp.assert_called_once_with(item_values[0], item_values[1])

    def test_on_tree_double_click_no_selection(self, mocker):
        mock_start_rdp = mocker.patch('TermiLINK.start_rdp_connection')
        mock_event = Mock()
        mock_tree = Mock()
        mock_event.widget = mock_tree
        mock_tree.selection.return_value = []

        on_tree_double_click(mock_event)

        mock_start_rdp.assert_not_called()
