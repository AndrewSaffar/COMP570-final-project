import re
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "test_raw"

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

def extract_line(raw_line):
    bold = raw_line.find("b")
    if bold is not None:
        bold_string = bold.get_text().strip()
        if bold_string.lower() != "end":
            character = bold_string[:-1] # Remove ":"
            bold.extract() # Remove the character from the line
            line = raw_line.text.strip()
            line = re.sub(r"\s+", " ", line) # Make better whitespaces
            return character, line
    return None, None

def get_episode_dialogue(soup):
    dialogue = []
    lines = soup.find_all("p")
    for raw_line in lines:
        character, line = extract_line(raw_line)
        if character is not None:
            dialogue.append({
                "character": character,
                "line": line
            })
    episode_df = pd.DataFrame(dialogue)
    return episode_df


def main():
    df = pd.DataFrame(columns=["season", "episode", "title", "character", "line"])
    htm_files = get_all_script_files()    
    for file in htm_files:
        season, episode = get_season_episode(file)

        with open(file, "r", encoding="utf-8", errors="replace") as file: # See if we could do errors="ignore" instead of "replace"
            content = file.read()
        soup = BeautifulSoup(content, "html5lib") # Address paragraphs with wrong closing tag
        soup = soup.prettify()
        soup = BeautifulSoup(soup, "html.parser")


        title = get_title(soup)
        episode_df = get_episode_dialogue(soup)

        episode_df["season"] = season
        episode_df["episode"] = episode
        episode_df["title"] = title

        df = pd.concat([df, episode_df], ignore_index = True)

    df.to_csv(DATA_DIR / "friends.csv")


if __name__ == "__main__":
    main()

