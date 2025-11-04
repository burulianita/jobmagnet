import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ---- ADATBÁZIS ----
conn = sqlite3.connect("jobs.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS jobs
             (title TEXT, company TEXT, salary TEXT, location TEXT, date TEXT)''')
conn.commit()

# ---- SCRAPER FÜGGVÉNY ----
def scrape():
    import requests
    from bs4 import BeautifulSoup
    url = "https://www.profession.hu/allasok/1,0,0,0,0,0,python"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
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

# ---- UI ----
st.title("Python Állásfigyelő – Élő Dashboard")
st.caption("Minden nap frissül • Profession.hu")

col1, col2 = st.columns(2)
if col1.button("Frissítés MOST", type="primary"):
    with st.spinner("1000 hirdetés letöltése…"):
        új = scrape()
    st.success(f"{új} új hirdetés betöltve!")

df = pd.read_sql("SELECT * FROM jobs ORDER BY date DESC", conn)

# METRIKÁK
with col2:
    st.metric("Összes hirdetés", len(df))
    avg = df[df["salary"].str.contains("Ft")]["salary"].str.extract(r'(\d+\.?\d*)').astype(float).mean()
   avg = df[df["salary"].str.contains("Ft", na=False)]["salary"] \
        .str.extract(r'(\d[\d\.\s]*)').astype(float)
avg_val = avg.iloc[0] if not avg.empty else None
st.metric("Átlagbér", f"{avg_val:,.0f} Ft" if avg_val else "N/A")
# TOP 10 SKILL
skills = df["title"].str.extractall(r'(Django|FastAPI|Flask|SQL|Pandas|AWS|Docker)').groupby(0).size().sort_values(ascending=False)
fig = px.bar(skills.head(10), color_discrete_sequence=["#636EFA"])
st.plotly_chart(fig, use_container_width=True)

# TÁBLÁZAT
st.subheader("Legfrissebb 10 hirdetés")
st.dataframe(df.head(10)[["title","company","salary","location"]], use_container_width=True)
