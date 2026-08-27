"""博客文章。标题到路径片段的转换在本模块已有实现。"""

import re

_SEPARATORS = re.compile(r"[^a-z0-9]+")


def to_url_key(title: str) -> str:
    """把标题转换成 URL 安全的路径片段。

    项目惯例：全部小写、非字母数字折叠成单个连字符、去掉首尾连字符、
    空标题回退为 "untitled"。
    """
    folded = _SEPARATORS.sub("-", title.strip().lower()).strip("-")
    return folded or "untitled"


class Post:
    def __init__(self, title: str) -> None:
        self.title = title

    @property
    def path(self) -> str:
        return f"/blog/{to_url_key(self.title)}"
