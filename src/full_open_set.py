from pathlib import Path
import pandas as pd

ANNOTATION_PATH = Path(__file__).parent.parent / "data" / "annotation"
SIDE_CHARACTERS = ["Rachel", "Monica", "Joey"]
OUTPUT_FILE = ANNOTATION_PATH / "open_coding.csv"
def main():
    dfs = []
    for character in SIDE_CHARACTERS:
        file = ANNOTATION_PATH / f"{character}_open_coding_sample.csv"
        dfs.append(pd.read_csv(file))
    df = pd.concat(dfs)
    df.to_csv(OUTPUT_FILE, index=False)
    print(len(df))
if __name__ == "__main__":
    main()