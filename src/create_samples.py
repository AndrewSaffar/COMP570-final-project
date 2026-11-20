from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" 
ANNOTATION_PATH = DATA_PATH / "annotation"
SCRIPT_PATH = DATA_PATH / "friends.csv"
SIDE_CHARACTERS = ["Rachel", "Monica", "Joey"]
MIN_LENGTH = 15
TOTAL_SAMPLE_SIZE = 350
OPEN_CODING_SAMPLE_SIZE = 100
DOUBLE_ANNOTATION_SAMPLE_SIZE = 150
DOUBLE_ANNOTATION_SAMPLE_SIZE_PER_CHARACTER = int(DOUBLE_ANNOTATION_SAMPLE_SIZE / len(SIDE_CHARACTERS))
RANDOM_SEED = 42

def season_breakdown(sample, sample_name, character):
    print(f"{sample_name} {character} season breakdown: ")
    for season in sorted(sample["season"].unique()):
        print(f"Season {season}: {len(sample[sample["season"]==season])} lines.")
    print("------------\n")

def sample_character(df, character):
    character_df = df[df["character"]==character]
    character_df = character_df[character_df["length"]>=MIN_LENGTH]
    total_sample = character_df.sample(n=TOTAL_SAMPLE_SIZE, random_state = RANDOM_SEED)
    season_breakdown(total_sample, "total", character)
    total_sample_file = f"{character}_sample.csv"
    total_sample.to_csv(ANNOTATION_PATH / total_sample_file, index=False)

    open_coding_sample = total_sample.sample(n=OPEN_CODING_SAMPLE_SIZE, random_state = RANDOM_SEED)
    season_breakdown(open_coding_sample, "open coding", character)
    open_coding_file = f"{character}_open_coding_sample.csv"
    open_coding_sample.to_csv(ANNOTATION_PATH / open_coding_file, index=False)

    double_annotation_sample = total_sample.drop(open_coding_sample.index).sample(n=DOUBLE_ANNOTATION_SAMPLE_SIZE_PER_CHARACTER, random_state = RANDOM_SEED)
    season_breakdown(double_annotation_sample, "double annotation", character)
    double_annotation_file = f"{character}_double_annotation_sample.csv"
    double_annotation_sample.to_csv(ANNOTATION_PATH / double_annotation_file, index=False)

    single_annotation_sample = total_sample.drop(open_coding_sample.index).drop(double_annotation_sample.index)
    season_breakdown(single_annotation_sample, "single annotation", character)
    single_annotation_file = f"{character}_single_annotation_sample.csv"
    single_annotation_sample.to_csv(ANNOTATION_PATH / single_annotation_file, index=False)
    
def main():
    ANNOTATION_PATH.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SCRIPT_PATH)
    df = df[df["character"].isin(SIDE_CHARACTERS)]
    for col in df:
        print(f"Missing values in {col}: {df[col].isnull().sum()}")
    df["length"] = (
        df["line"]
        .str.replace(r"\([^()]*\)", "", regex=True)
        .str.split()
        .str.len())
    df = df[df["length"]>0]
    df["length"] = df["length"].astype(int)

    [sample_character(df, character) for character in SIDE_CHARACTERS]
    

if __name__ == "__main__":
    main()