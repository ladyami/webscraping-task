#this as can be save scrape_sentences.py or paste into a Jupyter notebook cell
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time, random, re, os
from urllib.parse import urlparse
import urllib.robotparser as robotparser

# Optional language check (install if you want): pip install langdetect
USE_LANGDETECT = False
if USE_LANGDETECT:
    try:
        from langdetect import detect
    except Exception:
        USE_LANGDETECT = False
        print("langdetect not available; continuing without language filtering.")

# ---------- Settings ----------
HEADERS = {
    "User-Agent": "LuxeScraper/1.0 (+mailto:amina.oyegoke@miva.edu.ng)"
}
DEFAULT_DELAY = 1.0  # seconds (used if robots.txt has no crawl-delay)
TARGET_SENTENCES = 2000
MIN_WORDS = 3
MAX_WORDS = 40
OUTPUT_CSV = "scraped_sentences.csv"
OUTPUT_XLSX = "scraped_sentences.xlsx"
# ------------------------------

def get_robots_info(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        # RobotFileParser may not expose crawl_delay for non-specified agents consistently,
        # so we try with our agent then '*'
        delay = rp.crawl_delay(HEADERS.get("User-Agent")) or rp.crawl_delay("*")
        return rp, delay
    except Exception:
        return None, None

def polite_get(url, session=None, max_retries=3):
    """Fetch a page politely (respecting robots via delay if found)."""
    session = session or requests.Session()
    rp, delay = get_robots_info(url)
    wait = delay if delay is not None else DEFAULT_DELAY
    for attempt in range(1, max_retries+1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                time.sleep(wait + random.random()*0.5)
                return resp
            else:
                # small backoff on non-200
                time.sleep(wait * attempt)
        except requests.RequestException as e:
            time.sleep(wait * attempt)
    return None

# -------------------------
# 1) Scrape quotes.toscrape.com
# -------------------------
def scrape_quotes_toscrape(max_pages=50):
    base = "http://quotes.toscrape.com/page/{}/"
    items = []
    session = requests.Session()
    for p in range(1, max_pages+1):
        url = base.format(p)
        resp = polite_get(url, session=session)
        if not resp:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        quote_spans = soup.find_all("span", class_="text")
        if not quote_spans:
            break
        for s in quote_spans:
            text = s.get_text(strip=True)
            items.append({"Sentence": text, "Source": url, "SourceType": "quote"})
        # optional break if we've collected a lot
        if len(items) >= 500:  # safe limit from this source
            break
    return items

# -------------------------
# 2) Download Project Gutenberg text and extract sentences
# -------------------------
def fetch_gutenberg_text(book_id):
    """
    Try common Gutenberg text URLs. Returns raw text or None on failure.
    """
    session = requests.Session()
    candidates = [
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"
    ]
    for url in candidates:
        resp = polite_get(url, session=session)
        if resp and resp.status_code == 200:
            return resp.text, url
    return None, None

def extract_gutenberg_body(text):
    """
    Strip Gutenberg header/footer markers if present.
    """
    start_match = re.search(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG.*\*\*\*", text, re.IGNORECASE)
    end_match = re.search(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG.*\*\*\*", text, re.IGNORECASE)
    if start_match and end_match:
        return text[start_match.end():end_match.start()]
    if start_match:
        return text[start_match.end():]
    return text

def split_into_sentences(text):
    """
    Prefer nltk if available; otherwise use a regex fallback.
    """
    try:
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
        except Exception:
            nltk.download('punkt')
        sents = nltk.tokenize.sent_tokenize(text)
        return sents
    except Exception:
        # Regex-based fallback
        cleaned = text.replace("\n", " ").strip()
        # split where sentence-ending punctuation is followed by whitespace and a capital letter or quote/parenthesis
        sents = re.split(r'(?<=[\.\?\!])\s+(?=[A-Z"\'\(\[\“\‘])', cleaned)
        return [s.strip() for s in sents if s.strip()]

def clean_sentence(s):
    s = s.strip()
    # remove URLs
    s = re.sub(r'http\S+|www\.\S+', '', s)
    # remove weird unicode non-letters (keep basic punctuation)
    s = re.sub(r'[^\x00-\x7F]+', ' ', s)
    # remove leftover multiple spaces
    s = re.sub(r'\s+', ' ', s)
    s = s.strip(" \"'`")  # strip surrounding quotes
    return s.strip()

def sentence_ok(s):
    words = s.split()
    if len(words) < MIN_WORDS or len(words) > MAX_WORDS:
        return False
    # simple heuristic to avoid dialogue lines that are just names, etc.
    if len(s) < 10:
        return False
    if any(ch in s for ch in ["@", "#"]):
        return False
    if USE_LANGDETECT:
        try:
            return detect(s) == 'en'
        except:
            return False
    return True

def scrape_gutenberg_books(book_ids):
    items = []
    for b in book_ids:
        print(f"Fetching Gutenberg book id={b} ...")
        text, url = fetch_gutenberg_text(b)
        if not text:
            print(f" -> failed to fetch book {b}. continuing.")
            continue
        body = extract_gutenberg_body(text)
        sents = split_into_sentences(body)
        for s in sents:
            cs = clean_sentence(s)
            if cs and sentence_ok(cs):
                items.append({"Sentence": cs, "Source": url or f"gutenberg:{b}", "SourceType": "gutenberg"})
        print(f" -> extracted {len(items)} sentences so far.")
        # stop early if we reached the target
        if len(items) >= TARGET_SENTENCES:
            break
    return items

# -------------------------
# 3) Main aggregator
# -------------------------
def build_dataset(target=TARGET_SENTENCES, gutenberg_ids=None):
    if gutenberg_ids is None:
        # recommended starter list of classics (public domain)
        gutenberg_ids = [1342, 11, 84, 1661, 98, 76, 2701, 345]  # Pride&Prejudice, Alice, Frankenstein, Sherlock Holmes, Tale of Two Cities, Huck Finn, Moby-Dick, Dracula
    all_items = []

    # 1) quotes (fast)
    print("Scraping quotes.toscrape.com ...")
    quotes = scrape_quotes_toscrape()
    all_items.extend(quotes)
    print(f"Collected {len(all_items)} sentences from quotes.")

    # 2) Gutenberg books (big boost)
    if len(all_items) < target:
        needed = target - len(all_items)
        print(f"Need {needed} more sentences from Gutenberg books.")
        guten_items = scrape_gutenberg_books(gutenberg_ids)
        all_items.extend(guten_items)
        print(f"Total collected after Gutenberg: {len(all_items)}")

    # 3) deduplicate and finalize
    df = pd.DataFrame(all_items)
    if df.empty:
        print("No sentences collected. Exiting.")
        return None
    orig_count = len(df)
    df.drop_duplicates(subset="Sentence", inplace=True)
    dedup_count = len(df)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    # keep only first `target` sentences
    if len(df) > target:
        df = df.iloc[:target].copy()
    # Add a SourceCategory column if not present
    if "SourceType" not in df.columns:
        df["SourceType"] = df["Source"].apply(lambda x: "unknown")
    # Save
    df.to_csv(OUTPUT_CSV, index=False)
    try:
        df.to_excel(OUTPUT_XLSX, index=False)
    except Exception as e:
        print("Could not save xlsx (openpyxl may be missing):", e)
    print(f"Saved {len(df)} sentences (orig {orig_count}, deduplicated {dedup_count}) to {OUTPUT_CSV} and {OUTPUT_XLSX}")
    return df

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    dataset = build_dataset()
    if dataset is not None:
        print("\nSample sentences:")
        print(dataset["Sentence"].head(10).to_list())


        input("Press Enter to exit...")

