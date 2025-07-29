import argparse
import os
import time
import textwrap
import tkinter as tk
from tkinter import ttk
import yaml  # type: ignore
import subprocess
import platform
import tempfile
import sys


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def initialize_window():
    window = tk.Tk()
    window.title("TermiLink")
    window.geometry("500x400")
    icon_path = get_resource_path("TermiLINK.ico")
    if os.path.exists(icon_path):
        window.iconbitmap(icon_path)

    tree = ttk.Treeview(
        window,
        columns=('host'),
        show='tree headings'
    )
    tree.pack(fill=tk.BOTH, expand=True)
    tree.bind("<Double-1>", on_tree_double_click)

    tree.column('#0', width=100, minwidth=60, stretch=tk.YES)
    tree.heading('#0', text='名前', anchor=tk.W)
    tree.column('host', width=200, minwidth=80, stretch=tk.YES, anchor=tk.W)
    tree.heading('host', text='ホスト', anchor=tk.W)

    return (window, tree)


def load_yaml_data(filepath: str) -> dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {'Error': [{'name': f'{filepath} が見つかりません。', 'host': ''}]}
    except yaml.YAMLError as e:
        return {'Error': [{'name': f'YAMLの解析に失敗しました: {e}', 'host': ''}]}
    except Exception as e:
        return {'Error': [{'name': f'予期せぬエラーが発生しました: {e}', 'host': ''}]}


def populate_tree_recursive(tree: ttk.Treeview, parent_id: str, data: list):
    if not isinstance(data, list):
        return

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        if 'name' in item:
            item_name = item.get('name', 'N/A')
            item_host = item.get('host', '')
            item_user = item.get('user', 'Administrator')
            item_id = f"{parent_id}_{i}"
            tree.insert(
                parent=parent_id,
                index='end',
                iid=item_id,
                text=item_name,
                values=(item_host, item_user)
            )
        else:
            for group_name, sub_items in item.items():
                sub_group_id = f"{parent_id}_{group_name}"
                sub_group_node = tree.insert(
                    parent=parent_id,
                    index='end',
                    iid=sub_group_id,
                    text=group_name,
                    open=True
                )
                populate_tree_recursive(tree, sub_group_node, sub_items)


def populate_tree(tree: ttk.Treeview, data: dict):
    for item in tree.get_children():
        tree.delete(item)

    for group_name, items in data.items():
        parent_node = tree.insert(
            parent='',
            index='end',
            iid=group_name,
            text=group_name,
            open=True
        )
        populate_tree_recursive(tree, parent_node, items)


def platform_check():
    if platform.system() != "Windows":
        print(f'{"Error: This program running for Windows only."}')
        exit()


def start_rdp_connection(host: str, user: str):
    if not host:
        return

    rdp_content = textwrap.dedent(
        f"""full address:s:{host}
            username:s:{user}
            prompt for credentials:i:0
        """).strip()

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.rdp',
        delete=False,
        encoding='utf-8'
    ) as rdp_file:
        rdp_config_path = rdp_file.name
        rdp_file.write(rdp_content)
    try:
        subprocess.Popen(['mstsc', rdp_config_path])
        time.sleep(1)
    except FileNotFoundError:
        print(f'{"Error: mstsc command not found."}')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if os.path.exists(rdp_config_path):
            os.remove(rdp_config_path)


def on_tree_double_click(event):
    tree = event.widget
    selection = tree.selection()
    if selection:
        item_id = selection[0]
        connect_info = tree.item(item_id, 'values')
        start_rdp_connection(connect_info[0], connect_info[1])


def parse_argument():
    parser = argparse.ArgumentParser(
                        description='TermiLink: RDP Teminal Link tool')
    parser.add_argument('-c', '--config',
                        help='Config file path',
                        default='config.yaml')
    return parser.parse_args()


if __name__ == "__main__":
    platform_check()
    args = parse_argument()
    window, tree = initialize_window()

    yaml_data = load_yaml_data(args.config)
    populate_tree(tree, yaml_data)

    window.mainloop()
