import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# ------------------- ADATBÁZIS -------------------
conn = sqlite3.connect("jobs.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        title TEXT, company TEXT, salary TEXT, location TEXT, date TEXT
    )
''')
conn.commit()

# ------------------- SCRAPER -------------------
def scrape():
    url = "https://www.profession.hu/allasok/1,0,0,0,0,0,python"
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    for card in soup.select(".job-card"):
        title = card.select_one("h2 a")
        company = card.select_one(".company-name")
        salary = card.select_one(".salary")
        location = card.select_one(".location")
        jobs.append({
            "title": title.text.strip() if title else "N/A",
            "company": company.text.strip() if company else "N/A",
            "salary": salary.text.strip() if salary else "Nem publikus",
            "location": location.text.strip() if location else "N/A",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    if jobs:
        pd.DataFrame(jobs).to_sql("jobs", conn, if_exists="append", index=False)
    return len(jobs)

# ------------------- UI -------------------
st.set_page_config(page_title="JobMagnet", layout="wide")
st.title("Python Állásfigyelő – Élő Dashboard")
st.caption("Minden nap frissül • Profession.hu • Kattints és frissül!")

# FRISSÍTÉS GOMB
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("FRISSÍTÉS MOST", type="primary", use_container_width=True):
        with st.spinner("1000+ hirdetés letöltése..."):
            új = scrape()
        st.success(f"{új} új hirdetés betöltve!")

# ADATOK BETÖLTÉSE
df = pd.read_sql("SELECT * FROM jobs ORDER BY date DESC", conn)

# METRIKÁK
with col2:
    st.metric("Összes hirdetés", len(df))

# ÁTLAGBÉR (hibamentes!)
try:
    nums = df[df["salary"].str.contains("Ft", na=False)]["salary"]\
        .str.extract(r'(\d[\d\.\s]*)').astype(float).dropna()
    avg = nums.mean().iloc[0] if not nums.empty else None
    st.metric("Átlagbér", f"{avg:,.0f} Ft" if avg else "N/A")
except:
    st.metric("Átlagbér", "N/A")

# TOP 10 SKILL
skills = df["title"].str.extractall(r'(Django|FastAPI|Flask|SQL|Pandas|AWS|Docker|React|Vue)')\
    .groupby(0).size().sort_values(ascending=False)
if not skills.empty:
    fig = px.bar(skills.head(10), color_discrete_sequence=["#636EFA"], text_auto=True)
    fig.update_layout(showlegend=False, title="Top 10 keresett skill")
    st.plotly_chart(fig, use_container_width=True)

# LEGFRISSEBB HIRDETÉSEK
st.subheader("Legfrissebb 10 állás")
if not df.empty:
    st.dataframe(
        df.head(10)[["title", "company", "salary", "location"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Még nincs adat – kattints a FRISSÍTÉS MOST gombra!")

st.caption("JobMagnet by [A Te Neved] • [GitHub linked] • [LinkedIn linked]")
