from pathlib import Path

# 0
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 1
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"
SRC_DIR = ROOT_DIR / "src"
ENV_FILE = ROOT_DIR / ".env"

# 2
LOG_DIR = SRC_DIR / "log"

if __name__ == "__main__":
    print(ROOT_DIR)
