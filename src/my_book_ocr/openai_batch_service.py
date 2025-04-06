from src.definition.const.location import OUTPUT_DIR
from src.pipeline.flow.openai_batch_flow import openai_batch_flow

if __name__ == "__main__":
    openai_batch_flow(OUTPUT_DIR / "认知科学与广义进化论 (赵南元) (Z-Library).jsonl")
