import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host='localhost',
    database='fm_wonderkids',
    user='postgres',
    password=os.environ.get('DB_PASSWORD'),
    port='5432'
)

# ── 1. PLAYERS BY POSITION ─────────────────────────────────────────────────
def plot_by_position():
    df = pd.read_sql("""
        SELECT position, COUNT(*) as count
        FROM wonderkids
        GROUP BY position
        ORDER BY CASE position
            WHEN 'GK' THEN 1 WHEN 'DC' THEN 2
            WHEN 'FBL' THEN 3 WHEN 'FBR' THEN 4
            WHEN 'DM' THEN 5 WHEN 'MC' THEN 6
            WHEN 'AML' THEN 7 WHEN 'AMR' THEN 8
            WHEN 'AMC' THEN 9 WHEN 'ST' THEN 10
        END
    """, conn)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(df['position'], df['count'], color='#5b4fcf')
    ax.bar_label(bars, padding=3)
    ax.set_title('FM26 Wonderkids by Position', fontsize=16, fontweight='bold')
    ax.set_xlabel('Position')
    ax.set_ylabel('Number of Players')
    plt.tight_layout()
    plt.savefig('by_position.png', dpi=150)
    plt.show()
    print('Saved by_position.png')

# ── 2. AVERAGE RATING BY POSITION ──────────────────────────────────────────
def plot_avg_rating():
    df = pd.read_sql("""
        SELECT position, ROUND(AVG(rating), 1) as avg_rating
        FROM wonderkids
        GROUP BY position
        ORDER BY avg_rating DESC
    """, conn)

    colors = ['#5b4fcf' if i == 0 else '#a78bfa' for i in range(len(df))]
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(df['position'], df['avg_rating'], color=colors)
    ax.bar_label(bars, padding=3)
    ax.set_ylim(78, 84)
    ax.set_title('Average Rating by Position', fontsize=16, fontweight='bold')
    ax.set_xlabel('Position')
    ax.set_ylabel('Average Rating')
    plt.tight_layout()
    plt.savefig('avg_rating.png', dpi=150)
    plt.show()
    print('Saved avg_rating.png')

# ── 3. TOP 15 NATIONS ──────────────────────────────────────────────────────
def plot_top_nations():
    df = pd.read_sql("""
        SELECT nationality, COUNT(*) as players
        FROM wonderkids
        GROUP BY nationality
        ORDER BY players DESC
        LIMIT 15
    """, conn)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(df['nationality'][::-1], df['players'][::-1], color='#5b4fcf')
    ax.bar_label(bars, padding=3)
    ax.set_title('Top 15 Nations — FM26 Wonderkids', fontsize=16, fontweight='bold')
    ax.set_xlabel('Number of Players')
    plt.tight_layout()
    plt.savefig('top_nations.png', dpi=150)
    plt.show()
    print('Saved top_nations.png')

# ── 4. TOP 20 WONDERKIDS ───────────────────────────────────────────────────
def plot_top20():
    df = pd.read_sql("""
        SELECT name, position, rating, nationality
        FROM wonderkids
        ORDER BY rating DESC
        LIMIT 20
    """, conn)

    labels = [f"{row['name']} ({row['position']})" for _, row in df.iterrows()]

    fig, ax = plt.subplots(figsize=(12, 9))
    bars = ax.barh(labels[::-1], df['rating'][::-1], color='#5b4fcf')
    ax.bar_label(bars, padding=3)
    ax.set_xlim(88, 98)
    ax.set_title('Top 20 FM26 Wonderkids by Rating', fontsize=16, fontweight='bold')
    ax.set_xlabel('Rating')
    plt.tight_layout()
    plt.savefig('top20.png', dpi=150)
    plt.show()
    print('Saved top20.png')

# ── 5. RATING DISTRIBUTION ─────────────────────────────────────────────────
def plot_rating_dist():
    df = pd.read_sql("SELECT rating FROM wonderkids WHERE rating IS NOT NULL", conn)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(df['rating'], bins=20, color='#5b4fcf', edgecolor='white')
    ax.set_title('Rating Distribution — All FM26 Wonderkids', fontsize=16, fontweight='bold')
    ax.set_xlabel('Rating')
    ax.set_ylabel('Number of Players')
    plt.tight_layout()
    plt.savefig('rating_dist.png', dpi=150)
    plt.show()
    print('Saved rating_dist.png')

# ── 6. AGE vs RATING SCATTER ───────────────────────────────────────────────
def plot_age_vs_rating():
    df = pd.read_sql("""
        SELECT age, rating, position
        FROM wonderkids
        WHERE age IS NOT NULL AND rating IS NOT NULL
    """, conn)

    colors = {
        'GK': '#ef4444', 'DC': '#f59e0b', 'FBL': '#22c55e',
        'FBR': '#06b6d4', 'DM': '#8b5cf6', 'MC': '#5b4fcf',
        'AML': '#ec4899', 'AMR': '#f97316', 'AMC': '#14b8a6', 'ST': '#84cc16'
    }

    fig, ax = plt.subplots(figsize=(12, 7))
    for pos, group in df.groupby('position'):
        ax.scatter(group['age'], group['rating'],
                  label=pos, color=colors.get(pos, '#gray'),
                  alpha=0.7, s=40)

    ax.set_title('Age vs Rating — FM26 Wonderkids', fontsize=16, fontweight='bold')
    ax.set_xlabel('Age')
    ax.set_ylabel('Rating')
    ax.legend(loc='lower right', ncol=2)
    plt.tight_layout()
    plt.savefig('age_vs_rating.png', dpi=150)
    plt.show()
    print('Saved age_vs_rating.png')

# ── 7. TOP CLUBS ───────────────────────────────────────────────────────────
def plot_top_clubs():
    df = pd.read_sql("""
        SELECT club, COUNT(*) as players,
               ROUND(AVG(rating), 1) as avg_rating
        FROM wonderkids
        WHERE club != '' AND club != '-'
        GROUP BY club
        ORDER BY players DESC
        LIMIT 15
    """, conn)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(df['club'][::-1], df['players'][::-1], color='#5b4fcf')
    ax.bar_label(bars, padding=3)
    ax.set_title('Top 15 Clubs with Most Wonderkids', fontsize=16, fontweight='bold')
    ax.set_xlabel('Number of Wonderkids')
    plt.tight_layout()
    plt.savefig('top_clubs.png', dpi=150)
    plt.show()
    print('Saved top_clubs.png')

# ── RUN ALL ────────────────────────────────────────────────────────────────
print('Generating visualisations...')
plot_by_position()
plot_avg_rating()
plot_top_nations()
plot_top20()
plot_rating_dist()
plot_age_vs_rating()
plot_top_clubs()

conn.close()
print('\nAll charts saved!')