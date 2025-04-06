from pathlib import Path

from pipeline.task.pdf_to_jsonl import (
    gen_pdf_path,
    generate_jsonl_lines_from_pdf,
    write_jsonl_append,
)
from src.definition.const.location import INPUT_DIR, OUTPUT_DIR


async def pdf_to_jsonl_flow(
    prompt: str,
    pdf_dir: Path = INPUT_DIR,
    model: str = "gpt-4o-mini",
    detail: str = "auto",
    output_dir: Path = OUTPUT_DIR,
) -> None:
    async for path in gen_pdf_path(pdf_dir):
        path: Path
        write_jsonl_append(
            output_dir / path.with_suffix(".jsonl").name,
            generate_jsonl_lines_from_pdf(path, prompt, model, detail),
        )
