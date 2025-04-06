from asyncio import run

from pipeline.flow.pdf_to_jsonl_flow import pdf_to_jsonl_flow

if __name__ == "__main__":
    run(
        pdf_to_jsonl_flow(
            prompt="请将图像内容转换为 Markdown 结构化文本，保留原始排版格式，不使用代码块。只返回转换后的 Markdown 文本内容，勿添加任何解释。",
        )
    )
