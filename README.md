# Web Scraping Task – Week 1 Assignment

This project is part of the **Week 1 Web Scraping Assignment**, covering both the ethical/legal aspects of web scraping (Part A) and a practical dataset creation task (Part B).

---

## 📌 Part A: Ethics & Legality of Web Scraping
- **Terms of Use (ToU):** Website rules that restrict scraping. Violating them can lead to bans or legal issues.
- **Legality:** Depends on the type of data, purpose, and jurisdiction.
  - Public data scraping is often legal.
  - Private/login-protected scraping is usually illegal.
  - U.S. courts (HiQ vs LinkedIn) allowed scraping of public profiles.
  - EU’s GDPR restricts personal data scraping.
- **Ethical Concerns:**
  - Respect privacy (don’t scrape personal info).
  - Avoid server overload (use delays).
  - Respect content ownership (credit sources).
  - Be transparent in data use.

---

## 📌 Part B: Web Scraping English Sentences Dataset

**Objective:**  
Build a dataset of at least 2,000 clean, spoken-like English sentences.

**Sources Used:**  
- [Quotes to Scrape](http://quotes.toscrape.com) – short, natural quotes.  
- [Project Gutenberg](https://www.gutenberg.org/) – public-domain books (long-form text).  

**Steps Taken:**  
1. Scraped quotes using `requests` and `BeautifulSoup`.  
2. Downloaded books from Project Gutenberg.  
3. Split into sentences, cleaned text (removed URLs, strange characters, very short/long sentences).  
4. Deduplicated sentences and saved dataset.  
5. Final dataset: **2,000+ sentences** in both CSV and Excel formats.

---

## 📂 Repository Structure
- `scrape_sentences.py` → Python script for scraping and cleaning text.  
- `scraped_sentences.csv` → Final dataset (CSV format).  
- `scraped_sentences.xlsx` → Final dataset (Excel format).  
- `README.md` → Documentation (this file).  

---

## 🚀 How to Run
### Setup
```bash
# Clone repo
git clone https://github.com/ladyami/webscraping-task.git
cd webscraping-task

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows (Git Bash)
# OR
source venv/bin/activate      # macOS/Linux

# Install dependencies
pip install -r requirements.txt
