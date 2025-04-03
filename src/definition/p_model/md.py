from pydantic import BaseModel, Field

from src.definition.enum.markdown_syntax import MarkdownLevel, MarkdownStyle


class MarkdownElement(BaseModel):
    """
    表示结构化的 Markdown 文本元素，可组合结构等级和样式修饰。
    """

    level: MarkdownLevel = Field(..., description="Markdown 层级，如标题或段落")
    style: MarkdownStyle = Field(..., description="Markdown 样式修饰，如列表")
    content: str = Field(..., description="文本内容")

    def render(self) -> str:
        """
        渲染为标准 Markdown 字符串。
        支持组合 style + level。
        """
        parts = []
        if self.style != MarkdownStyle.NONE:
            parts.append(self.style.value)
        if self.level != MarkdownLevel.PARAGRAPH:
            parts.append(self.level.value)
        parts.append(self.content)
        return " ".join(filter(None, parts))
