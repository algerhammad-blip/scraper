import streamlit as st
import pandas as pd
import cloudscraper
import re
import json
from urllib.parse import urlparse

st.set_page_config(page_title="Industrial Lead Scraper", layout="wide")

with st.sidebar:
    st.title("🔑 Configuration")
    serper_key = "587b340c8ef53f0c9a4d04e8feeff9113c0b499e"
    st.info("Bypasses security to find Emails & Phone Numbers.")

st.title("🚀 Professional Lead & Contact Scraper")
st.write("Finds companies and extracts direct contact details for free.")

def extract_contacts(html):
    """Final Pro Version: Extracts complete, valid business contacts"""
    
    # 1. Emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, html)
    emails = [e.strip().lower() for e in list(set(emails)) if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
    
    # 2. Phone Numbers - Improved Logic
    # Looks for numbers starting with + or digits, at least 10 characters long
    phone_pattern = r'\+?[\d\s\-\(\)]{10,20}'
    raw_phones = re.findall(phone_pattern, html)
    
    cleaned_phones = []
    for p in raw_phones:
        # Remove spaces and dashes to count actual digits
        digits_only = "".join(filter(str.isdigit, p))
        
        # VALID PHONE CRITERIA:
        # - Must have between 10 and 15 digits
        # - Must not be a repetitive dummy number like '255 255 255'
        if 10 <= len(digits_only) <= 15:
            if len(set(digits_only)) > 3: # Filters out things like 0000000000 or 255255255
                cleaned_phones.append(p.strip())

    # Remove duplicates
    final_phones = list(dict.fromkeys(cleaned_phones)) 
    
    return ", ".join(emails[:2]), ", ".join(final_phones[:2])

def crawl_site(url):
    """Visits site and tries to find contacts"""
    # Avoid scraping Facebook/LinkedIn/Insta - they always block bots
    domain = urlparse(url).netloc
    if any(social in domain for social in ['facebook.com', 'instagram.com', 'linkedin.com', 'twitter.com']):
        return "Social Media (Blocked)", "Check Page Manually"

    scraper = cloudscraper.create_scraper()
    try:
        res = scraper.get(url, timeout=10)
        emails, phones = extract_contacts(res.text)
        
        # Try contact page if homepage is empty
        if not emails and not phones:
            for path in ["/contact", "/about"]:
                res = scraper.get(url.rstrip('/') + path, timeout=5)
                emails, phones = extract_contacts(res.text)
                if emails or phones: break
        
        return (emails if emails else "Not Found"), (phones if phones else "Not Found")
    except:
        return "Security Block", "N/A"

query = st.text_input("Enter Search Keyword:", placeholder="e.g. Software companies in Sargodha")

if st.button("Run Full Scrape"):
    if not serper_key:
        st.error("Please enter Serper Key in the sidebar!")
    elif query:
        with st.spinner("Scanning websites for contact details..."):
            import requests
            search_url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
            # We add "website" to the query to get better results
            search_res = requests.post(search_url, headers=headers, data=json.dumps({"q": query}))
            
            organic = search_res.json().get('organic', [])
            if organic:
                results = []
                bar = st.progress(0)
                for i, item in enumerate(organic[:10]):
                    link = item.get('link')
                    email, phone = crawl_site(link)
                    results.append({
                        "Company": item.get('title'),
                        "Website": link,
                        "Email": email,
                        "Phone/Contact": phone
                    })
                    bar.progress((i + 1) / len(organic[:10]))
                
                df = pd.DataFrame(results)
                st.success("Scrape Complete!")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Export Data to CSV", csv, "leads.csv", "text/csv")
            else:
                st.error("No results found.")