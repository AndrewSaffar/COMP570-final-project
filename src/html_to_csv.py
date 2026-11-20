import re
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from copy import deepcopy
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_FILE_RAW = DATA_DIR / "friends_raw.csv"
OUTPUT_FILE = DATA_DIR / "friends.csv"
CHARACTERS = ["rachel", "monica", "joey"]

def get_all_script_files():
    if RAW_DATA_DIR.exists():
        return list(RAW_DATA_DIR.glob("*.htm"))
    else:
        print(f"No raw data found.")
        return None

def get_season_episode(file):
    raw_number = re.search(r"\d+", file.name)
    number = int(raw_number.group())

    if number > 1000:
        season = 10
        episode = number - 1000
    else:
        season = number // 100 # Fist number
        episode = number % 100 # Next two numbers

    return season, episode

def get_title(soup):
    title = soup.title
    if title is None: # Error with season 8, episode 17
        title = soup.find("h1")   
    return title.get_text().strip()  

def check_side_character(character):
    characters = re.split(r",|\s+and\s+", character) # For when there are multiple characters
    for character in characters:
        if character.strip().lower() in CHARACTERS:
            return True
    return False

def extract_line_filtered(raw_line):
    bold = raw_line.find("b")
    if bold is not None:
        bold_string = bold.get_text().strip()
        if bold_string.lower() != "end": # Excludes END
            character = bold_string[:-1] # Remove ":"
            is_side_character = check_side_character(character)
            if is_side_character:
                bold.extract() # Remove the character from the line
                line = raw_line.text.strip()
                line = re.sub(r"\s+", " ", line) # Make better whitespaces
                no_stage_directions = re.sub(r"(?:\(.*?\)|\[.*?\])", " ", line) # Do not count stage directions in word count
                if len(no_stage_directions.split()) >= 15: # Removes banter
                    return character, line
    return None, None

def extract_line_raw(raw_line):
    line_copy = deepcopy(raw_line) # Because .extract() modifies the soup and would fail for the filtered version
    bold = line_copy.find("b")
    if bold is not None:
        bold_string = bold.get_text().strip()
        character = bold_string[:-1] # Remove ":"
        bold.extract() # Remove the character from the line
        line = line_copy.text.strip()
        return character, line
    return None, None

def get_episode_dialogue(soup, filtered=True):
    dialogue = []
    lines = soup.find_all("p")
    for raw_line in lines:
        if filtered:
            character, line = extract_line_filtered(raw_line)
        else:
            character, line = extract_line_raw(raw_line)
        if character is not None:
            dialogue.append({
                "character": character,
                "line": line
            })
    episode_df = pd.DataFrame(dialogue)
    return episode_df


def main():
    df_raw = pd.DataFrame(columns=["season", "episode", "title", "character", "line"])
    df = pd.DataFrame(columns=["season", "episode", "title", "character", "line"])
    htm_files = get_all_script_files()    
    for file in tqdm(htm_files):
        season, episode = get_season_episode(file)

        with open(file, "r", encoding="utf-8", errors="replace") as file: # See if we could do errors="ignore" instead of "replace"
            content = file.read()
        soup = BeautifulSoup(content, "html5lib") # Address paragraphs with wrong closing tag
        soup = soup.prettify()
        soup = BeautifulSoup(soup, "html.parser")

        title = get_title(soup)
        episode_df_raw = get_episode_dialogue(soup, filtered=False)
        episode_df = get_episode_dialogue(soup, filtered=True)

        episode_df_raw["season"] = season
        episode_df_raw["episode"] = episode
        episode_df_raw["title"] = title
        
        episode_df["season"] = season
        episode_df["episode"] = episode
        episode_df["title"] = title

        df_raw = pd.concat([df_raw, episode_df_raw], ignore_index = True)
        df = pd.concat([df, episode_df], ignore_index = True)

    df_raw.to_csv(OUTPUT_FILE_RAW, index=False)
    df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()

