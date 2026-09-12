# Bengaluru Urban Avian Bio-Acoustic Observatory

Streamlit dashboard for the Arduino UNO Q + BirdNET Bengaluru monitoring station.

## Run locally
```bash
pip install -r requirements.txt
streamlit run dashboard_app.py
```

## Image mapping
Bird photographs are stored locally under `assets/birds/`.
- Specific project images are used for bulbuls, crows, barbets, Purple Sunbird, Common Myna and Common Tailorbird.
- Generic category images are automatically reused for matching BirdNET labels, e.g. Barn Owl -> `owl.*`, Grey Hornbill -> `hornbill.*`, Black Drongo -> `drongo.*`, Little Egret -> `heron.*`.
- Food/prey photographs are stored under `assets/food/` and are loaded locally.

## Streamlit Cloud
Create a public GitHub repository and upload this folder. Then create a Streamlit Community Cloud app with:
- Branch: `main`
- Main file: `dashboard_app.py`
- Python dependencies: root `requirements.txt`

Do not upload `birdnet_model.onnx` or `birds.db` to a public repository.
