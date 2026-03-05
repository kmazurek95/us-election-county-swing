import os
import io
import zipfile
import requests
import pandas as pd
from census import Census

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

MEDSL_DOI = "doi:10.7910/DVN/VOQCHQ"
MEDSL_URL = (
    "https://dataverse.harvard.edu/api/access/dataset/"
    f":persistentId/?persistentId={MEDSL_DOI}"
)

NCHS_URL = "https://www.cdc.gov/nchs/data/data-analysis/NCHSurb-rural-codes.csv"

GAZETTEER_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2024_Gazetteer/2024_Gaz_counties_national.zip"
)

# BLS Local Area Unemployment Statistics, all states seasonally adjusted
BLS_LAUS_URL = "https://download.bls.gov/pub/time.series/la/la.data.3.AllStatesS"


def _ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def download_medsl(force=False):
    """Download MEDSL county presidential returns from Harvard Dataverse."""
    _ensure_dirs()
    csv_path = os.path.join(RAW_DIR, 'countypres_2000-2024.csv')
    if os.path.exists(csv_path) and not force:
        print(f"Already exists: {csv_path}")
        return csv_path

    print("Downloading MEDSL election data from Harvard Dataverse...")
    resp = requests.get(MEDSL_URL, timeout=180)
    resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    csv_names = [n for n in z.namelist() if n.lower().endswith(('.csv', '.tab'))]
    if not csv_names:
        raise FileNotFoundError(f"No CSV/TAB found in MEDSL ZIP. Contents: {z.namelist()}")

    # pick the largest file (the main dataset)
    target = max(csv_names, key=lambda n: z.getinfo(n).file_size)
    print(f"Extracting {target}...")

    with z.open(target) as src, open(csv_path, 'wb') as dst:
        dst.write(src.read())

    print(f"Saved to {csv_path}")
    return csv_path


def download_nchs(force=False):
    """Download NCHS 2013 urban-rural classification codes from CDC."""
    _ensure_dirs()
    out_path = os.path.join(RAW_DIR, 'nchs_urban_rural.csv')
    if os.path.exists(out_path) and not force:
        print(f"Already exists: {out_path}")
        return out_path

    print("Downloading NCHS urban-rural codes...")
    resp = requests.get(NCHS_URL, timeout=60)
    resp.raise_for_status()
    with open(out_path, 'wb') as f:
        f.write(resp.content)

    print(f"Saved to {out_path}")
    return out_path


def download_gazetteer(force=False):
    """Download Census 2024 gazetteer for county land area."""
    _ensure_dirs()
    out_path = os.path.join(RAW_DIR, 'gazetteer_counties.txt')
    if os.path.exists(out_path) and not force:
        print(f"Already exists: {out_path}")
        return out_path

    print("Downloading Census gazetteer...")
    resp = requests.get(GAZETTEER_URL, timeout=60)
    resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    txt_names = [n for n in z.namelist() if n.endswith('.txt')]
    if not txt_names:
        raise FileNotFoundError(f"No TXT in gazetteer ZIP. Contents: {z.namelist()}")

    with z.open(txt_names[0]) as src, open(out_path, 'wb') as dst:
        dst.write(src.read())

    print(f"Saved to {out_path}")
    return out_path


def download_bls_laus(force=False):
    """Fetch state unemployment rates from BLS public API for 2020 and 2024."""
    _ensure_dirs()
    out_path = os.path.join(RAW_DIR, 'bls_laus_states.json')
    if os.path.exists(out_path) and not force:
        print(f"Already exists: {out_path}")
        return out_path

    import json
    from us import states as us_states

    # build series IDs: LASST{FIPS}0000000000003 = state unemployment rate
    series_ids = []
    for s in us_states.STATES:
        series_ids.append(f"LASST{s.fips}0000000000003")
    # DC
    series_ids.append("LASST110000000000003")

    print("Fetching state unemployment rates from BLS API...")

    # BLS v2 API without registration key limits to 25 series per request
    all_data = []
    for i in range(0, len(series_ids), 25):
        batch = series_ids[i:i+25]
        payload = {
            "seriesid": batch,
            "startyear": "2020",
            "endyear": "2024",
        }
        resp = requests.post(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get('status') != 'REQUEST_SUCCEEDED':
            print(f"BLS API warning: {result.get('message', 'unknown error')}")

        for series in result.get('Results', {}).get('series', []):
            sid = series['seriesID']
            for entry in series['data']:
                all_data.append({
                    'series_id': sid,
                    'year': int(entry['year']),
                    'period': entry['period'],
                    'value': entry['value'],
                })

    with open(out_path, 'w') as f:
        json.dump(all_data, f)

    print(f"Saved {len(all_data)} records to {out_path}")
    return out_path


def fetch_acs_demographics(api_key, vintage=2023):
    """Pull ACS 5-year county demographics via Census API. Returns DataFrame."""
    _ensure_dirs()
    out_path = os.path.join(RAW_DIR, 'acs_demographics.csv')

    print(f"Fetching ACS {vintage} 5-year data from Census API...")
    c = Census(api_key, year=vintage)

    fields = [
        'NAME',
        'B01003_001E',  # total population
        'B01002_001E',  # median age
        'B19013_001E',  # median household income
        'B15003_001E',  # total pop 25+ (denominator for education)
        'B15003_022E',  # bachelor's degree
        'B15003_023E',  # master's degree
        'B15003_024E',  # professional degree
        'B15003_025E',  # doctorate
        'B23025_003E',  # civilian labor force
        'B23025_005E',  # unemployed
        'B03002_001E',  # total pop (for hispanic %)
        'B03002_003E',  # non-Hispanic white alone
        'B03002_012E',  # Hispanic/Latino
        'B02001_002E',  # white alone
        'B02001_003E',  # Black alone
    ]

    rows = c.acs5.state_county(fields, Census.ALL, Census.ALL)
    df = pd.DataFrame(rows)

    # build 5-digit FIPS
    df['FIPS'] = df['state'].str.zfill(2) + df['county'].str.zfill(3)

    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} counties to {out_path}")
    return df
