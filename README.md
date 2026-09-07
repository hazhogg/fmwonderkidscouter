# FM26 Wonderkids Pipeline

A data pipeline that scrapes all Football Manager 2026 wonderkids from FMScout, stores them in PostgreSQL and generates visualisation charts across all positions.

## What it does

- Scrapes 940+ wonderkids from fmscout.com across 10 positions
- Stores all player data in PostgreSQL
- Analyses top rated players per position
- Identifies best nations and clubs for wonderkids
- Generates 7 visualisation charts
- Updates automatically when re-run (upserts existing players)

## Positions covered

| Code | Position |
|---|---|
| GK | Goalkeeper |
| DC | Centre Back |
| FBL | Left Back |
| FBR | Right Back |
| DM | Defensive Midfielder |
| MC | Central Midfielder |
| AML | Left Winger |
| AMR | Right Winger |
| AMC | Attacking Midfielder |
| ST | Striker |

## Tech stack

- Python
- pandas
- PostgreSQL
- psycopg2
- BeautifulSoup4
- requests
- matplotlib

## Sample output

```
Players by position:
position  count  avg_rating  top_rating
      GK     45        79.7          86
      DC    140        79.9          88
     FBL     53        80.9          88
     FBR     43        80.5          87
      DM     84        80.4          90
      MC    126        81.6          93
     AML    116        81.3          90
     AMR     95        81.8          97
     AMC    104        82.5          93
      ST    135        82.4          96

Top Rated Wonderkid Per Position:
AMR | 97 | Lamine Yamal       | FC Barcelona     | Spain
ST  | 96 | Endrick            | Real Madrid      | Brazil
AMC | 93 | Paz, Nico          | Como             | Argentina
MC  | 93 | Bouaddi, Ayyoub    | Lille OSC        | France
DM  | 90 | Bernal, Marc       | FC Barcelona     | Spain
FBL | 88 | Lewis-Skelly, Myles| Arsenal          | England
DC  | 88 | Vušković, Luka     | Tottenham        | Croatia
GK  | 86 | Seimen, Dennis     | Stuttgart        | Germany
FBR | 87 | Fortea, Jesús      | Real Madrid      | Spain

Top Nations:
England     96 players  avg 80.9
Spain       96 players  avg 82.3
France      79 players  avg 81.3
Brazil      67 players  avg 81.4
Germany     57 players  avg 81.4
```

## Database table

### wonderkids

| Column | Description |
|---|---|
| name | Player name |
| age | Player age |
| position | Primary position code (GK, DC etc.) |
| positions | All positions the player can play |
| club | Current club |
| wage_k | Weekly wage in thousands |
| nationality | Player nationality |
| rating | FMScout recommendation rating (1-100) |
| fetched_at | When data was last scraped |

## Setup

1. Install PostgreSQL

2. Clone the repo:
```bash
git clone https://github.com/yourusername/fm-wonderkids-pipeline.git
cd fm-wonderkids-pipeline
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```
DB_PASSWORD=yourpassword
DB_HOST=localhost
```

5. Run the pipeline:
```bash
python fm_pipeline.py
```

## Visualisations

```bash
python visualise.py
```

Generates 7 charts:
- Wonderkids count by position
- Average rating by position
- Top 15 nations by number of wonderkids
- Top 20 wonderkids by rating
- Rating distribution histogram
- Age vs rating scatter plot (coloured by position)
- Top 15 clubs with most wonderkids

## Example queries

```sql
-- Top 10 wonderkids overall
SELECT name, position, club, nationality, rating, age
FROM wonderkids
ORDER BY rating DESC
LIMIT 10;

-- Best strikers
SELECT name, club, nationality, rating, age
FROM wonderkids
WHERE position = 'ST'
ORDER BY rating DESC
LIMIT 10;

-- Cheapest high rated wonderkids (bargains)
SELECT name, position, club, nationality, rating, wage_k
FROM wonderkids
WHERE rating >= 83
ORDER BY wage_k ASC
LIMIT 15;

-- Best wonderkids by nation
SELECT nationality, COUNT(*) as players,
       ROUND(AVG(rating), 1) as avg_rating,
       MAX(rating) as top_rating
FROM wonderkids
GROUP BY nationality
ORDER BY avg_rating DESC
LIMIT 15;

-- Young high potential players (age 16-17)
SELECT name, age, position, club, nationality, rating
FROM wonderkids
WHERE age <= 17
ORDER BY rating DESC
LIMIT 20;
```

## Project structure

```
fm-wonderkids-pipeline/
├── fm_pipeline.py   ← main scraper and ETL pipeline
├── visualise.py     ← chart generation
├── requirements.txt ← dependencies
├── .gitignore       ← excludes .env and charts
└── .env             ← database password (not pushed)
```

## Data source

Data scraped from [FMScout.com](https://www.fmscout.com/a-football-manager-2026-wonderkids.html) — the definitive Football Manager wonderkids resource.

## Author

Harry
