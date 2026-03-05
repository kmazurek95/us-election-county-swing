import pandas as pd
import numpy as np


def compute_two_party_share(election_df):
    """From MEDSL long-format data, compute R two-party vote share per county-year."""
    df = election_df.copy()

    # MEDSL uses 'party_simplified' in recent versions, 'party' in older ones
    party_col = 'party_simplified' if 'party_simplified' in df.columns else 'party'
    df[party_col] = df[party_col].str.upper().str.strip()

    dr = df[df[party_col].isin(['DEMOCRAT', 'REPUBLICAN'])].copy()

    pivot = dr.pivot_table(
        index=['year', 'county_fips'],
        columns=party_col,
        values='candidatevotes',
        aggfunc='sum'
    ).reset_index()

    pivot.columns.name = None
    pivot = pivot.rename(columns={'DEMOCRAT': 'dem_votes', 'REPUBLICAN': 'rep_votes'})

    # some counties might only have one party reported
    pivot['dem_votes'] = pivot['dem_votes'].fillna(0)
    pivot['rep_votes'] = pivot['rep_votes'].fillna(0)

    pivot['two_party_total'] = pivot['dem_votes'] + pivot['rep_votes']
    pivot['rep_share'] = pivot['rep_votes'] / pivot['two_party_total']

    return pivot


def compute_swing(shares_df):
    """Compute 2020-to-2024 swing from a two-party share dataframe."""
    s2020 = shares_df[shares_df['year'] == 2020][['county_fips', 'rep_share', 'dem_votes', 'rep_votes']].copy()
    s2024 = shares_df[shares_df['year'] == 2024][['county_fips', 'rep_share', 'dem_votes', 'rep_votes']].copy()

    merged = s2020.merge(s2024, on='county_fips', suffixes=('_2020', '_2024'))
    merged['swing'] = merged['rep_share_2024'] - merged['rep_share_2020']

    return merged


def process_acs(df_acs):
    """Rename ACS columns, handle missing sentinels, compute derived percentages."""
    renames = {
        'B01003_001E': 'total_pop',
        'B01002_001E': 'median_age',
        'B19013_001E': 'median_hh_income',
        'B15003_001E': 'pop_25plus',
        'B15003_022E': 'bachelors',
        'B15003_023E': 'masters',
        'B15003_024E': 'professional',
        'B15003_025E': 'doctorate',
        'B23025_003E': 'labor_force',
        'B23025_005E': 'unemployed',
        'B03002_001E': 'total_pop_race',
        'B03002_003E': 'white_nh_pop',
        'B03002_012E': 'hispanic_pop',
        'B02001_002E': 'white_pop',
        'B02001_003E': 'black_pop',
    }
    out = df_acs.rename(columns=renames).copy()

    # Census API returns -666666666 for suppressed/missing data
    numeric_cols = list(renames.values())
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors='coerce')
            out.loc[out[col] < 0, col] = np.nan

    out['college_plus'] = (
        out['bachelors'] + out['masters'] + out['professional'] + out['doctorate']
    )
    out['pct_college'] = out['college_plus'] / out['pop_25plus']
    out['pct_unemployed'] = out['unemployed'] / out['labor_force']
    out['pct_white_nh'] = out['white_nh_pop'] / out['total_pop']
    out['pct_black'] = out['black_pop'] / out['total_pop']
    out['pct_hispanic'] = out['hispanic_pop'] / out['total_pop']

    keep = [
        'FIPS', 'NAME', 'total_pop', 'median_age', 'median_hh_income',
        'pct_college', 'pct_unemployed', 'pct_white_nh', 'pct_black', 'pct_hispanic',
    ]
    return out[keep]


def parse_bls_laus(path):
    """Parse BLS LAUS JSON from API, return state-level unemployment rate change 2020-2024."""
    import json

    with open(path) as f:
        records = json.load(f)

    df = pd.DataFrame(records)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['state_fips'] = df['series_id'].str[5:7]

    # try M13 (annual average) first; if absent, average the monthly values
    annual = df[df['period'] == 'M13'].copy()
    if len(annual) == 0:
        # BLS API v1 doesn't return M13, so compute from monthly periods (M01-M12)
        monthly = df[df['period'].str.match(r'^M\d{2}$') & (df['period'] != 'M13')].copy()
        annual = monthly.groupby(['state_fips', 'year'])['value'].mean().reset_index()

    needed = annual[annual['year'].isin([2020, 2024])]

    pivot = needed.pivot_table(
        index='state_fips', columns='year', values='value'
    ).reset_index()

    # handle case where 2024 data might not be complete yet
    cols = list(pivot.columns)
    if 2020 in cols and 2024 in cols:
        pivot = pivot.rename(columns={2020: 'unemp_rate_2020', 2024: 'unemp_rate_2024'})
        pivot['unemp_rate_change'] = pivot['unemp_rate_2024'] - pivot['unemp_rate_2020']
    elif 2020 in cols and 2023 in cols:
        pivot = pivot.rename(columns={2020: 'unemp_rate_2020', 2023: 'unemp_rate_2024'})
        pivot['unemp_rate_change'] = pivot['unemp_rate_2024'] - pivot['unemp_rate_2020']
        print("Note: using 2023 unemployment data (2024 not yet available)")
    else:
        available = [c for c in cols if isinstance(c, (int, float))]
        raise ValueError(f"Expected 2020 and 2024 in BLS data, found years: {available}")

    return pivot[['state_fips', 'unemp_rate_2020', 'unemp_rate_2024', 'unemp_rate_change']]


def parse_nchs(path):
    """Parse NCHS urban-rural classification CSV."""
    df = pd.read_csv(path, encoding='latin-1')

    code_col = [c for c in df.columns if '2013' in c.lower() and 'code' in c.lower()][0]

    # NCHS has separate STFIPS and CTYFIPS columns; combine into 5-digit FIPS
    if 'STFIPS' in df.columns and 'CTYFIPS' in df.columns:
        df['FIPS'] = (
            df['STFIPS'].astype(str).str.zfill(2)
            + df['CTYFIPS'].astype(str).str.zfill(3)
        )
        fips_col = 'FIPS'
    else:
        fips_col = [c for c in df.columns if 'fips' in c.lower()][0]

    out = df[[fips_col, code_col]].copy()
    out.columns = ['FIPS', 'urban_rural_code']
    out['FIPS'] = out['FIPS'].astype(str).str.zfill(5)
    out['urban_rural_code'] = pd.to_numeric(out['urban_rural_code'], errors='coerce')

    labels = {
        1: 'Large central metro',
        2: 'Large fringe metro',
        3: 'Medium metro',
        4: 'Small metro',
        5: 'Micropolitan',
        6: 'Noncore (rural)',
    }
    out['urban_rural_label'] = out['urban_rural_code'].map(labels)

    return out


def parse_gazetteer(path):
    """Parse Census gazetteer, return FIPS and land area in sq miles."""
    df = pd.read_csv(path, sep='\t', dtype=str)
    df.columns = df.columns.str.strip()

    geoid_col = [c for c in df.columns if 'GEOID' in c.upper()][0]
    area_col = [c for c in df.columns if 'ALAND_SQMI' in c.upper()][0]

    out = df[[geoid_col, area_col]].copy()
    out.columns = ['FIPS', 'land_area_sqmi']
    out['FIPS'] = out['FIPS'].str.zfill(5)
    out['land_area_sqmi'] = pd.to_numeric(out['land_area_sqmi'], errors='coerce')

    return out
