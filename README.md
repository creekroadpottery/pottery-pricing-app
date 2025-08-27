
# Pottery Cost Analysis App

A simple Streamlit app for pottery cost analysis and pricing. It calculates per piece cost, wholesale from margin, retail from multiplier, a 2 by 2 by 2 preset, energy costs, and glaze costs by grams.

## Quick Deploy on Streamlit Cloud

1. Create a new GitHub repo, public or private.
2. Upload two files to the repo
   - `pottery_pricing_app.py`
   - `requirements.txt`  with these lines:
     ```
     streamlit
     pandas
     ```
3. Go to https://share.streamlit.io
4. Select your repo and pick `pottery_pricing_app.py` as the main file.
5. Click Deploy. Your app will build, then open at a public URL.

## Edit and update

- Change the code in `pottery_pricing_app.py` on GitHub, then Streamlit Cloud will rebuild.
- If the build ever fails, check the logs in Streamlit Cloud.

## Local run (optional)

```
pip install streamlit pandas
streamlit run pottery_pricing_app.py
```

