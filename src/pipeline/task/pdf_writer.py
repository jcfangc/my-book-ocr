from pathlib import Path
from typing import Iterable

from src.definition.p_model.md import MarkdownElement


def write_markdown_file(elements: Iterable[MarkdownElement], output_path: Path) -> None:
    """
    将 MarkdownElement 序列写入指定 Markdown 文件。

    Args:
        elements (Iterable[MarkdownElement]): Markdown 元素列表或生成器。
        output_path (Path): 输出的 markdown 文件路径，自动创建父级目录。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for element in elements:
            f.write(element.render() + "\n\n")  # 多一行空行增加可读性
