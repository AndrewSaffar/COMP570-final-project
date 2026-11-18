import json
from pathlib import Path
import re
import time
import pandas as pd
from bs4 import BeautifulSoup as BS
import requests_cache
import requests
from datetime import timedelta
from urllib.parse import urljoin

requests_cache.install_cache(
    'imsdb_cache', 
    expire_after=timedelta(minutes=30)
)
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "script.csv"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def scrape_transcript(link, episode_name):
    base_url = 'https://imsdb.com/'
    response = requests.get(urljoin(base_url, link), headers=HEADERS)
    html = response.text
    soup = BS(html, 'html.parser')
    details = soup.select_one(".script-details") 
    if not details:
        print(f"No .script-details for episode: {episode_name}")
        return pd.DataFrame()
    a_tags = details.select('a')
    hrefs = [a.get("href", "") for a in a_tags]
    transcript_link = next((href for href in hrefs if href.startswith('/transcripts/')), None)
    if not transcript_link:
        print(f"No trancript link for episode: {episode_name}")
        return pd.DataFrame()
    transcript_response = requests.get(urljoin(base_url, transcript_link), headers=HEADERS)
    transcript_html = transcript_response.text
    transcript_soup = BS(transcript_html, 'html.parser')
    script = transcript_soup.select_one(".scrtext")
    if not script:
        print(f"No .scrtext for episode: {episode_name}")
        return pd.DataFrame()
    
    title = ''
    transcript = []
    for b_tag in script.find_all("b"):
        if len(b_tag.get_text(strip=True)) == 0 and len(b_tag.find_all()) == 0:
            b_tag.decompose()
    for b_tag in script.find_all("b"):
        if len(title) == 0:
            title = b_tag.get_text().strip()
        else:
            character = b_tag.get_text().strip()
            content = ''
            for sibling in b_tag.next_siblings:
                if getattr(sibling, 'name', None) == 'b':
                    break
                text = sibling.get_text() if hasattr(sibling, 'get_text') else str(sibling)
                text = text.strip()
                if text:
                    if len(content) == 0:
                        content = text
                    else:
                        content += ' ' + text
            transcript.append({'episode_name': episode_name, 'character': character, 'content': content})  
    transcript = pd.DataFrame(transcript)
    return transcript

def main():
    url = "https://imsdb.com/TV/Seinfeld.html"
    response = requests.get(url, headers=HEADERS)
    html = response.text

    soup = BS(html, 'html.parser')
    series = []
    for h2 in soup.find_all("h2"):
        heading = h2.get_text(strip=True)
        if not heading.startswith('Series'):
            continue

        season_match = re.search(r"\d+$", heading)
        if not season_match:
            continue
        season_number = int(season_match.group())

        episodes = []
        episode_number = 1
        for sibling in h2.find_next_siblings():
            if sibling.name == "h2":
                break
            a_tag = sibling.select_one('a')
            if a_tag and a_tag.get('href'):
                episode_name = a_tag.get_text(strip=True)
                print(f"S{season_number} E{episode_number}")
                episode = scrape_transcript(a_tag.get('href'), episode_name)
                print(f"length: {len(episode)} lines")
                if not episode.empty:
                    episode["season_number"] = season_number
                    episode["episode_number"] = episode_number
                    episodes.append(episode)
                episode_number += 1
                time.sleep(0.5)
        if episodes:
            episodes_df = pd.concat(episodes, ignore_index=True)
            series.append(episodes_df)
    if series:
        df = pd.concat(series, ignore_index=True)
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_FILE, columns=["season_number", "episode_number", "episode_name", "character", "content"], index=False)

        print(f"Scraping successful. Output at: {OUTPUT_FILE}")
        print(f"Total number of scrapes lines: {len(df)}")
    else:
        print("No transcripts scraped.")

if __name__ == "__main__":
    main()