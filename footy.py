import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'localhost'),
    'database': 'fm_wonderkids',
    'user':     'postgres',
    'password': os.environ.get('DB_PASSWORD'),
    'port':     '5432'
}

# Position labels matching the page order
POSITION_LABELS = [
    'GK', 'DC', 'FBL', 'FBR', 'DM',
    'MC', 'AML', 'AMR', 'AMC', 'ST'
]

# ── SETUP DATABASE ─────────────────────────────────────────────────────────
def setup_database():
    try:
        setup_conn = psycopg2.connect(
            host='localhost', database='postgres',
            user='postgres', password=os.environ.get('DB_PASSWORD'), port='5432'
        )
        setup_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        setup_conn.cursor().execute('CREATE DATABASE fm_wonderkids')
        setup_conn.close()
        print('fm_wonderkids database created!')
    except Exception as e:
        print(f'Database note: {e}')

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wonderkids (
            id         SERIAL PRIMARY KEY,
            name       VARCHAR(100),
            age        INTEGER,
            position   VARCHAR(10),
            positions  VARCHAR(100),
            club       VARCHAR(100),
            wage_k     NUMERIC,
            nationality VARCHAR(100),
            rating     INTEGER,
            fetched_at TIMESTAMP,
            UNIQUE(name, position)
        )
    """)
    conn.commit()
    conn.close()
    print('Database ready!')

# ── EXTRACT ────────────────────────────────────────────────────────────────
def extract():
    print('Fetching FM Scout page...')
    url = 'https://www.fmscout.com/a-football-manager-2026-wonderkids.html'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f'Failed to fetch page: {response.status_code}')
    print(f'Page fetched successfully!')
    return response.content

# ── TRANSFORM ──────────────────────────────────────────────────────────────
def transform(content):
    print('Parsing tables...')
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    print(f'Found {len(tables)} position tables')

    all_players = []

    for i, table in enumerate(tables):
        position = POSITION_LABELS[i] if i < len(POSITION_LABELS) else f'POS{i}'
        rows = table.find_all('tr')[1:]  # skip header

        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 6:
                continue
            try:
                rating   = cols[0].text.strip()
                name     = cols[1].text.strip()
                age      = cols[2].text.strip()
                positions = cols[3].text.strip()
                club     = cols[4].text.strip()
                wage     = cols[5].text.strip()

                # Get nationality from img alt tag
                nat_img = cols[6].find('img') if len(cols) > 6 else None
                nationality = nat_img['alt'] if nat_img and nat_img.get('alt') else 'Unknown'

                # Clean wage — remove commas, handle missing
                wage_clean = wage.replace(',', '').strip()
                wage_val = float(wage_clean) if wage_clean and wage_clean != '-' else None

                all_players.append({
                    'name':        name,
                    'age':         int(age) if age.isdigit() else None,
                    'position':    position,
                    'positions':   positions,
                    'club':        club,
                    'wage_k':      wage_val,
                    'nationality': nationality,
                    'rating':      int(rating) if rating.isdigit() else None,
                    'fetched_at':  datetime.now(),
                })
            except Exception as e:
                continue

    df = pd.DataFrame(all_players)
    print(f'Parsed {len(df)} players across {len(tables)} positions')
    return df

# ── LOAD ───────────────────────────────────────────────────────────────────
def load(df, conn):
    print(f'Loading {len(df)} players into database...')
    cursor = conn.cursor()
    loaded = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO wonderkids
                (name, age, position, positions, club, wage_k, nationality, rating, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (name, position) DO UPDATE SET
                    age        = EXCLUDED.age,
                    club       = EXCLUDED.club,
                    wage_k     = EXCLUDED.wage_k,
                    rating     = EXCLUDED.rating,
                    fetched_at = EXCLUDED.fetched_at
            """, (
                row['name'], row['age'], row['position'], row['positions'],
                row['club'], row['wage_k'], row['nationality'],
                row['rating'], row['fetched_at']
            ))
            loaded += 1
        except Exception as e:
            conn.rollback()
            continue
    conn.commit()
    print(f'Loaded {loaded} players!')

# ── ANALYSE ────────────────────────────────────────────────────────────────
def analyse(conn):
    print('\n--- FM26 Wonderkids Summary ---')

    # Total by position
    by_pos = pd.read_sql("""
        SELECT position, COUNT(*) as count,
               ROUND(AVG(rating), 1) as avg_rating,
               MAX(rating) as top_rating
        FROM wonderkids
        GROUP BY position
        ORDER BY CASE position
            WHEN 'GK'  THEN 1 WHEN 'DC'  THEN 2
            WHEN 'FBL' THEN 3 WHEN 'FBR' THEN 4
            WHEN 'DM'  THEN 5 WHEN 'MC'  THEN 6
            WHEN 'AML' THEN 7 WHEN 'AMR' THEN 8
            WHEN 'AMC' THEN 9 WHEN 'ST'  THEN 10
        END
    """, conn)
    print('\nPlayers by position:')
    print(by_pos.to_string(index=False))

    # Top rated per position
    print('\n--- Top Rated Wonderkid Per Position ---')
    top = pd.read_sql("""
        SELECT DISTINCT ON (position) position, name, club, nationality, rating
        FROM wonderkids
        ORDER BY position, rating DESC
    """, conn)
    for _, row in top.iterrows():
        print(f"  {row['position']:5} | {row['rating']:3} | {row['name']:<30} | {row['club']:<25} | {row['nationality']}")

    # Top 10 overall
    print('\n--- Top 10 Wonderkids Overall ---')
    top10 = pd.read_sql("""
        SELECT name, position, club, nationality, rating, age
        FROM wonderkids
        ORDER BY rating DESC
        LIMIT 10
    """, conn)
    print(top10.to_string(index=False))

    # Best by nationality
    print('\n--- Top Nations ---')
    nations = pd.read_sql("""
        SELECT nationality, COUNT(*) as players,
               ROUND(AVG(rating), 1) as avg_rating
        FROM wonderkids
        GROUP BY nationality
        ORDER BY players DESC
        LIMIT 10
    """, conn)
    print(nations.to_string(index=False))

# ── RUN ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    setup_database()

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True

    # Extract
    content = extract()

    # Transform
    df = transform(content)

    # Load
    load(df, conn)

    # Analyse
    analyse(conn)

    conn.close()
    print('\n✅ Pipeline complete!')