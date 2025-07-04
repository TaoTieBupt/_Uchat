# common/config.py
import json

def get_config():
    """读取并返回 config.json 的内容"""
    with open('config.json', 'r') as f:
        return json.load(f)