from enum import Enum


class MarkdownLevel(str, Enum):
    """
    Markdown 结构等级（标题/段落等），表示语义层次。
    """

    HEADING_1 = "#"
    HEADING_2 = "##"
    HEADING_3 = "###"
    PARAGRAPH = ""


class MarkdownStyle(str, Enum):
    """
    Markdown 格式修饰类型，如列表、引用等。
    可与 MarkdownLevel 组合使用。
    """

    NONE = ""
    LIST_ITEM = "-"
