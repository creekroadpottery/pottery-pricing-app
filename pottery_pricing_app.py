
import streamlit as st
import pandas as pd
import json
import datetime as _dt


st.set_page_config(page_title="Pottery Cost Analysis App", layout="wide")
ss = st.session_state



# ------------ Helpers ------------
def ensure_cols(df, schema: dict):
    if df is None or df.empty:
        return pd.DataFrame(columns=list(schema.keys()))
    
    df = df.copy()
    
    # Add missing columns
    for col, default in schema.items():
        if col not in df.columns:
            df[col] = default
    
    # Keep only schema columns in correct order
    df = df[list(schema.keys())]
    
    return df

# ------------ Unified Form Management System ------------
UNIFIED_FORM_SCHEMA = {
    "Form": "",
    "Clay_lb_wet": 0.0,
    "Default_glaze_g": 0.0,
    "Throwing_min": 0.0,
    "Trimming_min": 0.0,
    "Handling_min": 0.0,
    "Glazing_min": 0.0,
    "Pieces_per_shelf": 0,
    "Notes": ""
}

def migrate_to_unified_forms():
    """Migrate from 3 separate form databases to 1 unified one"""
    unified = pd.DataFrame(columns=list(UNIFIED_FORM_SCHEMA.keys()))
    
    # Migrate from form_presets_df (clay + glaze data)
    if "form_presets_df" in ss and not ss.form_presets_df.empty:
        for _, row in ss.form_presets_df.iterrows():
            new_row = {
                "Form": str(row.get("Form", "")).strip(),
                "Clay_lb_wet": float(row.get("Clay_lb_wet", 0.0)),
                "Default_glaze_g": float(row.get("Default_glaze_g", 0.0)),
                "Throwing_min": 0.0,  # defaults
                "Trimming_min": 0.0,
                "Handling_min": 0.0,
                "Glazing_min": 0.0,
                "Pieces_per_shelf": 0,
                "Notes": str(row.get("Notes", "")).strip()
            }
            unified = pd.concat([unified, pd.DataFrame([new_row])], ignore_index=True)
    
    # Migrate from production_forms (timing data)
    if "production_forms" in ss and not ss.production_forms.empty:
        for _, row in ss.production_forms.iterrows():
            form_name = str(row.get("Form", "")).strip()
            if not form_name:
                continue
                
            # Check if this form already exists from presets
            existing_idx = unified[unified["Form"] == form_name].index
            if len(existing_idx) > 0:
                # Update existing row with timing data
                idx = existing_idx[0]
                unified.at[idx, "Throwing_min"] = float(row.get("Throwing_min", 0.0))
                unified.at[idx, "Trimming_min"] = float(row.get("Trimming_min", 0.0))
                unified.at[idx, "Handling_min"] = float(row.get("Handling_min", 0.0))
                unified.at[idx, "Glazing_min"] = float(row.get("Glazing_min", 0.0))
                unified.at[idx, "Pieces_per_shelf"] = int(row.get("Pieces_per_shelf", 0))
                # Merge notes
                existing_notes = str(unified.at[idx, "Notes"]).strip()
                new_notes = str(row.get("Notes", "")).strip()
                if existing_notes and new_notes and existing_notes != new_notes:
                    unified.at[idx, "Notes"] = f"{existing_notes} | {new_notes}"
                elif new_notes:
                    unified.at[idx, "Notes"] = new_notes
            else:
                # Add new row with timing data
                new_row = {
                    "Form": form_name,
                    "Clay_lb_wet": 0.0,  # defaults
                    "Default_glaze_g": 0.0,
                    "Throwing_min": float(row.get("Throwing_min", 0.0)),
                    "Trimming_min": float(row.get("Trimming_min", 0.0)),
                    "Handling_min": float(row.get("Handling_min", 0.0)),
                    "Glazing_min": float(row.get("Glazing_min", 0.0)),
                    "Pieces_per_shelf": int(row.get("Pieces_per_shelf", 0)),
                    "Notes": str(row.get("Notes", "")).strip()
                }
                unified = pd.concat([unified, pd.DataFrame([new_row])], ignore_index=True)
    
    # Migrate from custom_forms (user timing data)
    if "custom_forms" in ss and not ss.custom_forms.empty:
        for _, row in ss.custom_forms.iterrows():
            form_name = str(row.get("Form", "")).strip()
            if not form_name:
                continue
                
            # Check if this form already exists
            existing_idx = unified[unified["Form"] == form_name].index
            if len(existing_idx) > 0:
                # Update existing row
                idx = existing_idx[0]
                unified.at[idx, "Throwing_min"] = float(row.get("Throwing_min", 0.0))
                unified.at[idx, "Trimming_min"] = float(row.get("Trimming_min", 0.0))
                unified.at[idx, "Handling_min"] = float(row.get("Handling_min", 0.0))
                unified.at[idx, "Glazing_min"] = float(row.get("Glazing_min", 0.0))
                unified.at[idx, "Pieces_per_shelf"] = int(row.get("Pieces_per_shelf", 0))
                # Merge notes
                existing_notes = str(unified.at[idx, "Notes"]).strip()
                new_notes = str(row.get("Notes", "")).strip()
                if existing_notes and new_notes and existing_notes != new_notes:
                    unified.at[idx, "Notes"] = f"{existing_notes} | {new_notes}"
                elif new_notes:
                    unified.at[idx, "Notes"] = new_notes
            else:
                # Add new row
                new_row = {
                    "Form": form_name,
                    "Clay_lb_wet": 0.0,  # defaults
                    "Default_glaze_g": 0.0,
                    "Throwing_min": float(row.get("Throwing_min", 0.0)),
                    "Trimming_min": float(row.get("Trimming_min", 0.0)),
                    "Handling_min": float(row.get("Handling_min", 0.0)),
                    "Glazing_min": float(row.get("Glazing_min", 0.0)),
                    "Pieces_per_shelf": int(row.get("Pieces_per_shelf", 0)),
                    "Notes": str(row.get("Notes", "")).strip()
                }
                unified = pd.concat([unified, pd.DataFrame([new_row])], ignore_index=True)
    
    # Remove duplicates and clean up
    unified = unified.drop_duplicates(subset=["Form"], keep="last").reset_index(drop=True)
    
    # Ensure proper data types
    for col, default_val in UNIFIED_FORM_SCHEMA.items():
        if col not in unified.columns:
            unified[col] = default_val
        if isinstance(default_val, str):
            unified[col] = unified[col].astype(str).str.strip()
        elif isinstance(default_val, float):
            unified[col] = pd.to_numeric(unified[col], errors="coerce").fillna(default_val).astype(float)
        elif isinstance(default_val, int):
            unified[col] = pd.to_numeric(unified[col], errors="coerce").fillna(default_val).astype(int)
    
    return unified[list(UNIFIED_FORM_SCHEMA.keys())]

def init_unified_forms():
    """Initialize unified form system, migrating from old system if needed"""
    if "unified_forms" not in ss:
        # First time - migrate from old system
        ss.unified_forms = migrate_to_unified_forms()
        
        # If migration resulted in empty dataframe, load defaults
        if ss.unified_forms.empty:
            ss.unified_forms = load_default_presets_unified()
        
        # Mark migration as complete
        ss._forms_migrated = True
    
    # Ensure dataframe has correct structure
    ss.unified_forms = ensure_cols(ss.unified_forms, UNIFIED_FORM_SCHEMA)

def load_default_presets_unified() -> pd.DataFrame:
    """Load default presets in unified format"""
    # Built-in fallback data (Sharon's starter list)
    fallback_data = [
        {"Form": "Mug (12 oz)", "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "straight"},
        {"Form": "Mug (14 oz)", "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
        {"Form": "Creamer (small)", "Clay_lb_wet": 0.75, "Default_glaze_g": 93, "Notes": ""},
        {"Form": "Pitcher (medium)", "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
        {"Form": "Bowl (cereal)", "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "≈6\""},
        {"Form": "Bowl (small)", "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
        {"Form": "Bowl (medium)", "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
        {"Form": "Bowl (large)", "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
        {"Form": "Plate (10 in dinner)", "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
        {"Form": "Pie plate", "Clay_lb_wet": 3.25, "Default_glaze_g": 403, "Notes": "3¼–3½ lb"},
        {"Form": "Sugar jar", "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
        {"Form": "Honey jar", "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
        {"Form": "Crock (small)", "Clay_lb_wet": 1.75, "Default_glaze_g": 218, "Notes": ""},
        {"Form": "Crock (medium)", "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
        {"Form": "Crock (large)", "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
    ]
    
    unified = pd.DataFrame(columns=list(UNIFIED_FORM_SCHEMA.keys()))
    
    for preset in fallback_data:
        new_row = {
            "Form": str(preset.get("Form", "")).strip(),
            "Clay_lb_wet": float(preset.get("Clay_lb_wet", 0.0)),
            "Default_glaze_g": float(preset.get("Default_glaze_g", 0.0)),
            "Throwing_min": 0.0,  # Default timing - users can customize
            "Trimming_min": 0.0,
            "Handling_min": 0.0,
            "Glazing_min": 6.0,  # Default 6 min glazing
            "Pieces_per_shelf": 12,  # Default shelf capacity
            "Notes": str(preset.get("Notes", "")).strip()
        }
        unified = pd.concat([unified, pd.DataFrame([new_row])], ignore_index=True)
    
    return ensure_cols(unified, UNIFIED_FORM_SCHEMA)

# Initialize unified form system
init_unified_forms()
def apply_quick_defaults():
    """Apply sensible defaults for quick start mode."""
    defaults = {
        'clay_price_per_bag': 50.0,
        'clay_bag_weight_lb': 25.0,
        'clay_yield': 0.9,
        'packaging_per_piece': 0.5,
        'kwh_rate': 0.24,  # Al's actual rate
        'kwh_bisque': 30.0,
        'kwh_glaze': 35.0,
        'kwh_third': 0.0,
        'pieces_per_electric_firing': 40,
        'labor_rate': 15.0,
        'overhead_per_month': 500.0,
        'pieces_per_month': 200,
        'fuel_gas': 'Propane',  # Default to propane
        'lp_price_per_gal': 3.50,
        'lp_gal_bisque': 4.7,  # Al's real usage
        'lp_gal_glaze': 9.4,   # Al's real usage
        'pieces_per_gas_firing': 40,
        'use_2x2x2': False,
        'wholesale_margin_pct': 50,
        'retail_multiplier': 2.0,
    }
    
    # Only set defaults if they haven't been set yet
    for key, default_val in defaults.items():
        if key not in ss.inputs:
            ss.inputs[key] = default_val

def get_common_materials_list():
    """Returns a list of common ceramic materials for searchable dropdown"""
    return [
        # Feldspars
        "Custer Feldspar", "F-4 Feldspar", "G-200 Feldspar", "Minspar 200", "NC-4 Feldspar",
        "K-200 Feldspar", "Kingman Feldspar", "Cornwall Stone", "Nepheline Syenite",
        
        # Silica sources
        "Flint (Silica)", "Silica Sand", "Quartz", "Cristobalite",
        
        # Clays and Kaolins
        "EPK Kaolin", "Grolleg Kaolin", "OM4 Ball Clay", "Kentucky Ball Clay", "Redart Clay",
        "Fire Clay", "Albany Slip Clay", "Goldart Stoneware Clay", "Hawthorne Bond Clay",
        
        # Fluxes
        "Gerstley Borate", "Whiting (Calcium Carbonate)", "Wollastonite", "Dolomite",
        "Magnesium Carbonate", "Barium Carbonate", "Strontium Carbonate", "Lithium Carbonate",
        "Pearl Ash (Potassium Carbonate)", "Soda Ash (Sodium Carbonate)", "Borax",
        
        # Frits
        "Frit 3124", "Frit 3134", "Frit 3195", "Frit 3249", "Frit 3269", "Frit 3278",
        "Frit 90", "Frit 25", "Frit 169", "Pemco P-54", "Pemco P-311",
        
        # Colorants (Oxides)
        "Red Iron Oxide", "Black Iron Oxide", "Yellow Iron Oxide", "Cobalt Oxide",
        "Cobalt Carbonate", "Copper Oxide", "Copper Carbonate", "Chrome Oxide",
        "Chromium Oxide", "Tin Oxide", "Titanium Dioxide", "Rutile", "Ilmenite",
        "Manganese Dioxide", "Manganese Carbonate", "Nickel Oxide", "Vanadium Pentoxide",
        
        # Colorants (Stains)
        "Mason 6020 Black", "Mason 6006 Blue", "Mason 6021 Brown", "Mason 6304 Coral",
        "Mason 6242 Crimson", "Mason 6226 Golden Yellow", "Mason 6120 Green",
        
        # Specialty materials
        "Bentonite", "Zircopax (Zirconium Silicate)", "Superpax", "Zinc Oxide",
        "Talc", "Pyrophyllite", "Spodumene", "Petalite", "Bone Ash", "Wood Ash",
        "Alumina Hydrate", "Calcined Alumina", "CMC (Carboxymethyl Cellulose)", "Veegum T"
    ]

def ensure_cols(df, schema: dict):
    if df is None:
        df = pd.DataFrame()
    else:
        df = df.copy()
    for col, default in schema.items():
        if col not in df.columns:
            df[col] = default
    df = df[list(schema.keys())]
    for col, default in schema.items():
        if isinstance(default, str):
            df[col] = df[col].astype(str)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default).astype(float)
    return df

def money(n):
    try:
        return f"${n:,.2f}"
    except Exception:
        return "$0.00"

def to_json_bytes(obj):
    return json.dumps(obj, indent=2).encode("utf-8")

def from_json_bytes(b):
    return json.loads(b.decode("utf-8"))

def other_materials_pp(df, pieces_in_project: int):
    df2 = ensure_cols(df, {
        "Item":"", "Unit":"", "Cost_per_unit":0.0, "Quantity_for_project":0.0
    }).copy()
    df2["Line_total"] = df2["Cost_per_unit"] * df2["Quantity_for_project"]
    project_total = float(df2["Line_total"].sum())
    per_piece = project_total / max(1, int(pieces_in_project))
    df2["Cost_per_piece"] = df2["Line_total"] / max(1, int(pieces_in_project))
    return per_piece, project_total, df2
# ---- Tariff rates loader (local JSON or URL) ----
@st.cache_data
def load_tariff_table(local_path: str = "tariff_rates.json", url: str = "") -> pd.DataFrame:
    df = pd.DataFrame(columns=["HS_code", "Description", "Country", "Duty_rate", "VAT_rate"])
    # try local first
    try:
        df = pd.read_json(local_path)
    except Exception:
        pass
    # optional URL override
    if url:
        try:
            df = pd.read_json(url)
        except Exception:
            pass
    # normalize columns
    for col in ["HS_code", "Description", "Country"]:
        if col not in df.columns:
            df[col] = ""
    for col in ["Duty_rate", "VAT_rate"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    # clean
    df["HS_code"] = df["HS_code"].astype(str).str.strip()
    df["Country"] = df["Country"].astype(str).str.strip()
    return df[["HS_code", "Description", "Country", "Duty_rate", "VAT_rate"]]


# --- Form presets: loader + initializer --------------------------------------
@st.cache_data(show_spinner=False)
def load_default_presets() -> pd.DataFrame:
    """
    Loads presets from your GitHub RAW CSV.
    Falls back to a built-in 'Sharon set' if the CSV can't be read.
    Columns: Form, Clay_lb_wet, Default_glaze_g, Notes
    """
    cols = {"Form": "", "Clay_lb_wet": 0.0, "Default_glaze_g": 0.0, "Notes": ""}

    # Try your repo first (RAW URL)
    url = "https://raw.githubusercontent.com/creekroadpottery/pottery-pricing-app/main/form_presets.csv"
    try:
        df = pd.read_csv(url)
        for c, d in cols.items():
            if c not in df.columns:
                df[c] = d
        return df[list(cols.keys())]
    except Exception:
        pass

    # Fallback: Sharon’s starter list (edit/expand anytime)
    fallback = pd.DataFrame(
        [
            {"Form": "Mug (12 oz)",              "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "straight"},
            {"Form": "Mug (14 oz)",              "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Creamer (small)",          "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Pitcher (medium)",         "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Bowl (cereal)",            "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "≈6\""},
            {"Form": "Bowl (small)",             "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Bowl (medium)",            "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Bowl (large)",             "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Plate (10 in dinner)",     "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Pie plate",                "Clay_lb_wet": 3.25, "Default_glaze_g": 403, "Notes": "3¼–3½ lb"},
            {"Form": "Sugar jar",                "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Honey jar",                "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Crock (small)",            "Clay_lb_wet": 1.75, "Default_glaze_g": 218, "Notes": ""},
            {"Form": "Crock (medium)",           "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Crock (large)",            "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Small cup",                       "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": "8 oz"},
            {"Form": "Tumbler",                         "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": "12 oz"},
            {"Form": "Beer mug",                        "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "20 oz"},
            {"Form": "Travel mug",                      "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "with handle"},
            {"Form": "Soup bowl",                       "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "shallow"},
            {"Form": "Ramen bowl",                      "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "deep"},
            {"Form": "Mixing bowl (small)",             "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "≈8 in"},
            {"Form": "Mixing bowl (medium)",            "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "≈10 in"},
            {"Form": "Mixing bowl (large)",             "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "≈12 in"},
            {"Form": "Salad bowl (family)",             "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "≈14 in wide"},
            {"Form": "Small plate (6 in)",              "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Dessert plate (8 in)",            "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Dinner plate (10 in)",            "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Charger plate (12 in)",           "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Serving platter (small oval)",    "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "oval"},
            {"Form": "Serving platter (medium 14 in)",  "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "round"},
            {"Form": "Serving platter (large 16 in)",   "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": "round"},
            {"Form": "Pasta bowl (wide rim)",           "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Pie dish (9 in)",                 "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Casserole (small, with lid)",     "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Casserole (medium, with lid)",    "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Casserole (large, with lid)",     "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Covered jar (small)",             "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "lidded"},
            {"Form": "Covered jar (medium)",            "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "lidded"},
            {"Form": "Covered jar (large)",             "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "lidded"},
            {"Form": "Pitcher (small)",                 "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Pitcher (medium)",                "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Pitcher (large)",                 "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Teapot (2-cup)",                  "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "with lid"},
            {"Form": "Teapot (4-cup)",                  "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "with lid"},
            {"Form": "Teapot (6-cup)",                  "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "with lid"},
            {"Form": "Teapot (8-cup)",                  "Clay_lb_wet": 6.50, "Default_glaze_g": 806, "Notes": "with lid"},
            {"Form": "Sugar jar",                       "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Creamer",                         "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": "spout"},
            {"Form": "Butter dish (with lid)",          "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Salt cellar",                     "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Sponge holder",                   "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": "cutouts"},
            {"Form": "Utensil crock (small)",           "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "tall"},
            {"Form": "Utensil crock (large)",           "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "tall"},
            {"Form": "Planter (4 in)",                  "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "drainage"},
            {"Form": "Planter (6 in)",                  "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "drainage"},
            {"Form": "Planter (8 in)",                  "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "drainage"},
            {"Form": "Planter (10 in)",                 "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "drainage"},
            {"Form": "Vase (bud, 5 in)",                "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Vase (medium, 8 in)",             "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Vase (tall, 12 in)",              "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Luminary (small)",                "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "cutouts"},
            {"Form": "Luminary (large)",                "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "cutouts"},
            {"Form": "Baking dish (small rectangular)", "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Baking dish (large rectangular)", "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Loaf pan (small)",               "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Loaf pan (large)",               "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Batter bowl (with handle)",      "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "pour spout"},
            {"Form": "Serving dish (oval, small)",     "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Serving dish (oval, medium)",    "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Serving dish (oval, large)",     "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Chip & dip platter",             "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "with center bowl"},
            {"Form": "Cake stand (small)",             "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "6–8 in top"},
            {"Form": "Cake stand (large)",             "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "10–12 in top"},
            {"Form": "Covered butter keeper",          "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "French style"},
            {"Form": "Egg baker",                      "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Soup tureen (small)",            "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "with lid"},
            {"Form": "Soup tureen (large)",            "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "with lid"},
            {"Form": "Gravy boat",                     "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "with saucer"},
            {"Form": "Serving spoon rest",             "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Oil cruet",                      "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "pour spout"},
            {"Form": "Honey pot",                      "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "with lid & dipper"},
            {"Form": "Garlic keeper",                  "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "pierced"},
            {"Form": "Salsa bowl",                     "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Dip bowl (small)",               "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Dip bowl (medium)",              "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Dip bowl (large)",               "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Fruit bowl (small)",             "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Fruit bowl (large)",             "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Berry bowl (pierced)",           "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "strainer style"},
            {"Form": "Colander (small)",               "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "with handles"},
            {"Form": "Colander (large)",               "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "with handles"},
            {"Form": "Pasta bowl (individual)",        "Clay_lb_wet": 1.75, "Default_glaze_g": 218, "Notes": ""},
            {"Form": "Serving bowl (extra large)",     "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": ""},
            {"Form": "Ice cream bowl",                 "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Candle holder (taper)",          "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Candle holder (pillar)",         "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Lantern (pierced)",              "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Incense burner (cone)",          "Clay_lb_wet": 0.50, "Default_glaze_g": 62,  "Notes": ""},
            {"Form": "Incense burner (stick)",         "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Wall pocket vase",               "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Wall planter",                   "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "flat back"},
            {"Form": "Hanging planter (small)",        "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "with holes"},
            {"Form": "Hanging planter (large)",        "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "with holes"},
            {"Form": "Orchid pot (pierced)",           "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Succulent planter (tiny)",       "Clay_lb_wet": 0.50, "Default_glaze_g": 62,  "Notes": "2–3 in"},
            {"Form": "Succulent planter (medium)",     "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "4–5 in"},
            {"Form": "Succulent planter (large)",      "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "6–7 in"},
            {"Form": "Mortar & pestle (small)",        "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "with pestle"},
            {"Form": "Mortar & pestle (large)",        "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "with pestle"},
            {"Form": "Soup mug (with handle)",         "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Handled bowl (breakfast)",       "Clay_lb_wet": 1.75, "Default_glaze_g": 218, "Notes": ""},
            {"Form": "Pet bowl (small)",               "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Pet bowl (large)",               "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Water dish (animal trough)",     "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "sturdy"},
            {"Form": "Wine goblet (small)",         "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "stemmed"},
            {"Form": "Wine goblet (large)",         "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": "stemmed"},
            {"Form": "Beer stein (straight)",       "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "20 oz"},
            {"Form": "Beer stein (tapered)",        "Clay_lb_wet": 2.25, "Default_glaze_g": 279, "Notes": "24 oz"},
            {"Form": "Tankard",                     "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "handle"},
            {"Form": "Shot glass",                  "Clay_lb_wet": 0.40, "Default_glaze_g": 50,  "Notes": "single"},
            {"Form": "Whiskey tumbler",             "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "lowball"},
            {"Form": "Highball glass",              "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "tall"},
            {"Form": "Cocktail coupe",              "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Martini glass",               "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Pitcher (extra large)",       "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": "gallon size"},
            {"Form": "Serving bowl (pasta)",        "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "wide"},
            {"Form": "Serving bowl (salad)",        "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": "extra large"},
            {"Form": "Mixing bowl (small)",         "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Mixing bowl (medium)",        "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Mixing bowl (large)",         "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Mortar bowl",                 "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "with pestle"},
            {"Form": "Colander (small)",            "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "with holes"},
            {"Form": "Colander (large)",            "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "with holes"},
            {"Form": "Fruit bowl (small)",          "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Fruit bowl (large)",          "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Chip and dip platter",        "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "center dip"},
            {"Form": "Deviled egg platter",         "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "indents"},
            {"Form": "Butter dish",                 "Clay_lb_wet": 2.25, "Default_glaze_g": 279, "Notes": "with lid"},
            {"Form": "Cheese dome",                 "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "with plate"},
            {"Form": "Cake stand",                  "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": "pedestal"},
            {"Form": "Cupcake stand",               "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "tiered"},
            {"Form": "Serving spoon rest",          "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Chopstick rest",              "Clay_lb_wet": 0.25, "Default_glaze_g": 31,  "Notes": ""},
            {"Form": "Sushi plate (small)",         "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Sushi plate (large)",         "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Soy sauce dish",              "Clay_lb_wet": 0.40, "Default_glaze_g": 50,  "Notes": ""},
            {"Form": "Rice bowl",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Donburi bowl",                "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "Japanese large rice bowl"},
            {"Form": "Noodle bowl",                 "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "ramen"},
            {"Form": "Soup tureen",                 "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": "with lid"},
            {"Form": "Handled soup bowl",           "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": "with handle"},
            {"Form": "Handled casserole",           "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "with lid"},
            {"Form": "Bread pan",                   "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Loaf pan",                    "Clay_lb_wet": 3.75, "Default_glaze_g": 465, "Notes": ""},
            {"Form": "Bundt pan",                   "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Muffin pan (6 cup)",          "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Muffin pan (12 cup)",         "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Tart pan (small)",            "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Tart pan (large)",            "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Candle holder (small)",       "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": "votive"},
            {"Form": "Candle holder (taper)",       "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Candle holder (pillar)",      "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Lamp base (small)",           "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Lamp base (large)",           "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Vase (bud)",                  "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Vase (small)",                "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Vase (medium)",               "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Vase (large)",                "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Vase (floor)",                "Clay_lb_wet": 12.0, "Default_glaze_g": 1488,"Notes": "tall"},
            {"Form": "Urn (small)",                 "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Urn (medium)",                "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Urn (large)",                 "Clay_lb_wet": 10.0, "Default_glaze_g": 1240,"Notes": ""},
            {"Form": "Planter (small)",             "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Planter (medium)",            "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Planter (large)",             "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Hanging planter",             "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "with holes"},
            {"Form": "Wall planter",                "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "flat back"},
            {"Form": "Teapot (1 cup)",              "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "body only"},
            {"Form": "Teapot (2 cup)",              "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Teapot (4 cup)",              "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Teapot (6 cup)",              "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": ""},
            {"Form": "Teapot lid (small)",          "Clay_lb_wet": 0.40, "Default_glaze_g": 50,  "Notes": ""},
            {"Form": "Teapot lid (medium)",         "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": ""},
            {"Form": "Teapot lid (large)",          "Clay_lb_wet": 0.80, "Default_glaze_g": 100, "Notes": ""},
            {"Form": "Jar (1 pint)",                "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Jar (1 quart)",               "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Jar (half gallon)",           "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Jar (1 gallon)",              "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Cookie jar",                  "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "with lid"},
            {"Form": "Canister (small)",            "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "with lid"},
            {"Form": "Canister (medium)",           "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Canister (large)",            "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Storage jar (extra large)",   "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Pitcher (small)",             "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Pitcher (medium)",            "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Pitcher (large)",             "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Tankard pitcher",             "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "sturdy"},
            {"Form": "Ewer (decorative pitcher)",   "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Oil cruet",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "pouring spout"},
            {"Form": "Vinegar cruet",               "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "pouring spout"},
            {"Form": "Salt cellar",                 "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": "with lid"},
            {"Form": "Pepper cellar",               "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": ""},
            {"Form": "Spice jar",                   "Clay_lb_wet": 0.80, "Default_glaze_g": 100, "Notes": ""},
            {"Form": "Honey pot",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "with lid and dipper"},
            {"Form": "Garlic keeper",               "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "vent holes"},
            {"Form": "Olive dish",                  "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "elongated"},
            {"Form": "Relish tray",                 "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "compartments"},
            {"Form": "Serving tray (small)",        "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Serving tray (medium)",       "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Serving tray (large)",        "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Serving tray (extra large)",  "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Oval platter",                "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Rectangular platter",         "Clay_lb_wet": 6.50, "Default_glaze_g": 806, "Notes": ""},
            {"Form": "Square platter",              "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Chip and dip tray",           "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "attached bowl"},
            {"Form": "Deviled egg tray",            "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "12 wells"},
            {"Form": "Cake plate (8 in)",           "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "footed"},
            {"Form": "Cake plate (10 in)",          "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Cake plate (12 in)",          "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Cake stand (small)",          "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Cake stand (large)",          "Clay_lb_wet": 7.50, "Default_glaze_g": 930, "Notes": ""},
            {"Form": "Pie plate (8 in)",            "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Pie plate (9 in)",            "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Pie plate (10 in)",           "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Tart pan (8 in)",             "Clay_lb_wet": 2.25, "Default_glaze_g": 279, "Notes": "fluted"},
            {"Form": "Tart pan (10 in)",            "Clay_lb_wet": 2.75, "Default_glaze_g": 341, "Notes": ""},
            {"Form": "Tart pan (12 in)",            "Clay_lb_wet": 3.25, "Default_glaze_g": 403, "Notes": ""},
            {"Form": "Bread pan (standard)",        "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Bread pan (large)",          "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Lasagna pan (small)",        "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Lasagna pan (large)",        "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Casserole (1 qt)",           "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "with lid"},
            {"Form": "Casserole (2 qt)",           "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "with lid"},
            {"Form": "Casserole (3 qt)",           "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Casserole (4 qt)",           "Clay_lb_wet": 7.50, "Default_glaze_g": 930, "Notes": ""},
            {"Form": "Covered casserole (small)",  "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Covered casserole (large)",  "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": ""},
            {"Form": "Dutch oven (small)",         "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Dutch oven (large)",         "Clay_lb_wet": 9.00, "Default_glaze_g": 1116,"Notes": ""},
            {"Form": "Soup tureen (small)",        "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": ""},
            {"Form": "Soup tureen (large)",        "Clay_lb_wet": 10.0, "Default_glaze_g": 1240,"Notes": ""},
            {"Form": "Stew pot",                   "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Bean pot",                   "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "with lid"},
            {"Form": "Sauce pot (small)",          "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Sauce pot (medium)",         "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Sauce pot (large)",          "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": ""},
            {"Form": "Baker (small)",              "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Baker (medium)",             "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Baker (large)",              "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Baker (rectangular)",        "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Pizza stone (12 in)",        "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Pizza stone (14 in)",        "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": ""},
            {"Form": "Pizza stone (16 in)",        "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Pizza pan (12 in)",          "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Pizza pan (14 in)",          "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Pizza pan (16 in)",          "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Tagine (small)",             "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": "with lid"},
            {"Form": "Tagine (large)",             "Clay_lb_wet": 7.50, "Default_glaze_g": 930, "Notes": ""},
            {"Form": "Gratin dish (small)",        "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Gratin dish (medium)",       "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Gratin dish (large)",        "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Soufflé dish (small)",       "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Soufflé dish (medium)",      "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Soufflé dish (large)",       "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Mixing bowl (1 qt)",         "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Mixing bowl (2 qt)",         "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Mixing bowl (3 qt)",         "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Mixing bowl (4 qt)",         "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Mixing bowl (5 qt)",         "Clay_lb_wet": 7.50, "Default_glaze_g": 930, "Notes": ""},
            {"Form": "Colander (small)",           "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "pierced"},
            {"Form": "Colander (large)",           "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Berry bowl",                 "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "holes, drip plate"},
            {"Form": "Strainer bowl",              "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Salad bowl (8 in)",          "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Salad bowl (10 in)",         "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Salad bowl (12 in)",         "Clay_lb_wet": 6.50, "Default_glaze_g": 806, "Notes": ""},
            {"Form": "Punch bowl (large)",         "Clay_lb_wet": 10.0, "Default_glaze_g": 1240,"Notes": ""},
            {"Form": "Serving bowl (small)",       "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Serving bowl (medium)",      "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Serving bowl (large)",       "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Serving bowl (XL)",          "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Serving platter (oval)",     "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Serving platter (rect)",     "Clay_lb_wet": 7.50, "Default_glaze_g": 930, "Notes": ""},
            {"Form": "Serving platter (round)",    "Clay_lb_wet": 8.00, "Default_glaze_g": 992, "Notes": ""},
            {"Form": "Serving tray (handles)",     "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Chip bowl",                  "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Dip bowl",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Chip-and-dip set",           "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "combined"},
            {"Form": "Soup bowl (shallow)",        "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Soup bowl (deep)",           "Clay_lb_wet": 2.25, "Default_glaze_g": 279, "Notes": ""},
            {"Form": "Stew bowl",                  "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "French onion soup crock",    "Clay_lb_wet": 2.75, "Default_glaze_g": 341, "Notes": "with handles"},
            {"Form": "Soup mug",                   "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Ramen bowl",                 "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "deep, wide"},
            {"Form": "Pho bowl",                   "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Pasta bowl (wide)",          "Clay_lb_wet": 2.75, "Default_glaze_g": 341, "Notes": ""},
            {"Form": "Pasta bowl (deep)",          "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Ice cream bowl",             "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Dessert bowl",               "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Custard cup",                "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Ramekin (small)",            "Clay_lb_wet": 0.80, "Default_glaze_g": 100, "Notes": ""},
            {"Form": "Ramekin (large)",            "Clay_lb_wet": 1.20, "Default_glaze_g": 149, "Notes": ""},
            {"Form": "Pudding bowl",               "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Trifle bowl",                "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Compote dish (small)",       "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "stemmed"},
            {"Form": "Compote dish (large)",       "Clay_lb_wet": 2.25, "Default_glaze_g": 279, "Notes": ""},
            {"Form": "Candy dish",                 "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Nut bowl",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Relish tray (3-part)",       "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Relish tray (5-part)",       "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Divided dish",               "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Butter dish (tray)",         "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Butter dish (covered)",      "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "with lid"},
            {"Form": "Mug (12 oz)",                 "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "straight"},
            {"Form": "Mug (14 oz)",                 "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Creamer (small)",             "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": ""},
            {"Form": "Pitcher (medium)",            "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Bowl (cereal)",               "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "≈6\""},
            {"Form": "Bowl (small)",                "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Bowl (medium)",               "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Bowl (large)",                "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": ""},
            {"Form": "Plate (10 in dinner)",        "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Pie plate",                   "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": "3¼–3½ lb"},
            {"Form": "Sugar jar",                   "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Honey jar",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Crock (small)",               "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": ""},
            {"Form": "Crock (medium)",              "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Crock (large)",               "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Small cup",                   "Clay_lb_wet": 0.75, "Default_glaze_g": 93,  "Notes": "8 oz"},
            {"Form": "Tumbler",                     "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": "12 oz"},
            {"Form": "Beer mug",                    "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "20 oz"},
            {"Form": "Travel mug",                  "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": "with handle"},
            {"Form": "Soup bowl",                   "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": "shallow"},
            {"Form": "Ramen bowl",                  "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "deep"},
            {"Form": "Mixing bowl (small)",         "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "≈8 in"},
            {"Form": "Mixing bowl (medium)",        "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "≈10 in"},
            {"Form": "Mixing bowl (large)",         "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": "≈12 in"},
            {"Form": "Pasta bowl (wide)",           "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": ""},
            {"Form": "Serving bowl (small)",        "Clay_lb_wet": 2.75, "Default_glaze_g": 342, "Notes": ""},
            {"Form": "Serving bowl (medium)",       "Clay_lb_wet": 3.75, "Default_glaze_g": 465, "Notes": ""},
            {"Form": "Serving bowl (large)",        "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": ""},
            {"Form": "Salad bowl (medium)",         "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": ""},
            {"Form": "Salad bowl (large)",          "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Batter bowl (small)",         "Clay_lb_wet": 2.75, "Default_glaze_g": 342, "Notes": "with spout"},
            {"Form": "Batter bowl (large)",         "Clay_lb_wet": 4.25, "Default_glaze_g": 528, "Notes": "with handle"},
            {"Form": "Casserole (1 qt, covered)",   "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": ""},
            {"Form": "Casserole (2 qt, covered)",   "Clay_lb_wet": 4.25, "Default_glaze_g": 528, "Notes": ""},
            {"Form": "Baker (rect, small)",         "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Baker (rect, large)",         "Clay_lb_wet": 5.00, "Default_glaze_g": 620, "Notes": ""},
            {"Form": "Bread pan",                   "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Lasagna pan",                 "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Gratin dish (oval)",          "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": ""},
            {"Form": "Tart pan (9 in)",             "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": ""},
            {"Form": "Quiche dish (9 in)",          "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": ""},
            {"Form": "Custard cup",                 "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": ""},
            {"Form": "Ramekin (large)",             "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": ""},
            {"Form": "Pie bird",                    "Clay_lb_wet": 0.25, "Default_glaze_g": 32,  "Notes": ""},
            {"Form": "Butter dish (covered)",       "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Cheese dome (small)",         "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": "with plate"},
            {"Form": "Chip and dip set",            "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": "2-piece"},
            {"Form": "Relish tray (3-section)",     "Clay_lb_wet": 2.75, "Default_glaze_g": 342, "Notes": ""},
            {"Form": "Divided dish (oval)",         "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Dinner plate (8 in)",         "Clay_lb_wet": 1.80, "Default_glaze_g": 224, "Notes": ""},
            {"Form": "Dinner plate (9 in)",         "Clay_lb_wet": 2.10, "Default_glaze_g": 261, "Notes": ""},
            {"Form": "Dinner plate (10 in)",        "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Dinner plate (11 in)",        "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Dinner plate (12 in)",        "Clay_lb_wet": 3.60, "Default_glaze_g": 447, "Notes": "charger"},
            {"Form": "Salad plate (8 in)",          "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": ""},
            {"Form": "Dessert plate (7 in)",        "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Bread plate (6 in)",          "Clay_lb_wet": 1.10, "Default_glaze_g": 137, "Notes": ""},
            {"Form": "Charger (13 in)",             "Clay_lb_wet": 4.25, "Default_glaze_g": 528, "Notes": ""},
            {"Form": "Sushi plate (rect small)",    "Clay_lb_wet": 1.40, "Default_glaze_g": 174, "Notes": ""},
            {"Form": "Sushi plate (rect large)",    "Clay_lb_wet": 2.20, "Default_glaze_g": 273, "Notes": ""},
            {"Form": "Platter (oval small)",        "Clay_lb_wet": 2.75, "Default_glaze_g": 342, "Notes": ""},
            {"Form": "Platter (oval medium)",       "Clay_lb_wet": 4.00, "Default_glaze_g": 496, "Notes": ""},
            {"Form": "Platter (oval large)",        "Clay_lb_wet": 5.50, "Default_glaze_g": 682, "Notes": ""},
            {"Form": "Platter (rect small)",        "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": ""},
            {"Form": "Platter (rect large)",        "Clay_lb_wet": 5.25, "Default_glaze_g": 651, "Notes": ""},
            {"Form": "Sectional platter",           "Clay_lb_wet": 4.50, "Default_glaze_g": 558, "Notes": "party"},
            {"Form": "Gobo cup (sake)",             "Clay_lb_wet": 0.40, "Default_glaze_g": 50,  "Notes": ""},
            {"Form": "Tea cup (handle-less)",       "Clay_lb_wet": 0.70, "Default_glaze_g": 87,  "Notes": ""},
            {"Form": "Goblet",                      "Clay_lb_wet": 1.25, "Default_glaze_g": 155, "Notes": ""},
            {"Form": "Wine goblet (large)",         "Clay_lb_wet": 1.60, "Default_glaze_g": 199, "Notes": ""},
            {"Form": "Beer stein (heavy)",          "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": ""},
            {"Form": "Highball",                    "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Lowball",                     "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": ""},
            {"Form": "Martini coupe",               "Clay_lb_wet": 1.20, "Default_glaze_g": 149, "Notes": ""},
            {"Form": "Shot cup",                    "Clay_lb_wet": 0.35, "Default_glaze_g": 44,  "Notes": ""},
            {"Form": "Teapot (2-cup)",              "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": "w/ lid"},
            {"Form": "Teapot (4-cup)",              "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": "w/ lid"},
            {"Form": "Creamer (medium)",            "Clay_lb_wet": 1.10, "Default_glaze_g": 137, "Notes": ""},
            {"Form": "Sugar jar (with lid)",        "Clay_lb_wet": 1.40, "Default_glaze_g": 174, "Notes": ""},
            {"Form": "Coffee server",               "Clay_lb_wet": 2.75, "Default_glaze_g": 342, "Notes": "pour spout"},
            {"Form": "Pour-over dripper",           "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "cone"},
            {"Form": "Pitcher (small)",             "Clay_lb_wet": 1.50, "Default_glaze_g": 186, "Notes": ""},
            {"Form": "Pitcher (large)",             "Clay_lb_wet": 3.75, "Default_glaze_g": 465, "Notes": ""},
            {"Form": "Ewer (decorative)",           "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": ""},
            {"Form": "Canister (small)",            "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": "with lid"},
            {"Form": "Canister (medium)",           "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "with lid"},
            {"Form": "Canister (large)",            "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "with lid"},
            {"Form": "Cookie jar",                  "Clay_lb_wet": 3.75, "Default_glaze_g": 465, "Notes": "with lid"},
            {"Form": "Utensil crock",               "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": "tall"},
            {"Form": "Salt pig",                    "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": ""},
            {"Form": "Spice jar",                   "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": ""},
            {"Form": "Butter keeper (water seal)",  "Clay_lb_wet": 1.40, "Default_glaze_g": 174, "Notes": ""},
            {"Form": "Olive dish",                  "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "narrow"},
            {"Form": "Relish dish (long)",          "Clay_lb_wet": 1.20, "Default_glaze_g": 149, "Notes": ""},
            {"Form": "Tray w/ handles (small)",     "Clay_lb_wet": 1.80, "Default_glaze_g": 224, "Notes": ""},
            {"Form": "Tray w/ handles (large)",     "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": ""},
            {"Form": "Deviled egg plate",           "Clay_lb_wet": 2.40, "Default_glaze_g": 298, "Notes": "12 wells"},
            {"Form": "Mortar & pestle (small)",     "Clay_lb_wet": 1.60, "Default_glaze_g": 199, "Notes": ""},
            {"Form": "Mortar & pestle (large)",     "Clay_lb_wet": 2.75, "Default_glaze_g": 342, "Notes": ""},
            {"Form": "Colander (small)",            "Clay_lb_wet": 1.80, "Default_glaze_g": 224, "Notes": "pierced"},
            {"Form": "Colander (large)",            "Clay_lb_wet": 2.80, "Default_glaze_g": 347, "Notes": "pierced"},
            {"Form": "Oil cruet",                   "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "cork"},
            {"Form": "Syrup pitcher",               "Clay_lb_wet": 1.00, "Default_glaze_g": 124, "Notes": ""},
            {"Form": "Soap dispenser bottle",       "Clay_lb_wet": 1.10, "Default_glaze_g": 137, "Notes": "pump"},
            {"Form": "Utensil holder (wide)",       "Clay_lb_wet": 3.75, "Default_glaze_g": 465, "Notes": ""},
            {"Form": "Lamp base (small)",           "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": "wired"},
            {"Form": "Lamp base (large)",           "Clay_lb_wet": 4.25, "Default_glaze_g": 528, "Notes": "wired"},
            {"Form": "Candle holder (taper)",       "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": ""},
            {"Form": "Votive/tea-light",            "Clay_lb_wet": 0.40, "Default_glaze_g": 50,  "Notes": "luminary"},
            {"Form": "Lantern (pierced)",           "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "cutouts"},
            {"Form": "Planter (4 in)",              "Clay_lb_wet": 1.20, "Default_glaze_g": 149, "Notes": "with hole"},
            {"Form": "Planter (6 in)",              "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "with hole"},
            {"Form": "Planter (8 in)",              "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": "with hole"},
            {"Form": "Planter (10 in)",             "Clay_lb_wet": 4.75, "Default_glaze_g": 589, "Notes": "with hole"},
            {"Form": "Hanging planter (small)",     "Clay_lb_wet": 1.75, "Default_glaze_g": 217, "Notes": "with holes"},
            {"Form": "Hanging planter (large)",     "Clay_lb_wet": 3.00, "Default_glaze_g": 372, "Notes": "with holes"},
            {"Form": "Self-watering planter",       "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": "insert"},
            {"Form": "Bird feeder",                 "Clay_lb_wet": 2.00, "Default_glaze_g": 248, "Notes": "hanging"},
            {"Form": "Bird bath (bowl)",            "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "wide"},
            {"Form": "Wind chime tubes (set)",      "Clay_lb_wet": 1.20, "Default_glaze_g": 149, "Notes": "stringing"},
            {"Form": "Wind bell",                   "Clay_lb_wet": 0.90, "Default_glaze_g": 112, "Notes": "clapper"},
            {"Form": "Tile (4×4 in)",               "Clay_lb_wet": 0.40, "Default_glaze_g": 50,  "Notes": ""},
            {"Form": "Tile (6×6 in)",               "Clay_lb_wet": 0.85, "Default_glaze_g": 106, "Notes": ""},
            {"Form": "Trivet (round)",              "Clay_lb_wet": 1.20, "Default_glaze_g": 149, "Notes": "feet"},
            {"Form": "Switch plate (double)",       "Clay_lb_wet": 0.50, "Default_glaze_g": 62,  "Notes": ""},
            {"Form": "Vase (bud)",                  "Clay_lb_wet": 0.80, "Default_glaze_g": 100, "Notes": ""},
            {"Form": "Vase (table)",                "Clay_lb_wet": 2.25, "Default_glaze_g": 280, "Notes": ""},
            {"Form": "Vase (floor)",                "Clay_lb_wet": 6.50, "Default_glaze_g": 807, "Notes": "tall"},
            {"Form": "Urn (small)",                 "Clay_lb_wet": 3.75, "Default_glaze_g": 465, "Notes": "lid"},
            {"Form": "Urn (large)",                 "Clay_lb_wet": 6.00, "Default_glaze_g": 744, "Notes": "lid"},
            {"Form": "Sculpture (small)",           "Clay_lb_wet": 2.50, "Default_glaze_g": 310, "Notes": "figurine"},
            {"Form": "Sculpture (bust)",            "Clay_lb_wet": 7.50, "Default_glaze_g": 930, "Notes": ""},
            {"Form": "Mask (wall)",                 "Clay_lb_wet": 1.40, "Default_glaze_g": 174, "Notes": "hang loop"},
            {"Form": "Clock face (pottery)",        "Clay_lb_wet": 1.60, "Default_glaze_g": 199, "Notes": "fit movement"},
            {"Form": "Sponge holder",               "Clay_lb_wet": 0.60, "Default_glaze_g": 75,  "Notes": "kitchen"},
            {"Form": "Spoon rest",                  "Clay_lb_wet": 0.80, "Default_glaze_g": 100, "Notes": ""},
            {"Form": "Measuring cup (1 cup)",       "Clay_lb_wet": 1.10, "Default_glaze_g": 137, "Notes": "spout"},
            {"Form": "Measuring cup (2 cup)",       "Clay_lb_wet": 1.60, "Default_glaze_g": 199, "Notes": "spout"},
            {"Form": "Gravy boat",                  "Clay_lb_wet": 1.40, "Default_glaze_g": 174, "Notes": "with saucer"},
            {"Form": "Soup tureen (large)",         "Clay_lb_wet": 6.50, "Default_glaze_g": 807, "Notes": "with lid"},
            {"Form": "Tagine (base+lid)",           "Clay_lb_wet": 6.25, "Default_glaze_g": 775, "Notes": "oven"},
            {"Form": "Pizza stone (round)",         "Clay_lb_wet": 5.25, "Default_glaze_g": 651, "Notes": "unglazed surface"},
            {"Form": "Baguette tray",               "Clay_lb_wet": 3.50, "Default_glaze_g": 434, "Notes": "vented"},
            {"Form": "Roaster (oval)",              "Clay_lb_wet": 5.75, "Default_glaze_g": 713, "Notes": "handles"},
            {"Form": "Dutch oven (covered)",        "Clay_lb_wet": 7.00, "Default_glaze_g": 868, "Notes": "heavy"},
            {"Form": "Cloche (bread dome)",         "Clay_lb_wet": 5.75, "Default_glaze_g": 713, "Notes": "base+lid"},
            {"Form": "Watering can (ceramic)",      "Clay_lb_wet": 3.25, "Default_glaze_g": 404, "Notes": "garden"},
            {"Form": "Fountain bowl",               "Clay_lb_wet": 7.25, "Default_glaze_g": 899, "Notes": "outdoor"},
            {"Form": "Wall pocket (planter)",       "Clay_lb_wet": 1.60, "Default_glaze_g": 199, "Notes": "hang loop"},           
            


        ]
    )
    return fallback

def init_form_presets_in_state():
    """Ensure ss.form_presets_df exists and is normalized."""
    if "form_presets_df" not in ss:
        ss.form_presets_df = load_default_presets()

    # Normalize + types
    ss.form_presets_df = ss.form_presets_df.copy()
    ss.form_presets_df["Form"] = ss.form_presets_df["Form"].astype(str).str.strip()
    ss.form_presets_df["Clay_lb_wet"] = pd.to_numeric(ss.form_presets_df["Clay_lb_wet"], errors="coerce").fillna(0.0)
    ss.form_presets_df["Default_glaze_g"] = pd.to_numeric(ss.form_presets_df["Default_glaze_g"], errors="coerce").fillna(0.0)
    if "Notes" not in ss.form_presets_df.columns:
        ss.form_presets_df["Notes"] = ""


# ---------- Preset categorizer ----------
CATEGORY_ORDER = [
    "Mugs and cups",          # most common first
    "Bowls",
    "Plates and platters",
    "Drinkware and bar",
    "Bakeware and ovensafe",
    "Serveware and table",
    "Jars and canisters",
    "Teaware and coffee",
    "Pitchers and ewers",
    "Cookware and kitchen",
    "Lighting and decor",
    "Planters and garden",
    "Tiles and fixtures",
    "Sculpture and art",
    "Specialty and other",
]

def infer_category(name: str) -> str:
    n = str(name).lower()

    # Mugs and cups
    if any(k in n for k in ["mug", "cup", "demitasse", "espresso", "teacup", "soup mug"]):
        return "Mugs and cups"

    # Bowls
    if any(k in n for k in ["bowl", "ramekin", "donburi", "noodle", "ramen", "pho", "custard", "trifle", "compote"]):
        return "Bowls"

    # Plates and platters
    if any(k in n for k in ["plate", "platter", "tray", "sushi plate", "square plate", "oval platter", "rectangular platter"]):
        return "Plates and platters"

    # Drinkware and bar
    if any(k in n for k in ["stein", "goblet", "tumbler", "highball", "lowball", "martini", "coupe", "shot", "wine"]):
        return "Drinkware and bar"

    # Bakeware and ovensafe
    if any(k in n for k in ["pie", "tart", "bread pan", "loaf", "bundt", "baker", "baking", "casserole", "lasagna", "gratin", "soufflé", "tagine", "dutch oven", "roaster", "pizza stone", "cloche"]):
        return "Bakeware and ovensafe"

    # Serveware and table
    if any(k in n for k in ["serving", "chip and dip", "chip", "dip", "relish", "divided dish", "butter dish", "salt pig", "salt cellar", "spice jar", "utensil crock", "ladle"]):
        return "Serveware and table"

    # Jars and canisters
    if any(k in n for k in ["jar", "canister", "storage", "cookie jar", "urn"]):
        return "Jars and canisters"

    # Teaware and coffee
    if any(k in n for k in ["teapot", "tea", "pour-over", "french press", "coffee server", "creamer", "sugar"]):
        return "Teaware and coffee"

    # Pitchers and ewers
    if any(k in n for k in ["pitcher", "ewer", "cruet"]):
        return "Pitchers and ewers"

    # Cookware and kitchen
    if any(k in n for k in ["colander", "mortar", "pestle", "strainer", "soup tureen", "sauce pot", "pan", "tagine", "tandoor", "kitchen utensil holder", "oil burner"]):
        return "Cookware and kitchen"

    # Lighting and decor
    if any(k in n for k in ["candle", "candlestick", "lantern", "luminary", "lamp base", "clock", "mask", "votive"]):
        return "Lighting and decor"

    # Planters and garden
    if any(k in n for k in ["planter", "garden", "bird", "wind chime", "wind bell", "stepping stone", "fountain", "birdbath", "bird bath"]):
        return "Planters and garden"

    # Tiles and fixtures
    if any(k in n for k in ["tile", "trivet", "switch plate"]):
        return "Tiles and fixtures"

    # Sculpture and art
    if any(k in n for k in ["sculpture", "bust", "relief", "totem", "column", "capital", "columbarium"]):
        return "Sculpture and art"

    return "Specialty and other"

def sort_by_category_then_form(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Category" not in df.columns:
        df["Category"] = df["Form"].apply(infer_category)
    order_map = {cat: i for i, cat in enumerate(CATEGORY_ORDER)}
    df["__cat_rank"] = df["Category"].map(order_map).fillna(len(CATEGORY_ORDER)).astype(int)
    df = df.sort_values(["__cat_rank", "Form"], kind="stable").drop(columns="__cat_rank")
    return df


# Call init early in your script (after you define ss = st.session_state)
init_form_presets_in_state()


# ------------ Session defaults ------------
if "shrink_rate_pct" not in ss:
    ss.shrink_rate_pct = 12.0   # typical stoneware range 10 to 15
if "shrink_units" not in ss:
    ss.shrink_units = "in"

if "inputs" not in ss:
    ss.inputs = dict(
        units_made=1,
        clay_price_per_bag=50.0,
        clay_bag_weight_lb=25.0,
        clay_weight_per_piece_lb=1.0,
        clay_yield=0.9,
        packaging_per_piece=0.0,
        kwh_rate=0.24,  # Al's actual rate
        kwh_bisque=30.0,  # Keep electric defaults for those who use electric
        kwh_glaze=35.0, 
        kwh_third=0.0, 
        pieces_per_electric_firing=40,
        labor_rate=15.0, 
        hours_per_piece=0.25,
        overhead_per_month=500.0, 
        pieces_per_month=200,
        use_2x2x2=False, 
        wholesale_margin_pct=50, 
        retail_multiplier=2.0,
        # Al's propane data
        fuel_gas="Propane",  # Default to propane since that's what Al uses
        lp_price_per_gal=3.50, 
        lp_gal_bisque=4.7,  # Al's 1 tank = ~4.7 gallons
        lp_gal_glaze=9.4,   # Al's 2 tanks = ~9.4 gallons
        pieces_per_gas_firing=40,  # We can adjust this if Al tells us his typical load
        ng_price_per_therm=1.20, 
        ng_therms_bisque=0.0, 
        ng_therms_glaze=0.0,
        # wood firing defaults (keeping your originals)
        wood_price_per_cord=300.0, 
        wood_price_per_facecord=120.0,
        wood_cords_bisque=0.0, 
        wood_cords_glaze=0.0, 
        wood_cords_third=0.0,
        wood_facecords_bisque=0.0, 
        wood_facecords_glaze=0.0, 
        wood_facecords_third=0.0,
        pieces_per_wood_firing=40,
    )

if "catalog_df" not in ss:
    ss.catalog_df = pd.DataFrame([
        {"Material": "Custer Feldspar", "Cost_per_lb": 0.00},
        {"Material": "Silica 325m",     "Cost_per_lb": 0.00},
        {"Material": "EPK Kaolin",      "Cost_per_lb": 0.00},
        {"Material": "Frit 3134",       "Cost_per_lb": 0.00},
    ])

if "recipe_df" not in ss:
    ss.recipe_df = pd.DataFrame([
        {"Material":"Custer Feldspar","Percent":0.0},
        {"Material":"Silica 325m","Percent":0.0},
        {"Material":"EPK Kaolin","Percent":0.0},
        {"Material":"Frit 3134","Percent":0.0},
    ])

if "recipe_grams_per_piece" not in ss:
    ss.recipe_grams_per_piece = 8.0

if "glaze_piece_df" not in ss:
    ss.glaze_piece_df = pd.DataFrame([
        {"Material":"Frit 3134","Cost_per_lb":0.00,"Grams_per_piece":0.0},
    ])

# other materials default
if "other_mat_df" not in ss:
    ss.other_mat_df = pd.DataFrame([
        {"Item":"","Unit":"","Cost_per_unit":0.0,"Quantity_for_project":0.0},
    ])

# Initialize unified form system (replaces old separate form databases)
init_unified_forms()
    
# ------------ Glaze helpers ------------
def glaze_cost_from_piece_table(df):
    gdf = ensure_cols(df, {"Material": "", "Cost_per_lb": 0.0, "Grams_per_piece": 0.0}).copy()
    gdf["Cost_per_g"] = gdf["Cost_per_lb"] / 453.592
    gdf["Cost_per_piece"] = gdf["Cost_per_g"] * gdf["Grams_per_piece"]
    return float(gdf["Cost_per_piece"].sum()), gdf

def percent_recipe_table(catalog_df, recipe_df, batch_g):
    price_map = {
        str(r["Material"]).strip().lower(): float(r["Cost_per_lb"]) / 453.592
        for _, r in ensure_cols(catalog_df, {"Material": "", "Cost_per_lb": 0.0}).iterrows()
    }
    rdf = ensure_cols(recipe_df, {"Material": "", "Percent": 0.0}).copy()
    tot = float(rdf["Percent"].sum()) or 100.0
    rows = []
    for _, r in rdf.iterrows():
        name = str(r["Material"]).strip()
        pct = float(r["Percent"])
        grams = batch_g * pct / tot
        cost = grams * price_map.get(name.lower(), 0.0)
        rows.append({
            "Material": name, "Percent": pct,
            "Grams": round(grams, 2),
            "Ounces": round(grams / 28.3495, 2),
            "Pounds": round(grams / 453.592, 3),
            "Cost": cost
        })
    out = pd.DataFrame(rows)
    batch_total = float(out["Cost"].sum()) if not out.empty else 0.0
    cost_per_g = batch_total / batch_g if batch_g else 0.0
    cost_per_oz = cost_per_g * 28.3495
    cost_per_lb = cost_per_g * 453.592
    return out, batch_total, cost_per_g, cost_per_oz, cost_per_lb

def glaze_per_piece_from_recipe(catalog_df, recipe_df, grams_per_piece):
    price_map = {
        str(r["Material"]).strip().lower(): float(r["Cost_per_lb"]) / 453.592
        for _, r in ensure_cols(catalog_df, {"Material": "", "Cost_per_lb": 0.0}).iterrows()
    }
    rdf = ensure_cols(recipe_df, {"Material": "", "Percent": 0.0}).copy()
    tot = float(rdf["Percent"].sum()) or 100.0
    rows = []
    total_cost_pp = 0.0
    for _, r in rdf.iterrows():
        name = str(r["Material"]).strip()
        pct = float(r["Percent"])
        g = grams_per_piece * pct / tot
        cost_pp = g * price_map.get(name.lower(), 0.0)
        total_cost_pp += cost_pp
        rows.append({
            "Material": name,
            "Percent": round(pct, 2),
            "Grams_per_piece": round(g, 3),
            "Ounces_per_piece": round(g / 28.3495, 3),
            "Pounds_per_piece": round(g / 453.592, 4),
            "Cost_per_piece": cost_pp
        })
    df = pd.DataFrame(rows)
    return df, float(total_cost_pp)

# ------------ Energy and totals ------------
def calc_energy(ip):
    e_cost = (ip.get("kwh_bisque", 0.0) + ip.get("kwh_glaze", 0.0) + ip.get("kwh_third", 0.0)) * ip.get("kwh_rate", 0.0)
    e_pp = e_cost / max(1, int(ip.get("pieces_per_electric_firing", 40)))

    fuel = str(ip.get("fuel_gas", "None")).strip()
    fuel_pp = 0.0

    if fuel == "Propane":
        gas_cost = ip.get("lp_price_per_gal", 0.0) * (ip.get("lp_gal_bisque", 0.0) + ip.get("lp_gal_glaze", 0.0))
        fuel_pp = gas_cost / max(1, int(ip.get("pieces_per_gas_firing", 40)))

    elif fuel == "Natural Gas":
        gas_cost = ip.get("ng_price_per_therm", 0.0) * (ip.get("ng_therms_bisque", 0.0) + ip.get("ng_therms_glaze", 0.0))
        fuel_pp = gas_cost / max(1, int(ip.get("pieces_per_gas_firing", 40)))

    elif fuel == "Wood":
        wood_cost = (
            ip.get("wood_price_per_cord", 0.0) * (ip.get("wood_cords_bisque", 0.0) + ip.get("wood_cords_glaze", 0.0) + ip.get("wood_cords_third", 0.0))
            + ip.get("wood_price_per_facecord", 0.0) * (ip.get("wood_facecords_bisque", 0.0) + ip.get("wood_facecords_glaze", 0.0) + ip.get("wood_facecords_third", 0.0))
        )
        fuel_pp = wood_cost / max(1, int(ip.get("pieces_per_wood_firing", 40)))

    return e_pp + fuel_pp

def calc_totals(ip, glaze_per_piece_cost, other_pp: float = 0.0):
    clay_cost_per_lb = ip["clay_price_per_bag"] / ip["clay_bag_weight_lb"] if ip["clay_bag_weight_lb"] else 0.0
    clay_pp = (ip["clay_weight_per_piece_lb"] / max(ip["clay_yield"], 1e-9)) * clay_cost_per_lb
    energy_pp = calc_energy(ip)
    labor_pp = ip["labor_rate"] * ip["hours_per_piece"]
    overhead_pp = ip["overhead_per_month"] / max(1, int(ip["pieces_per_month"]))

    material_pp = clay_pp + glaze_per_piece_cost + ip["packaging_per_piece"] + other_pp
    total_pp = material_pp + energy_pp + labor_pp + overhead_pp

    if ip["use_2x2x2"]:
        wholesale = total_pp * 2.0
        retail = wholesale * 2.0
        distributor = retail * 2.0
    else:
        margin = ip["wholesale_margin_pct"] / 100.0
        wholesale = total_pp / max(1e-9, 1.0 - margin) if margin < 1 else float("inf")
        retail = wholesale * ip["retail_multiplier"]
        distributor = None

    return dict(
        clay_pp=clay_pp, glaze_pp=glaze_per_piece_cost, pack_pp=ip["packaging_per_piece"],
        other_pp=other_pp, energy_pp=energy_pp, labor_pp=labor_pp, oh_pp=overhead_pp,
        total_pp=total_pp, wholesale=wholesale, retail=retail, distributor=distributor
    )
st.title("Pottery Cost Analysis App")

# Initialize unified form system (replaces old separate form databases)
try:
    init_unified_forms()
    st.write(f"✅ Unified forms initialized: {len(ss.unified_forms)} forms loaded")
except Exception as e:
    st.error(f"❌ Failed to initialize unified forms: {e}")
    # Fallback - create empty unified forms
    if "unified_forms" not in ss:
        ss.unified_forms = pd.DataFrame(columns=list(UNIFIED_FORM_SCHEMA.keys()))

tab_titles = [
    "Quick Start",      # 0
    "Per Unit",         # 1
    "Glaze Recipe",     # 2
    "Energy",           # 3
    "Production Planning",  # 4
    "Kiln Load Planner",    # 5 
    "Labor and Overhead",   # 6
    "Pricing",              # 7
    "Save and Load",        # 8
    "Shipping & Tariffs",   # 9
    "Report",               # 10
    "About",                # 11
]
tabs = st.tabs(tab_titles)

# ------------- Quick Start Tab (POLISHED) -------------
with tabs[0]:
    st.header("🎯 Quick Start")
    st.markdown("**Get pricing for your pottery in under 2 minutes**")
    
    # Apply defaults
    apply_quick_defaults()
    
    # Add a session state variable to control tab switching
    if "target_tab" not in ss:
        ss.target_tab = None
    
    # Create two columns for clean layout
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        st.subheader("1. What are you making?")
        
        # Form selector using unified form database
        init_unified_forms()  # Ensure unified forms are loaded
        unified_forms = ss.unified_forms.copy()
        
        # Get popular forms (first 20 or so)
        popular_forms = unified_forms.head(20)["Form"].tolist() if not unified_forms.empty else []
        
        selected_form = st.selectbox(
            "Choose a form:",
            ["Custom"] + popular_forms,
            index=1 if popular_forms else 0,
            help="Can't find your form? Choose 'Custom' or switch to the 'Per Unit' tab for full control."
        )
        
        # Get preset values if form is selected
        clay_weight = 1.0
        glaze_amount = 80
        confidence_factors = {"form": False}
        
        if selected_form != "Custom" and not unified_forms.empty:
            preset_row = unified_forms.loc[unified_forms["Form"] == selected_form].iloc[0]
            preset_clay_lb = float(preset_row.get("Clay_lb_wet", 1.0))
            preset_glaze_g = float(preset_row.get("Default_glaze_g", 80))
            
            # Show preset info
            c1, c2 = st.columns(2)
            c1.metric("Clay weight", f"{preset_clay_lb:.2f} lb")
            c2.metric("Glaze amount", f"{preset_glaze_g:.0f} g")
            
            # Auto-apply to session state
            ss.inputs["clay_weight_per_piece_lb"] = preset_clay_lb
            ss.recipe_grams_per_piece = preset_glaze_g
            clay_weight = preset_clay_lb
            glaze_amount = preset_glaze_g
            confidence_factors["form"] = True
        else:
            # Manual entry for custom with validation
            clay_weight = st.number_input(
                "Clay weight per piece (lb):",
                min_value=0.1,
                max_value=20.0,  # Reasonable upper limit
                value=float(ss.inputs.get("clay_weight_per_piece_lb", 1.0)),
                step=0.1,
                help="💡 Typical range: 0.5-5 lbs for most functional pottery"
            )
            ss.inputs["clay_weight_per_piece_lb"] = clay_weight
            confidence_factors["form"] = clay_weight > 0
        
        st.subheader("2. Basic costs")
        
        col_a, col_b = st.columns(2)
        with col_a:
            # Clay cost - simplified with validation
            clay_method = st.radio("Clay cost:", ["Per bag", "Per pound"], horizontal=True)
            
            if clay_method == "Per bag":
                bag_cost = st.number_input(
                    "Cost per bag:", 
                    min_value=0.0, 
                    max_value=200.0,
                    value=50.0, 
                    step=1.0,
                    help="💡 Typical range: $25-80 per bag for stoneware"
                )
                bag_weight = st.number_input(
                    "Bag weight (lb):", 
                    min_value=1.0, 
                    max_value=100.0,
                    value=25.0, 
                    step=1.0,
                    help="💡 Most common: 25 or 50 lb bags"
                )
                
                # Validation
                if bag_cost <= 0 or bag_weight <= 0:
                    st.warning("⚠️ Please enter positive values for bag cost and weight")
                    confidence_factors["clay"] = False
                else:
                    ss.inputs["clay_price_per_bag"] = bag_cost
                    ss.inputs["clay_bag_weight_lb"] = bag_weight
                    clay_per_lb = bag_cost / bag_weight
                    st.caption(f"= {money(clay_per_lb)} per pound")
                    confidence_factors["clay"] = True
            else:
                clay_per_lb = st.number_input(
                    "Cost per pound:", 
                    min_value=0.0, 
                    max_value=10.0,
                    value=2.00, 
                    step=0.05,
                    help="💡 Typical range: $1-4 per pound"
                )
                if clay_per_lb <= 0:
                    st.warning("⚠️ Please enter a positive clay cost")
                    confidence_factors["clay"] = False
                else:
                    ss.inputs["clay_price_per_bag"] = clay_per_lb * 25  # Assume 25lb bags
                    ss.inputs["clay_bag_weight_lb"] = 25.0
                    confidence_factors["clay"] = True
        
        with col_b:
            # Time and labor with validation
            hours_input = st.number_input(
                "Total time per piece (hours):",
                min_value=0.1,
                max_value=20.0,
                value=float(ss.inputs.get("hours_per_piece", 0.5)),
                step=0.25,
                help="💡 Typical range: 0.5-3 hours total (throwing + trimming + glazing + loading)"
            )
            
            labor_input = st.number_input(
                "Your time is worth ($/hour):",
                min_value=1.0,
                max_value=200.0,
                value=float(ss.inputs.get("labor_rate", 15.0)),
                step=1.0,
                help="💡 Most potters: $12-30/hour • Experienced: $25-50/hour"
            )
            
            # Validation and application
            if hours_input <= 0:
                st.warning("⚠️ Time must be greater than 0")
                confidence_factors["labor"] = False
            else:
                ss.inputs["hours_per_piece"] = hours_input
                confidence_factors["labor"] = True
                
            if labor_input <= 0:
                st.warning("⚠️ Labor rate must be greater than 0")
            else:
                ss.inputs["labor_rate"] = labor_input
        
        # Advanced toggle with validation
        with st.expander("⚙️ Adjust other costs (optional)"):
            st.caption("These have sensible defaults, but you can customize:")
            
            adj_a, adj_b = st.columns(2)
            with adj_a:
                elec_rate = st.number_input(
                    "Electricity rate ($/kWh):",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(ss.inputs.get("kwh_rate", 0.15)),
                    step=0.01,
                    help="💡 U.S. average: $0.12-0.20/kWh"
                )
                ss.inputs["kwh_rate"] = max(0.0, elec_rate)
                
                pack_cost = st.number_input(
                    "Packaging per piece ($):",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(ss.inputs.get("packaging_per_piece", 0.5)),
                    step=0.1,
                    help="💡 Boxes, bubble wrap, labels: $0.25-2.00"
                )
                ss.inputs["packaging_per_piece"] = max(0.0, pack_cost)
            
            with adj_b:
                overhead = st.number_input(
                    "Monthly overhead ($):",
                    min_value=0.0,
                    max_value=10000.0,
                    value=float(ss.inputs.get("overhead_per_month", 500.0)),
                    step=50.0,
                    help="💡 Studio rent, insurance, utilities: $200-2000/month"
                )
                ss.inputs["overhead_per_month"] = max(0.0, overhead)
                
                pieces_month = st.number_input(
                    "Pieces you make per month:",
                    min_value=1,
                    max_value=2000,
                    value=int(ss.inputs.get("pieces_per_month", 200)),
                    step=10,
                    help="💡 Hobbyist: 20-50 • Part-time: 50-150 • Full-time: 200+"
                )
                ss.inputs["pieces_per_month"] = max(1, pieces_month)
    
    with right_col:
        st.subheader("💰 Your Pricing")
        
        # Calculate confidence score
        confidence_score = sum([
            confidence_factors.get("form", False),
            confidence_factors.get("clay", False), 
            confidence_factors.get("labor", False),
        ]) / 3 * 100
        
        # Confidence indicator
        if confidence_score >= 80:
            confidence_color = "🟢"
            confidence_text = "High confidence"
        elif confidence_score >= 60:
            confidence_color = "🟡" 
            confidence_text = "Medium confidence"
        else:
            confidence_color = "🔴"
            confidence_text = "Low confidence - check inputs"
            
        st.metric(
            label="Estimate Confidence",
            value=f"{confidence_color} {confidence_text}",
            help="Based on completeness of your inputs. Green = reliable estimate, Red = may need adjustment"
        )
        
        # Calculate costs using existing functions
        grams_pp = float(ss.get("recipe_grams_per_piece", glaze_amount))
        _, glaze_pp_cost = glaze_per_piece_from_recipe(ss.catalog_df, ss.recipe_df, grams_pp)
        
        # Use a simple glaze cost if recipe is empty
        if glaze_pp_cost <= 0:
            glaze_pp_cost = grams_pp * 0.01  # Rough estimate: 1 cent per gram
        
        other_pp, _, _ = other_materials_pp(ss.other_mat_df, int(ss.inputs.get("units_made", 1)))
        
        # Only calculate if we have valid inputs
        if confidence_factors.get("clay", False) and confidence_factors.get("labor", False):
            totals = calc_totals(ss.inputs, glaze_pp_cost, other_pp)
            
            # Display results prominently
            st.markdown("---")
            
            # Cost breakdown
            with st.container():
                st.markdown("**Cost breakdown per piece:**")
                cost_col1, cost_col2 = st.columns(2)
                
                with cost_col1:
                    st.write(f"• Clay: {money(totals['clay_pp'])}")
                    st.write(f"• Glaze: {money(totals['glaze_pp'])}")
                    st.write(f"• Labor: {money(totals['labor_pp'])}")
                
                with cost_col2:
                    st.write(f"• Energy: {money(totals['energy_pp'])}")
                    st.write(f"• Overhead: {money(totals['oh_pp'])}")
                    st.write(f"• Other: {money(totals['pack_pp'] + totals['other_pp'])}")
            
            st.markdown("---")
            
            # Final prices - big and bold
            st.metric(
                label="🏪 WHOLESALE PRICE",
                value=money(totals["wholesale"]),
                help="What to charge stores and galleries (50% margin built in)"
            )
            
            st.metric(
                label="🛒 RETAIL PRICE", 
                value=money(totals["retail"]),
                help="What to charge individual customers (2x wholesale)"
            )
            
            st.metric(
                label="📊 Your Cost",
                value=money(totals["total_pp"]),
                help="Never sell below this! This covers all your expenses."
            )
            
            # Profit margins
            st.caption("Wholesale: 2x cost • Retail: 2x wholesale")
            
        else:
            st.info("💡 Complete the required fields above to see your pricing")
    
    # Call to action - FUNCTIONAL BUTTONS
    st.markdown("---")
    st.markdown("### 🚀 Want more control?")
    
    cta_col1, cta_col2, cta_col3 = st.columns(3)
    
    with cta_col1:
        if st.button("🧪 Customize Glaze Recipe", use_container_width=True):
            st.info("✅ Great! Now click the **Glaze Recipe** tab at the top of the page to create custom recipes and track material costs.")

    with cta_col2:
        if st.button("⚡ Adjust Energy Costs", use_container_width=True):
            st.info("✅ Perfect! Now click the **Energy** tab at the top to set up gas kilns, wood firing, and detailed electricity costs.")
        
    with cta_col3:
        if st.button("📋 Full Details", use_container_width=True):
            st.info("✅ Excellent! Now click the **Per Unit** tab at the top for complete control over clay costs, shrink rates, and all cost factors.")

    
    # Helpful tips at bottom
    with st.expander("💡 Pricing Tips", expanded=False):
        st.markdown("""
        **Quick guidelines:**
        - **Never sell below cost** - that's the red "Your Cost" number above
        - **Wholesale = 2x cost** - gives you 50% margin to cover unexpected expenses  
        - **Retail = 2.2x wholesale** - standard markup that galleries expect
        - **Track your actual time** - most potters underestimate by 30-50%
        - **Include ALL costs** - studio rent, insurance, equipment wear, your salary
        - **Price confidently** - handmade pottery has real value
        
        **Regional benchmarks:**
        - Coffee mugs: $18-35 retail
        - Cereal bowls: $22-40 retail  
        - Dinner plates: $28-50 retail
        """)


# ------------- Per unit -------------
with tabs[1]:
    ip = ss.inputs
    left, right = st.columns(2)

    # =========================
    # Left column
    # =========================
    with left:
        #  ---------- Form preset picker + manager ----------
        
        st.subheader("Form preset")

        # Use unified forms database
        unified_forms = ss.unified_forms.copy()

        # Dropdown of forms
        forms = list(unified_forms["Form"]) if not unified_forms.empty else []
        choice = st.selectbox("Choose a form", ["None"] + forms, index=0, key="form_choice")

        # Preview & apply
        if choice != "None" and not unified_forms.empty:
            row = unified_forms.loc[unified_forms["Form"] == choice].iloc[0]
            preset_clay_lb = float(row.get("Clay_lb_wet", 0.0))
            preset_glaze_g = float(row.get("Default_glaze_g", 0.0))
            preset_throwing_min = float(row.get("Throwing_min", 0.0))
            preset_glazing_min = float(row.get("Glazing_min", 0.0))
            note = str(row.get("Notes", "")).strip()

            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            c1.metric("Clay", f"{preset_clay_lb:.2f} lb")
            c2.metric("Glaze", f"{preset_glaze_g:.0f} g")
            if preset_throwing_min > 0:
                c3.metric("Throwing", f"{preset_throwing_min:.1f} min")
            if preset_glazing_min > 0:
                c4.metric("Glazing", f"{preset_glazing_min:.1f} min")
            if note:
                st.caption(f"💡 {note}")

            if st.button("Use this preset", key="apply_preset_btn"):
                ip["clay_weight_per_piece_lb"] = preset_clay_lb
                ss.recipe_grams_per_piece = preset_glaze_g
                if preset_throwing_min > 0:
                    # Also update labor hours if timing data exists
                    total_time_hours = (preset_throwing_min + preset_glazing_min) / 60.0
                    if total_time_hours > 0:
                        ip["hours_per_piece"] = total_time_hours
                st.success("Preset applied to clay weight, glaze amount, and labor time.")

        # Manage presets
        with st.expander("Manage unified forms (CSV import/export, inline edit)"):
            st.caption("Unified form database includes clay weight, glaze amount, timing data, and kiln info")

            # Export current unified forms
            _csv_bytes = ss.unified_forms.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download unified forms CSV",
                _csv_bytes,
                file_name="unified_forms.csv",
                mime="text/csv",
                key="dl_unified_csv",
            )

            # Upload new forms
            u1, u2 = st.columns([1, 1])
            with u1:
                upload_mode = st.radio(
                    "When uploading",
                    ["Replace", "Append"],
                    horizontal=True,
                    key="unified_upload_mode",
                )
            with u2:
                up = st.file_uploader("Upload unified forms CSV", type=["csv"], key="unified_csv_uploader")

            if up is not None:
                try:
                    new_df = pd.read_csv(up)
                    # Ensure all required columns exist
                    new_df = ensure_cols(new_df, UNIFIED_FORM_SCHEMA)
                    
                    # Clean and validate data
                    for col, default_val in UNIFIED_FORM_SCHEMA.items():
                        if isinstance(default_val, str):
                            new_df[col] = new_df[col].astype(str).str.strip()
                        elif isinstance(default_val, float):
                            new_df[col] = pd.to_numeric(new_df[col], errors="coerce").fillna(default_val)
                        elif isinstance(default_val, int):
                            new_df[col] = pd.to_numeric(new_df[col], errors="coerce").fillna(default_val).astype(int)

                    if upload_mode == "Replace":
                        ss.unified_forms = new_df
                    else:
                        base = ss.unified_forms.copy()
                        combo = pd.concat([base, new_df], ignore_index=True)
                        ss.unified_forms = combo.drop_duplicates(subset=["Form"], keep="last").reset_index(drop=True)

                    st.success(f"Loaded {len(new_df)} unified forms.")
                except Exception as e:
                    st.error(f"Could not read CSV. {e}")

            st.caption("Edit rows below (add/delete allowed). All form data in one place!")
            edited = st.data_editor(
                ss.unified_forms,
                column_config={
                    "Form": st.column_config.TextColumn("Form"),
                    "Clay_lb_wet": st.column_config.NumberColumn("Clay (lb)", min_value=0.0, step=0.05),
                    "Default_glaze_g": st.column_config.NumberColumn("Glaze (g)", min_value=0.0, step=1.0),
                    "Throwing_min": st.column_config.NumberColumn("Throwing (min)", min_value=0.0, step=0.1),
                    "Trimming_min": st.column_config.NumberColumn("Trimming (min)", min_value=0.0, step=0.1),
                    "Handling_min": st.column_config.NumberColumn("Handling (min)", min_value=0.0, step=0.1),
                    "Glazing_min": st.column_config.NumberColumn("Glazing (min)", min_value=0.0, step=0.1),
                    "Pieces_per_shelf": st.column_config.NumberColumn("Per shelf", min_value=0, step=1),
                    "Notes": st.column_config.TextColumn("Notes"),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="unified_forms_editor",
            )
            ss.unified_forms = edited.copy()
            

        # ---------- Clay & packaging ----------
       
        st.subheader("Clay and packaging")

        ip["units_made"] = st.number_input(
            "Units in this batch", min_value=1, value=int(ip["units_made"]), step=1
        )
        ip["clay_price_per_bag"] = st.number_input(
            "Clay price per bag", min_value=0.0, value=float(ip["clay_price_per_bag"]), step=0.5
        )
        ip["clay_bag_weight_lb"] = st.number_input(
            "Clay bag weight lb", min_value=0.1, value=float(ip["clay_bag_weight_lb"]), step=0.1
        )
        ip["clay_weight_per_piece_lb"] = st.number_input(
            "Clay weight per piece lb (wet)",
            min_value=0.0,
            value=float(ip["clay_weight_per_piece_lb"]),
            step=0.1,
        )
        ip["clay_yield"] = st.slider(
            "Clay yield after trimming and loss",
            min_value=0.5,
            max_value=1.0,
            value=float(ip.get("clay_yield", 0.9)),
            step=0.01,
            help="Fraction of the starting ball that ends up in the finished piece. 1.00 means no loss; 0.85 means 15% loss.",
        )
        throw_weight = float(ip.get("clay_weight_per_piece_lb", 0.0))
        yield_frac = float(ip.get("clay_yield", 1.0))
        effective_lb = throw_weight / max(yield_frac, 1e-9)
        waste_pct = (1.0 - yield_frac) * 100.0
        st.caption(f"You pay for about {effective_lb:.2f} lb of clay per finished piece given {waste_pct:.0f}% loss.")

        ip["packaging_per_piece"] = st.number_input(
            "Packaging per piece", min_value=0.0, value=float(ip["packaging_per_piece"]), step=0.1
        )
        

        # --- Shrink tools in one dropdown only on this tab ---
        
        with st.expander("Shrink rate helper", expanded=False):
            # compute shrink from a test tile
            st.markdown("**Compute from test tile**")
            c1, c2, c3 = st.columns([1, 1, 1])
            wet_len = c1.number_input(
                "Wet length",
                min_value=0.0,
                value=float(ss.get("sh_wet_len", 10.00)),
                step=0.01,
                key="sh_wet_len",
            )
            fired_len = c2.number_input(
                "Fired length",
                min_value=0.0,
                value=float(ss.get("sh_fired_len", 8.80)),
                step=0.01,
                key="sh_fired_len",
            )
            shrink_from_test = 0.0 if wet_len <= 0 else max(0.0, (wet_len - fired_len) / wet_len * 100.0)
            c3.metric("Shrink from test", f"{shrink_from_test:.2f}%")
            if st.button("Use this shrink percent", key="btn_use_shrink_pct"):
                ss.shrink_rate_pct = float(shrink_from_test)
                st.toast("Shrink percent set", icon="✅")

            # units (WIDGET controls session_state)
            st.markdown("**Units**")
            units = st.radio(
                "Units",
                ["in", "mm", "cm"],
                index=["in", "mm", "cm"].index(ss.get("shrink_units", "in")),
                horizontal=True,
                key="shrink_units",
            )
            u = units

            st.markdown("**Size converter**")
            rate = max(0.0, float(ss.get("shrink_rate_pct", 12.0))) / 100.0
            s1, s2, s3 = st.columns([1, 1, 1])
            wet_size = s1.number_input(
                f"Wet size ({u})",
                min_value=0.0,
                value=float(ss.get("sh_wet_size", 4.00)),
                step=0.001,
                key="sh_wet_size",
            )
            target_fired = s2.number_input(
                f"Target fired size ({u})",
                min_value=0.0,
                value=float(ss.get("sh_target", 3.52)),
                step=0.001,
                key="sh_target",
            )
            fired_from_wet = wet_size * (1.0 - rate)
            s3.metric("Fired from wet", f"{fired_from_wet:.3f} {u}")
            needed_wet = target_fired / max(1e-9, (1.0 - rate))
            st.caption(f"To end at {target_fired:.3f} {u}, throw about {needed_wet:.3f} in wet.")

            st.markdown("**Lid remake helper**")
            st.caption("Measure the fired rim outside diameter on the pot. Choose a small clearance to keep the fit comfortable.")
            l1, l2, l3 = st.columns([1, 1, 1])
            fired_rim_od = l1.number_input(
                f"Fired rim outside diameter ({u})",
                min_value=0.0,
                value=float(ss.get("lid_fired_od", 3.00)),
                step=0.001,
                key="lid_fired_od",
            )
            default_clear = 0.03 if u == "in" else 0.8 if u == "mm" else 0.08
            clearance = l2.number_input(
                f"Extra diameter for clearance ({u})",
                min_value=0.0,
                value=float(ss.get("lid_clearance", default_clear)),
                step=0.001,
                key="lid_clearance",
            )
            wet_gallery_needed = (fired_rim_od + clearance) / max(1e-9, (1.0 - rate))
            l3.metric("Wet gallery inner diameter to throw", f"{wet_gallery_needed:.3f} {u}")

            # Gallery height calculation
            st.caption("Gallery height for proportional lid design")
            h1, h2 = st.columns([1, 1])
            desired_gallery_depth = h1.number_input(
                f"Desired fired gallery depth ({u})",
                min_value=0.0,
                value=float(ss.get("lid_desired_depth", 0.25 if u == "in" else 6.0 if u == "mm" else 0.6)),
                step=0.001,
                key="lid_desired_depth",
                help="How deep you want the lid to sit on the pot"
            )
            wet_gallery_height = desired_gallery_depth / max(1e-9, (1.0 - rate))
            h2.metric("Wet gallery height to throw", f"{wet_gallery_height:.3f} {u}")

            st.caption("Reverse check if you already threw a lid")
            rev1, rev2 = st.columns([1, 1])
            lid_wet_id = rev1.number_input(
                f"Wet gallery inner diameter you threw ({u})",
                min_value=0.0,
                value=float(ss.get("lid_wet_id", wet_gallery_needed)),
                step=0.001,
                key="lid_wet_id",
            )
            lid_wet_height = rev2.number_input(
                f"Wet gallery height you threw ({u})",
                min_value=0.0,
                value=float(ss.get("lid_wet_height", wet_gallery_height)),
                step=0.001,
                key="lid_wet_height",
            )
            expected_fired_id = lid_wet_id * (1.0 - rate)
            expected_fired_height = lid_wet_height * (1.0 - rate)
            st.write(f"Expected fired gallery inner diameter: **{expected_fired_id:.3f} {u}**")
            st.write(f"Expected fired gallery depth: **{expected_fired_height:.3f} {u}**")
           

        # ---------- Glaze source ----------
        
        st.subheader("Glaze source")
        glaze_source = st.radio(
            "Glaze cost comes from",
            ["Recipe tab", "Manual table"],
            index=0,
            horizontal=True,
            key="glaze_source_choice",
        )

        if glaze_source == "Manual table":
            st.caption("Edit names, cost per lb, and grams per piece.")
            ss.glaze_piece_df = st.data_editor(
                ensure_cols(
                    ss.glaze_piece_df, {"Material": "", "Cost_per_lb": 0.0, "Grams_per_piece": 0.0}
                ),
                column_config={
                    "Material": st.column_config.TextColumn("Material", help="Raw material name"),
                    "Cost_per_lb": st.column_config.NumberColumn("Cost per lb", min_value=0.0, step=0.01),
                    "Grams_per_piece": st.column_config.NumberColumn("Grams per piece", min_value=0.0, step=0.1),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="glaze_piece_editor_front",
            )
            glaze_pp_cost, source_df = glaze_cost_from_piece_table(ss.glaze_piece_df)
        else:
            grams_pp = float(ss.get("recipe_grams_per_piece", 8.0))
            source_df, glaze_pp_cost = glaze_per_piece_from_recipe(ss.catalog_df, ss.recipe_df, grams_pp)

        st.subheader("Glaze per piece and cost")
        _show_df = source_df.copy()
        if "Cost_per_piece" in _show_df.columns:
            _show_df["Cost_per_piece"] = _show_df["Cost_per_piece"].map(money)
        st.dataframe(_show_df, use_container_width=True)
        

    # =========================
    # Right column
    # =========================
    with right:
        # Other project materials (one-time items per project)
        
        st.subheader("Other project materials")
        st.caption("Add one-time items for this batch. The cost is divided by the number of pieces in the batch.")

        pieces = max(1, int(ip["units_made"]))
        base = ensure_cols(
            ss.other_mat_df,
            {"Item": "", "Unit": "", "Cost_per_unit": 0.0, "Quantity_for_project": 0.0},
        ).copy()
        base["Cost_per_unit"] = pd.to_numeric(base["Cost_per_unit"], errors="coerce").fillna(0.0)
        base["Quantity_for_project"] = pd.to_numeric(base["Quantity_for_project"], errors="coerce").fillna(0.0)
        base["Line_total"] = base["Cost_per_unit"] * base["Quantity_for_project"]
        base["Cost_per_piece"] = base["Line_total"] / pieces

        ss.other_mat_df = st.data_editor(
            base,
            column_config={
                "Item": st.column_config.TextColumn("Item"),
                "Unit": st.column_config.TextColumn("Unit"),
                "Cost_per_unit": st.column_config.NumberColumn("Cost per unit", min_value=0.0, step=0.01),
                "Quantity_for_project": st.column_config.NumberColumn("Quantity for project", min_value=0.0, step=0.1),
                "Line_total": st.column_config.NumberColumn("Line total", disabled=True),
                "Cost_per_piece": st.column_config.NumberColumn("Cost per piece", disabled=True),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="other_materials_editor_main",
        )

        project_total = float(ss.other_mat_df["Line_total"].sum()) if "Line_total" in ss.other_mat_df else 0.0
        other_pp = project_total / pieces
        st.caption(f"Project total {money(project_total)} • Adds {money(other_pp)} per piece")
        

        # Totals
        
        st.subheader("Per piece totals")
        totals = calc_totals(ip, glaze_pp_cost, other_pp)

        c = st.columns(3)
        c[0].metric("Energy", money(totals["energy_pp"]))
        c[1].metric("Labor", money(totals["labor_pp"]))
        c[2].metric("Overhead", money(totals["oh_pp"]))
        st.metric("Other project materials", money(totals["other_pp"]))
        st.metric("Total cost per piece", money(totals["total_pp"]))
        




# ------------ Glaze recipe ------------
with tabs[2]:
    if ss.get("guidance_type") == "glaze":
        st.success("✅ **Perfect!** Here you can create custom glaze recipes and track material costs.")
        st.markdown("💡 **Quick tip:** Your Quick Start used a simple estimate. Build your recipe below for precise glaze costing.")
        st.markdown("---")
    
    st.subheader("Catalog (choose cost unit)")
    if "catalog_unit" not in ss:
        ss.catalog_unit = "lb"
    ss.catalog_unit = st.radio("Catalog cost unit", ["lb", "kg"], horizontal=True, index=0 if ss.catalog_unit=="lb" else 1)

    # SEARCHABLE MATERIAL ENTRY
    with st.expander("➕ Add new materials to catalog", expanded=False):
        st.caption("Select from 50+ common materials or enter custom names")
        
        # Get list of materials already in catalog
        current_materials = list(ss.catalog_df["Material"].str.strip().str.lower()) if not ss.catalog_df.empty else []
        common_materials = get_common_materials_list()
        
        # Filter out materials already in catalog
        available_materials = [m for m in common_materials if m.lower() not in current_materials]
        
        add_col1, add_col2, add_col3 = st.columns([2, 1, 1])
        
        with add_col1:
            # Searchable dropdown with custom option
            material_options = ["-- Select Material --"] + available_materials + ["⌨️ Enter Custom Name"]
            selected_material = st.selectbox(
                "Choose material:", 
                material_options,
                key="material_selector"
            )
            
            # Custom name input if needed
            if selected_material == "⌨️ Enter Custom Name":
                custom_material = st.text_input("Enter custom material name:", key="custom_material_name")
                final_material_name = custom_material.strip()
            elif selected_material != "-- Select Material --":
                final_material_name = selected_material
            else:
                final_material_name = ""
        
        with add_col2:
            if ss.catalog_unit == "lb":
                new_cost = st.number_input("Cost per lb:", min_value=0.0, step=0.05, key="new_material_cost")
            else:
                new_cost = st.number_input("Cost per kg:", min_value=0.0, step=0.05, key="new_material_cost")
        
        with add_col3:
            if st.button("Add Material") and final_material_name and new_cost >= 0:
                # Create new row
                if ss.catalog_unit == "lb":
                    new_row = {
                        "Material": final_material_name,
                        "Cost_per_lb": new_cost,
                        "Cost_per_kg": new_cost * 2.20462
                    }
                else:
                    new_row = {
                        "Material": final_material_name,
                        "Cost_per_lb": new_cost / 2.20462,
                        "Cost_per_kg": new_cost
                    }
                
                # Add to catalog
                new_df = pd.concat([ss.catalog_df, pd.DataFrame([new_row])], ignore_index=True)
                ss.catalog_df = new_df.drop_duplicates(subset=["Material"], keep="last").reset_index(drop=True)
                
                st.success(f"Added {final_material_name}!")
                st.rerun()

    # REGULAR CATALOG EDITOR
    if ss.catalog_unit == "lb":
        edited = st.data_editor(
            ensure_cols(ss.catalog_df, {"Material": "", "Cost_per_lb": 0.0}),
            column_config={
                "Material": st.column_config.TextColumn("Material"),
                "Cost_per_lb": st.column_config.NumberColumn("Cost per lb", min_value=0.0, step=0.01),
            },
            num_rows="dynamic", use_container_width=True, key="catalog_editor_lb"
        )
        edited = ensure_cols(edited, {"Material": "", "Cost_per_lb": 0.0})
        edited["Cost_per_kg"] = edited["Cost_per_lb"] * 2.20462
        ss.catalog_df = edited[["Material", "Cost_per_lb", "Cost_per_kg"]]
    else:
        edited = st.data_editor(
            ensure_cols(ss.catalog_df, {"Material": "", "Cost_per_kg": 0.0}),
            column_config={
                "Material": st.column_config.TextColumn("Material"),
                "Cost_per_kg": st.column_config.NumberColumn("Cost per kg", min_value=0.0, step=0.01),
            },
            num_rows="dynamic", use_container_width=True, key="catalog_editor_kg"
        )
        edited = ensure_cols(edited, {"Material": "", "Cost_per_kg": 0.0})
        edited["Cost_per_lb"] = edited["Cost_per_kg"] / 2.20462
        ss.catalog_df = edited[["Material", "Cost_per_lb", "Cost_per_kg"]]

    # RECIPE SECTION WITH SEARCHABLE MATERIALS
    st.subheader("Recipe in percent")

    with st.expander("➕ Add materials to recipe", expanded=False):
        recipe_col1, recipe_col2, recipe_col3 = st.columns([2, 1, 1])
        
        # Get materials from catalog for recipe dropdown
        catalog_materials = list(ss.catalog_df["Material"].str.strip()) if not ss.catalog_df.empty else []
        recipe_materials = list(ss.recipe_df["Material"].str.strip()) if not ss.recipe_df.empty else []
        
        # Available materials not yet in recipe
        available_for_recipe = [m for m in catalog_materials if m not in recipe_materials]
        
        with recipe_col1:
            recipe_options = ["-- Select from Catalog --"] + available_for_recipe + ["⌨️ Enter New Material"]
            selected_recipe_material = st.selectbox("Add material to recipe:", recipe_options, key="recipe_material_selector")
            
            if selected_recipe_material == "⌨️ Enter New Material":
                custom_recipe_material = st.text_input("Material name:", key="custom_recipe_material")
                final_recipe_material = custom_recipe_material.strip()
            elif selected_recipe_material != "-- Select from Catalog --":
                final_recipe_material = selected_recipe_material
            else:
                final_recipe_material = ""
        
        with recipe_col2:
            recipe_percent = st.number_input("Percent:", min_value=0.0, step=0.1, key="recipe_percent_input")
        
        with recipe_col3:
            if st.button("Add to Recipe", key="add_recipe_btn") and final_recipe_material and recipe_percent >= 0:
                # Create new row
                new_recipe_row = {"Material": final_recipe_material, "Percent": recipe_percent}
                
                # Add to recipe dataframe
                if ss.recipe_df.empty:
                    ss.recipe_df = pd.DataFrame([new_recipe_row])
                else:
                    # Remove if already exists, then add (to avoid duplicates)
                    ss.recipe_df = ss.recipe_df[ss.recipe_df["Material"] != final_recipe_material]
                    new_recipe_df = pd.concat([ss.recipe_df, pd.DataFrame([new_recipe_row])], ignore_index=True)
                    ss.recipe_df = new_recipe_df
                
                st.success(f"Added {final_recipe_material} at {recipe_percent}%!")
                st.rerun()

    # REGULAR RECIPE EDITOR (with dynamic key for refresh)
    recipe_editor_key = f"recipe_editor_{len(ss.recipe_df)}"  # Key changes when length changes

    ss.recipe_df = st.data_editor(
        ensure_cols(ss.recipe_df, {"Material": "", "Percent": 0.0}),
        column_config={
            "Material": st.column_config.TextColumn("Material"),
            "Percent": st.column_config.NumberColumn("Percent", min_value=0.0, step=0.1),
        },
        num_rows="dynamic", 
        use_container_width=True, 
        key=recipe_editor_key  # Dynamic key forces refresh when recipe changes
    )

    # BATCH CALCULATION SECTION
    st.subheader("Batch calculator")
    
    colA, colB = st.columns([2, 1])
    with colA:
        batch_str = st.text_input("Batch size", value="100")
    with colB:
        unit = st.selectbox("Units", ["g", "oz", "lb"], index=0)

    def _to_float(s):
        try:
            return float(str(s).strip())
        except Exception:
            return 0.0

    batch_val = _to_float(batch_str)
    batch_g = batch_val if unit=="g" else batch_val*28.3495 if unit=="oz" else batch_val*453.592
    
    if batch_g <= 0:
        st.warning("Enter a positive batch size")
    else:
        out, batch_total, cpg, cpo, cpl = percent_recipe_table(ss.catalog_df, ss.recipe_df, batch_g)

        st.caption(f"Batch size {batch_g:.0f} g  •  {batch_g/28.3495:.2f} oz  •  {batch_g/453.592:.3f} lb")
        show = out.copy()
        if "Cost" in show.columns:
            show["Cost"] = show["Cost"].map(money)
        st.dataframe(show, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Batch total", money(batch_total))
        col2.metric("Cost per gram", money(cpg))
        col3.metric("Cost per ounce", money(cpo))
        st.metric("Cost per pound", money(cpl))

    # PER PIECE CALCULATION SECTION
    st.subheader("Per piece cost")
    
    grams_str = st.text_input("Grams used per piece", value=str(ss.get("recipe_grams_per_piece", 80.0)))
    try:
        ss.recipe_grams_per_piece = float(grams_str)
        if batch_g > 0:
            st.metric("Glaze cost per piece from this recipe", money(cpg * ss.recipe_grams_per_piece))
        else:
            st.caption("Enter a valid batch size above to see per-piece cost")
    except ValueError:
        st.warning("Please enter a number for grams per piece")
    

# ------------ Energy ------------
with tabs[3]:
    if ss.get("guidance_type") == "energy":
        st.success("✅ **Great choice!** Set up your exact kiln costs here.")
        st.markdown("💡 **Your Quick Start assumed basic costs.** Enter your specific rates and usage below for precision.")
        st.markdown("---")
    
    ip = ss.inputs

    
    # PRIMARY FUEL SELECTION
    st.subheader("Primary firing method")
    
    fuel_options = ["Electric Only", "Propane", "Natural Gas", "Wood", "Electric + Gas", "Electric + Wood"]
    current_fuel = str(ip.get("fuel_gas", "Propane"))
    if current_fuel not in fuel_options:
        current_fuel = "Propane"
    
    ip["fuel_gas"] = st.selectbox(
        "What do you primarily use for firing?", 
        fuel_options,
        index=fuel_options.index(current_fuel),
        key="energy_fuel_selector",
        help="💡 Choose your main firing method - this determines which cost fields to show"
    )
    
    # ELECTRIC SECTION (for Electric Only, Electric + Gas, Electric + Wood)
    if ip["fuel_gas"] in ["Electric Only", "Electric + Gas", "Electric + Wood"]:
        if ip["fuel_gas"] == "Electric Only":
            st.subheader("Electric kiln costs")
        else:
            st.subheader("Electric kiln costs")
            st.caption(f"💡 Electric portion of your {ip['fuel_gas'].lower()} setup")
        
        # Electric rate
        ip["kwh_rate"] = st.number_input(
            "Electricity rate per kWh", 
            min_value=0.0, 
            value=float(ip.get("kwh_rate", 0.24)), 
            step=0.01,
            help="💡 U.S. range: $0.10-0.30/kWh • Check your electric bill"
        )
        
        # Three firings for electric
        elec_col1, elec_col2, elec_col3 = st.columns(3)
        
        with elec_col1:
            st.markdown("**Bisque firing**")
            ip["kwh_bisque"] = st.number_input(
                "kWh per bisque", 
                min_value=0.0, 
                value=float(ip.get("kwh_bisque", 30.0)), 
                step=1.0,
                help="💡 Typical: 25-40 kWh"
            )
            ip["pieces_per_electric_bisque"] = st.number_input(
                "Pieces per electric bisque", 
                min_value=1, 
                value=int(ip.get("pieces_per_electric_bisque", 50)), 
                step=1,
                help="💡 Pack tight, no stilts"
            )
        
        with elec_col2:
            st.markdown("**Glaze firing**")
            ip["kwh_glaze"] = st.number_input(
                "kWh per glaze", 
                min_value=0.0, 
                value=float(ip.get("kwh_glaze", 35.0)), 
                step=1.0,
                help="💡 Typical: 30-45 kWh"
            )
            ip["pieces_per_electric_glaze"] = st.number_input(
                "Pieces per electric glaze", 
                min_value=1, 
                value=int(ip.get("pieces_per_electric_glaze", 40)), 
                step=1,
                help="💡 Need stilts, spacing"
            )
        
        with elec_col3:
            st.markdown("**Third firing** (luster, china paint)")
            ip["kwh_third"] = st.number_input(
                "kWh per third", 
                min_value=0.0, 
                value=float(ip.get("kwh_third", 25.0)), 
                step=1.0,
                help="💡 Lower temp: 20-30 kWh"
            )
            ip["pieces_per_electric_third"] = st.number_input(
                "Pieces per electric third", 
                min_value=0, 
                value=int(ip.get("pieces_per_electric_third", 0)), 
                step=1,
                help="💡 Default 0 = no third firing cost"
            )
    
    # PROPANE SECTION (for Propane, Electric + Gas)
    if ip["fuel_gas"] in ["Propane", "Electric + Gas"]:
        if ip["fuel_gas"] == "Electric + Gas":
            st.subheader("Propane costs (additional)")
            st.caption("💡 These costs will be added to your electric costs above")
        else:
            st.subheader("Propane costs")
        
        st.caption("💡 **Al's real data:** 1 tank bisque (~5 gal), 2 tanks glaze (~9 gal)")
        
        # Propane rate
        ip["lp_price_per_gal"] = st.number_input(
            "Propane price per gallon", 
            min_value=0.0, 
            value=float(ip.get("lp_price_per_gal", 3.50)), 
            step=0.05,
            help="💡 Typical: $2.50-4.50/gallon"
        )
        
        # Three firings for propane
        prop_col1, prop_col2, prop_col3 = st.columns(3)
        
        with prop_col1:
            st.markdown("**Bisque firing**")
            ip["lp_gal_bisque"] = st.number_input(
                "Gallons per bisque", 
                min_value=0.0, 
                value=float(ip.get("lp_gal_bisque", 4.7)), 
                step=0.1,
                help="💡 1 × 20lb tank ≈ 4.7 gal"
            )
            ip["pieces_per_propane_bisque"] = st.number_input(
                "Pieces per propane bisque", 
                min_value=1, 
                value=int(ip.get("pieces_per_propane_bisque", 50)), 
                step=1
            )
        
        with prop_col2:
            st.markdown("**Glaze firing**")
            ip["lp_gal_glaze"] = st.number_input(
                "Gallons per glaze", 
                min_value=0.0, 
                value=float(ip.get("lp_gal_glaze", 9.4)), 
                step=0.1,
                help="💡 2 × 20lb tanks ≈ 9.4 gal"
            )
            ip["pieces_per_propane_glaze"] = st.number_input(
                "Pieces per propane glaze", 
                min_value=1, 
                value=int(ip.get("pieces_per_propane_glaze", 40)), 
                step=1
            )
        
        with prop_col3:
            st.markdown("**Third firing**")
            ip["lp_gal_third"] = st.number_input(
                "Gallons per third", 
                min_value=0.0, 
                value=float(ip.get("lp_gal_third", 4.7)), 
                step=0.1,
                help="💡 Lower temp, less fuel"
            )
            ip["pieces_per_propane_third"] = st.number_input(
                "Pieces per propane third", 
                min_value=0, 
                value=int(ip.get("pieces_per_propane_third", 0)), 
                step=1,
                help="💡 Default 0 = no third firing cost"
            )
    
    # NATURAL GAS SECTION
    if ip["fuel_gas"] == "Natural Gas":
        st.subheader("Natural gas costs")
        
        # Natural gas rate
        ip["ng_price_per_therm"] = st.number_input(
            "Natural gas price per therm", 
            min_value=0.0, 
            value=float(ip.get("ng_price_per_therm", 1.20)), 
            step=0.05,
            help="💡 Typical: $0.80-2.00/therm"
        )
        
        # Three firings for natural gas
        ng_col1, ng_col2, ng_col3 = st.columns(3)
        
        with ng_col1:
            st.markdown("**Bisque firing**")
            ip["ng_therms_bisque"] = st.number_input(
                "Therms per bisque", 
                min_value=0.0, 
                value=float(ip.get("ng_therms_bisque", 8.0)), 
                step=0.1
            )
            ip["pieces_per_ng_bisque"] = st.number_input(
                "Pieces per NG bisque", 
                min_value=1, 
                value=int(ip.get("pieces_per_ng_bisque", 50)), 
                step=1
            )
        
        with ng_col2:
            st.markdown("**Glaze firing**")
            ip["ng_therms_glaze"] = st.number_input(
                "Therms per glaze", 
                min_value=0.0, 
                value=float(ip.get("ng_therms_glaze", 12.0)), 
                step=0.1
            )
            ip["pieces_per_ng_glaze"] = st.number_input(
                "Pieces per NG glaze", 
                min_value=1, 
                value=int(ip.get("pieces_per_ng_glaze", 40)), 
                step=1
            )
        
        with ng_col3:
            st.markdown("**Third firing**")
            ip["ng_therms_third"] = st.number_input(
                "Therms per third", 
                min_value=0.0, 
                value=float(ip.get("ng_therms_third", 6.0)), 
                step=0.1
            )
            ip["pieces_per_ng_third"] = st.number_input(
                "Pieces per NG third", 
                min_value=0, 
                value=int(ip.get("pieces_per_ng_third", 0)), 
                step=1,
                help="💡 Default 0 = no third firing cost"
            )
    
    # WOOD SECTION (for Wood, Electric + Wood)
    if ip["fuel_gas"] in ["Wood", "Electric + Wood"]:
        if ip["fuel_gas"] == "Electric + Wood":
            st.subheader("Wood firing costs (additional)")
            st.caption("💡 These costs will be added to your electric costs above")
        else:
            st.subheader("Wood firing costs")
        
        st.caption("💡 **Wood firing:** Often electric bisque + wood glaze. Third firing rare with wood.")
        
        # Wood pricing
        wood_price_col1, wood_price_col2 = st.columns(2)
        with wood_price_col1:
            ip["wood_price_per_cord"] = st.number_input(
                "Wood price per cord", 
                min_value=0.0, 
                value=float(ip.get("wood_price_per_cord", 300.0)), 
                step=1.0,
                help="💡 Full cord: 4' × 4' × 8'"
            )
        with wood_price_col2:
            ip["wood_price_per_facecord"] = st.number_input(
                "Wood price per face cord", 
                min_value=0.0, 
                value=float(ip.get("wood_price_per_facecord", 120.0)), 
                step=1.0,
                help="💡 Face cord ≈ 1/3 full cord"
            )
        
        # Three firings for wood (though bisque and third often not used)
        wood_col1, wood_col2, wood_col3 = st.columns(3)
        
        with wood_col1:
            st.markdown("**Bisque firing** (rare)")
            ip["wood_cords_bisque"] = st.number_input(
                "Cords per bisque", 
                min_value=0.0, 
                value=float(ip.get("wood_cords_bisque", 0.0)), 
                step=0.05,
                help="💡 Usually electric for bisque"
            )
            ip["wood_facecords_bisque"] = st.number_input(
                "Face cords per bisque", 
                min_value=0.0, 
                value=float(ip.get("wood_facecords_bisque", 0.0)), 
                step=0.1
            )
            ip["pieces_per_wood_bisque"] = st.number_input(
                "Pieces per wood bisque", 
                min_value=1, 
                value=int(ip.get("pieces_per_wood_bisque", 40)), 
                step=1
            )
        
        with wood_col2:
            st.markdown("**Glaze firing** (main)")
            ip["wood_cords_glaze"] = st.number_input(
                "Cords per glaze", 
                min_value=0.0, 
                value=float(ip.get("wood_cords_glaze", 1.5)), 
                step=0.05,
                help="💡 Weekend firing: 1-2 cords"
            )
            ip["wood_facecords_glaze"] = st.number_input(
                "Face cords per glaze", 
                min_value=0.0, 
                value=float(ip.get("wood_facecords_glaze", 0.0)), 
                step=0.1
            )
            ip["pieces_per_wood_glaze"] = st.number_input(
                "Pieces per wood glaze", 
                min_value=1, 
                value=int(ip.get("pieces_per_wood_glaze", 40)), 
                step=1
            )
        
        with wood_col3:
            st.markdown("**Third firing** (very rare)")
            ip["wood_cords_third"] = st.number_input(
                "Cords per third", 
                min_value=0.0, 
                value=float(ip.get("wood_cords_third", 0.0)), 
                step=0.05,
                help="💡 Rarely done with wood"
            )
            ip["wood_facecords_third"] = st.number_input(
                "Face cords per third", 
                min_value=0.0, 
                value=float(ip.get("wood_facecords_third", 0.0)), 
                step=0.1
            )
            ip["pieces_per_wood_third"] = st.number_input(
                "Pieces per wood third", 
                min_value=0, 
                value=int(ip.get("pieces_per_wood_third", 0)), 
                step=1,
                help="💡 Default 0 = no cost"
            )
    
    # RESULTS SECTION
    st.subheader("Per piece energy cost")
    energy_cost = calc_energy(ip)
    st.metric("Energy per piece", money(energy_cost))
    
    # Detailed breakdown
    if energy_cost > 0:
        with st.expander("🔍 Cost breakdown", expanded=False):
            if ip["fuel_gas"] == "Electric Only":
                bisque_cost = ip.get("kwh_bisque", 0) * ip.get("kwh_rate", 0) / max(1, ip.get("pieces_per_electric_bisque", 1))
                glaze_cost = ip.get("kwh_glaze", 0) * ip.get("kwh_rate", 0) / max(1, ip.get("pieces_per_electric_glaze", 1))
                third_pieces = max(1, ip.get("pieces_per_electric_third", 1)) if ip.get("pieces_per_electric_third", 0) > 0 else 1
                third_cost = ip.get("kwh_third", 0) * ip.get("kwh_rate", 0) / third_pieces if ip.get("pieces_per_electric_third", 0) > 0 else 0
                st.write(f"• Bisque: {money(bisque_cost)} per piece")
                st.write(f"• Glaze: {money(glaze_cost)} per piece") 
                st.write(f"• Third: {money(third_cost)} per piece")
                
            elif ip["fuel_gas"] == "Propane":
                bisque_cost = ip.get("lp_gal_bisque", 0) * ip.get("lp_price_per_gal", 0) / max(1, ip.get("pieces_per_propane_bisque", 1))
                glaze_cost = ip.get("lp_gal_glaze", 0) * ip.get("lp_price_per_gal", 0) / max(1, ip.get("pieces_per_propane_glaze", 1))
                third_pieces = max(1, ip.get("pieces_per_propane_third", 1)) if ip.get("pieces_per_propane_third", 0) > 0 else 1
                third_cost = ip.get("lp_gal_third", 0) * ip.get("lp_price_per_gal", 0) / third_pieces if ip.get("pieces_per_propane_third", 0) > 0 else 0
                st.write(f"• Bisque: {money(bisque_cost)} per piece")
                st.write(f"• Glaze: {money(glaze_cost)} per piece")
                st.write(f"• Third: {money(third_cost)} per piece")
                
            else:
                st.write(f"Combined {ip['fuel_gas'].lower()} firing costs")
    else:
        st.caption("💡 Set your firing costs above to see energy cost per piece")

with tabs[4]:  # Production Planning tab
    st.header("🏭 Production Planning")
    st.markdown("**Plan your pottery production with real studio workflow**")
    
    # FORM SELECTION
    st.subheader("1. What are you making?")
    
    # Get all available forms from unified database
    unified_forms = ss.unified_forms.copy()
    available_forms = list(unified_forms["Form"]) if not unified_forms.empty else []
    
    selected_form = st.selectbox(
    "Choose form type:",
    ["None", "➕ Add New Form"] + available_forms,
    help="Select from your unified form database or add a new form with timing"
)
    
    # ADD NEW FORM TO UNIFIED DATABASE
    if selected_form == "➕ Add New Form":
        st.markdown("**Add new form to unified database**")
        
        with st.expander("Add new form with complete data", expanded=True):
            new_col1, new_col2 = st.columns(2)
            
            with new_col1:
                new_form_name = st.text_input("Form name (e.g., 'Large Vase', 'Dinner Plate')")
                new_clay_lb = st.number_input("Clay weight (lb wet)", min_value=0.0, step=0.1, value=1.0)
                new_glaze_g = st.number_input("Glaze amount (grams)", min_value=0.0, step=1.0, value=100.0)
                new_throwing = st.number_input("Throwing time (minutes per piece)", min_value=0.0, step=0.1, value=5.0)
                new_trimming = st.number_input("Trimming time (minutes per piece)", min_value=0.0, step=0.1, value=0.0)
            
            with new_col2:
                new_handling = st.number_input("Handling time (minutes per piece)", min_value=0.0, step=0.1, value=0.0)
                new_glazing = st.number_input("Glazing time (minutes per piece)", min_value=0.0, step=0.1, value=6.0)
                new_pieces_shelf = st.number_input("Pieces per kiln shelf", min_value=1, step=1, value=12)
                new_notes = st.text_input("Notes (optional)")
            
            if st.button("Add New Form to Database") and new_form_name.strip():
                new_unified_form = pd.DataFrame([{
                    "Form": new_form_name.strip(),
                    "Clay_lb_wet": new_clay_lb,
                    "Default_glaze_g": new_glaze_g,
                    "Throwing_min": new_throwing,
                    "Trimming_min": new_trimming, 
                    "Handling_min": new_handling,
                    "Glazing_min": new_glazing,
                    "Pieces_per_shelf": new_pieces_shelf,
                    "Notes": new_notes
                }])
                
                # Remove existing form with same name, then add new one
                ss.unified_forms = ss.unified_forms[ss.unified_forms["Form"] != new_form_name.strip()]
                ss.unified_forms = pd.concat([ss.unified_forms, new_unified_form], ignore_index=True)
                
                st.success(f"Added {new_form_name} to unified form database!")
                st.rerun()
    
    # PRODUCTION CALCULATION  
    if selected_form not in ["None", "➕ Add New Form"] and selected_form:
        # Get form data from unified database
        form_data = unified_forms[unified_forms["Form"] == selected_form].iloc[0]
        
        # Display form info
        st.markdown(f"**Selected: {selected_form}**")
        
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        info_col1.metric("Throwing", f"{form_data['Throwing_min']:.1f} min")
        info_col2.metric("Trimming", f"{form_data['Trimming_min']:.1f} min")
        info_col3.metric("Handling", f"{form_data['Handling_min']:.1f} min") 
        info_col4.metric("Glazing", f"{form_data['Glazing_min']:.1f} min")
        
        # Show clay and glaze data too
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        detail_col1.metric("Clay weight", f"{form_data['Clay_lb_wet']:.2f} lb")
        detail_col2.metric("Glaze amount", f"{form_data['Default_glaze_g']:.0f} g")
        detail_col3.metric("Per shelf", f"{int(form_data['Pieces_per_shelf'])} pcs")
        
        if form_data["Notes"]:
            st.caption(f"💡 {form_data['Notes']}")
        
        st.markdown("---")
        
        # ORDER DETAILS
        st.subheader("2. Order details")
        
        order_col1, order_col2, order_col3 = st.columns(3)
        
        with order_col1:
            quantity = st.number_input("Quantity to make", min_value=1, step=1, value=18)
            
        with order_col2:
            trim_option = st.radio("Trimming?", ["No trim", "Trim all"], horizontal=True)
            do_trimming = (trim_option == "Trim all")
            
        with order_col3:
            start_date = st.date_input("Start date", value=_dt.date.today())
        
        # TIMELINE CALCULATION
        st.subheader("3. Production timeline")
        
        # Calculate times
        throwing_total = quantity * form_data["Throwing_min"]
        trimming_total = quantity * form_data["Trimming_min"] if do_trimming else 0
        handling_total = quantity * form_data["Handling_min"]
        glazing_total = quantity * form_data["Glazing_min"]
        
        # Kiln calculations (using pieces per shelf and your 4-shelf kiln)
        pieces_per_shelf = int(form_data["Pieces_per_shelf"])
        pieces_per_kiln = pieces_per_shelf * 4  # 4 shelves
        kiln_loads_needed = int((quantity + pieces_per_kiln - 1) // pieces_per_kiln)
        
        # Fixed process times (Al's data)
        initial_drying_hours = 2
        final_drying_hours = 12
        bisque_fire_hours = 8
        bisque_cool_hours = 12
        glaze_fire_hours = 8
        glaze_cool_hours = 24  # 1 day cool
        loading_hours_per_kiln = 1
        
        # Calculate total calendar time
        hands_on_hours = (throwing_total + trimming_total + handling_total + glazing_total) / 60
        kiln_loading_hours = kiln_loads_needed * loading_hours_per_kiln * 2  # bisque + glaze loading
        
        # Calendar time calculation
        process_hours = (
            initial_drying_hours +
            final_drying_hours + 
            (bisque_fire_hours + bisque_cool_hours) * kiln_loads_needed +
            (glaze_fire_hours + glaze_cool_hours) * kiln_loads_needed
        )
        
        total_calendar_days = (hands_on_hours + kiln_loading_hours + process_hours) / 24
        
        # Results
        result_col1, result_col2 = st.columns(2)
        
        with result_col1:
            st.markdown("**⏱️ Hands-on time breakdown**")
            st.write(f"• Throwing: {throwing_total/60:.1f} hours")
            if do_trimming:
                st.write(f"• Trimming: {trimming_total/60:.1f} hours")
            if handling_total > 0:
                st.write(f"• Handling: {handling_total/60:.1f} hours")
            st.write(f"• Glazing: {glazing_total/60:.1f} hours")
            st.write(f"• Kiln loading: {kiln_loading_hours:.1f} hours")
            st.write(f"**Total hands-on: {hands_on_hours + kiln_loading_hours:.1f} hours**")
        
        with result_col2:
            st.markdown("**🔥 Kiln schedule**")
            st.write(f"• Kiln loads needed: {kiln_loads_needed}")
            st.write(f"• Pieces per load: {pieces_per_kiln}")
            st.write(f"• Bisque firing: {bisque_fire_hours}h fire + {bisque_cool_hours}h cool")
            st.write(f"• Glaze firing: {glaze_fire_hours}h fire + {glaze_cool_hours}h cool")
            st.write(f"**Total process time: {process_hours/24:.1f} days**")
        
        # DELIVERY ESTIMATE
        import datetime as dt
        
        delivery_date = start_date + _dt.timedelta(days=int(total_calendar_days) + (1 if total_calendar_days != int(total_calendar_days) else 0))
        
        st.markdown("---")
        st.subheader("📅 Delivery estimate")
        
        big_col1, big_col2, big_col3 = st.columns(3)
        big_col1.metric("Total calendar time", f"{total_calendar_days:.1f} days")
        big_col2.metric("Hands-on labor", f"{hands_on_hours + kiln_loading_hours:.1f} hours")
        big_col3.metric("Ready date", delivery_date.strftime("%B %d, %Y"))
        
        # COST INTEGRATION (NEW!)
        st.markdown("---")
        st.subheader("💰 Cost for this order")
        
        # Calculate costs using unified form data
        clay_weight_total = quantity * form_data["Clay_lb_wet"]
        glaze_grams_total = quantity * form_data["Default_glaze_g"]
        labor_hours_total = hands_on_hours + kiln_loading_hours
        
        cost_col1, cost_col2, cost_col3 = st.columns(3)
        cost_col1.metric("Total clay needed", f"{clay_weight_total:.1f} lb")
        cost_col2.metric("Total glaze needed", f"{glaze_grams_total:.0f} g")
        cost_col3.metric("Total labor hours", f"{labor_hours_total:.1f} hrs")
        
        # Use current cost settings to estimate order cost
        clay_cost_per_lb = ss.inputs["clay_price_per_bag"] / ss.inputs["clay_bag_weight_lb"] if ss.inputs["clay_bag_weight_lb"] else 0.0
        total_clay_cost = (clay_weight_total / ss.inputs.get("clay_yield", 0.9)) * clay_cost_per_lb
        total_labor_cost = labor_hours_total * ss.inputs.get("labor_rate", 15.0)
        
        st.write(f"**Estimated order costs:**")
        st.write(f"• Clay: {money(total_clay_cost)}")
        st.write(f"• Labor: {money(total_labor_cost)}")
        st.write(f"• **Subtotal: {money(total_clay_cost + total_labor_cost)}** (excludes glaze, energy, overhead)")
        
        # QUICK APPLY TO COST CALCULATOR
        if st.button("📊 Use this form in cost calculator"):
            ss.inputs["clay_weight_per_piece_lb"] = form_data["Clay_lb_wet"]
            ss.recipe_grams_per_piece = form_data["Default_glaze_g"]
            total_time_hours = (form_data["Throwing_min"] + form_data["Trimming_min"] + 
                              form_data["Handling_min"] + form_data["Glazing_min"]) / 60.0
            if total_time_hours > 0:
                ss.inputs["hours_per_piece"] = total_time_hours
            st.success("✅ Applied form data to cost calculator! Check the 'Per Unit' and 'Pricing' tabs.")
    
    else:
        st.info("👆 Select a form above to see production planning and cost estimates.")

# DETAILED BREAKDOWN (add this after the delivery estimate section)
        with st.expander("🔍 Detailed process breakdown", expanded=False):
            st.markdown("**Step-by-step timeline:**")
            current_time = 0
            
with tabs[5]:  # Kiln Load Planner
    st.header("🔥 Kiln Load Planner")
    st.markdown("**Plan your kiln loads with cost calculations**")
    
    # Initialize session state for kiln planning
    if "kiln_shelves" not in ss:
        ss.kiln_shelves = []
    if "firing_type" not in ss:
        ss.firing_type = "Bisque"
    
    # FIRING TYPE SELECTION
    col1, col2 = st.columns([1, 3])
    with col1:
        ss.firing_type = st.radio(
            "Firing type:",
            ["Bisque", "Glaze"],
            horizontal=True,
            key="kiln_firing_type",
            help="Bisque allows tighter packing, Glaze needs spacing for glazes"
        )
    
    with col2:
        if ss.firing_type == "Bisque":
            st.info("💡 **Bisque firing:** You can pack tighter, some pieces can tumble stack")
        else:
            st.warning("💡 **Glaze firing:** Leave space between pieces, no touching, use stilts")
    
    st.markdown("---")
    
    # SHELF MANAGEMENT
    shelf_col1, shelf_col2 = st.columns([2, 1])
    
    with shelf_col1:
        st.subheader("📚 Kiln Shelves")
        
        if st.button("➕ Add Shelf", key="add_shelf_btn"):
            new_shelf = {
                "shelf_id": len(ss.kiln_shelves),
                "capacity": 12,  # Default capacity
                "items": []  # List of {form, quantity} dicts
            }
            ss.kiln_shelves.append(new_shelf)
            st.rerun()
    
    with shelf_col2:
        if len(ss.kiln_shelves) > 0:
            st.metric("Total Shelves", len(ss.kiln_shelves))
            
            # Clear all shelves button
            if st.button("🗑️ Clear All Shelves", key="clear_all_shelves"):
                ss.kiln_shelves = []
                st.rerun()
    
    # DISPLAY SHELVES
    if not ss.kiln_shelves:
        st.info("👆 Click 'Add Shelf' to start planning your kiln load")
    else:
        total_pieces = 0
        all_items = []  # For cost calculation
        
        for i, shelf in enumerate(ss.kiln_shelves):
            st.markdown(f"### Shelf {i+1}")
            
            shelf_setup_col, shelf_content_col, shelf_actions_col = st.columns([1, 2, 1])
            
            # SHELF CAPACITY
            with shelf_setup_col:
                shelf["capacity"] = st.number_input(
                    f"Max pieces:",
                    min_value=1,
                    max_value=50,
                    value=shelf["capacity"],
                    step=1,
                    key=f"shelf_{i}_capacity"
                )
                
                # Remove shelf button
                if st.button(f"🗑️ Remove", key=f"remove_shelf_{i}"):
                    ss.kiln_shelves.pop(i)
                    st.rerun()
            
            # ADD ITEMS TO SHELF
            with shelf_content_col:
                # Form selector - get available forms
                unified_forms = ss.unified_forms.copy()
                available_forms = list(unified_forms["Form"]) if not unified_forms.empty else []
                
                add_col1, add_col2, add_col3 = st.columns([2, 1, 1])
                
                with add_col1:
                    selected_form = st.selectbox(
                        "Add form:",
                        ["Select form...", "➕ Custom Entry"] + available_forms,
                        key=f"shelf_{i}_form_selector"
                    )
                
                with add_col2:
                    quantity = st.number_input(
                        "Qty:",
                        min_value=1,
                        max_value=shelf["capacity"],
                        value=1,
                        key=f"shelf_{i}_quantity"
                    )
                
                with add_col3:
                    if st.button("Add", key=f"shelf_{i}_add_btn"):
                        if selected_form not in ["Select form...", "➕ Custom Entry"]:
                            # Check if there's room
                            current_items = sum(item["quantity"] for item in shelf["items"])
                            if current_items + quantity <= shelf["capacity"]:
                                # Add to shelf
                                shelf["items"].append({
                                    "form": selected_form,
                                    "quantity": quantity
                                })
                                st.rerun()
                            else:
                                st.error(f"Not enough space! Shelf capacity: {shelf['capacity']}, Current: {current_items}")
                        elif selected_form == "➕ Custom Entry":
                            # Handle custom entry
                            st.info("💡 Enter custom form name in the selectbox above")
                
                # CURRENT SHELF CONTENTS
                if shelf["items"]:
                    st.markdown("**Current contents:**")
                    shelf_total = 0
                    for j, item in enumerate(shelf["items"]):
                        item_col1, item_col2 = st.columns([3, 1])
                        with item_col1:
                            st.write(f"• {item['quantity']}× {item['form']}")
                        with item_col2:
                            if st.button("Remove", key=f"shelf_{i}_item_{j}_remove"):
                                shelf["items"].pop(j)
                                st.rerun()
                        shelf_total += item["quantity"]
                        total_pieces += item["quantity"]
                        all_items.append(item)  # For cost calculation
                else:
                    st.caption("Empty shelf")
                    shelf_total = 0
            
            # SHELF UTILIZATION
            with shelf_actions_col:
                utilization = (shelf_total / shelf["capacity"]) * 100 if shelf["capacity"] > 0 else 0
                st.metric("Used", f"{shelf_total}/{shelf['capacity']}")
                
                # Visual utilization bar
                if utilization > 90:
                    st.progress(utilization/100, text=f"{utilization:.0f}% Full")
                elif utilization > 70:
                    st.progress(utilization/100, text=f"{utilization:.0f}% Good")
                else:
                    st.progress(utilization/100, text=f"{utilization:.0f}% Space")
            
            st.markdown("---")
        
        # KILN LOAD SUMMARY
        if total_pieces > 0:
            st.subheader("📊 Kiln Load Summary")
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("Total Pieces", total_pieces)
                st.metric("Shelves Used", len([s for s in ss.kiln_shelves if s["items"]]))
            
            with summary_col2:
                # Energy cost calculation
                firing_type = ss.firing_type.lower()
                if ss.inputs.get("fuel_gas", "Electric") == "Electric":
                    if firing_type == "bisque":
                        energy_per_firing = ss.inputs.get("kwh_bisque", 30.0) * ss.inputs.get("kwh_rate", 0.24)
                    else:  # glaze
                        energy_per_firing = ss.inputs.get("kwh_glaze", 35.0) * ss.inputs.get("kwh_rate", 0.24)
                elif ss.inputs.get("fuel_gas", "Electric") == "Propane":
                    if firing_type == "bisque":
                        energy_per_firing = ss.inputs.get("lp_gal_bisque", 4.7) * ss.inputs.get("lp_price_per_gal", 3.50)
                    else:  # glaze
                        energy_per_firing = ss.inputs.get("lp_gal_glaze", 9.4) * ss.inputs.get("lp_price_per_gal", 3.50)
                else:
                    energy_per_firing = 25.0  # Default estimate
                
                energy_per_piece = energy_per_firing / max(1, total_pieces)
                
                st.metric("Energy Cost", money(energy_per_firing))
                st.metric("Per Piece", money(energy_per_piece))
            
            with summary_col3:
                # Firing time estimate
                if firing_type == "bisque":
                    firing_hours = 8 + 12  # fire + cool
                else:  # glaze
                    firing_hours = 8 + 24  # fire + cool
                
                st.metric("Firing Time", f"{firing_hours}h")
                
                # Efficiency rating
                avg_utilization = sum((sum(item["quantity"] for item in shelf["items"]) / shelf["capacity"]) * 100 
                                    for shelf in ss.kiln_shelves if shelf["items"]) / max(1, len([s for s in ss.kiln_shelves if s["items"]]))
                
                if avg_utilization > 85:
                    efficiency = "🟢 Excellent"
                elif avg_utilization > 70:
                    efficiency = "🟡 Good"
                else:
                    efficiency = "🔴 Consider adding more"
                
                st.metric("Load Efficiency", f"{avg_utilization:.0f}%")
                st.caption(efficiency)
            
            # DETAILED BREAKDOWN
            with st.expander("🔍 Detailed breakdown", expanded=False):
                st.markdown("**Items by type:**")
                
                # Group items by form
                item_summary = {}
                for item in all_items:
                    form = item["form"]
                    if form in item_summary:
                        item_summary[form] += item["quantity"]
                    else:
                        item_summary[form] = item["quantity"]
                
                for form, total_qty in item_summary.items():
                    st.write(f"• {total_qty}× {form}")
                
                st.markdown("**Energy cost breakdown:**")
                fuel_type = ss.inputs.get("fuel_gas", "Electric")
                st.write(f"• Fuel: {fuel_type}")
                st.write(f"• {firing_type.title()} firing cost: {money(energy_per_firing)}")
                st.write(f"• Cost per piece: {money(energy_per_piece)}")
                
# ------------ Labor and overhead ------------
with tabs[6]:
    ip = ss.inputs
   
    st.subheader("Labor")
    ip["labor_rate"] = st.number_input("Labor rate per hour", min_value=0.0, value=float(ip["labor_rate"]), step=1.0)
    ip["hours_per_piece"] = st.number_input("Hours per piece", min_value=0.0, value=float(ip["hours_per_piece"]), step=0.05)

    st.subheader("Overhead")
    ip["overhead_per_month"] = st.number_input("Overhead per month", min_value=0.0, value=float(ip["overhead_per_month"]), step=10.0)
    ip["pieces_per_month"] = st.number_input("Pieces per month", min_value=1, value=int(ip["pieces_per_month"]), step=10)
    
# ------------ Pricing ------------
with tabs[7]:
    ip = ss.inputs
    

    st.subheader("Pricing Options")
    ip["use_2x2x2"] = st.checkbox("Use 2x2x2 rule", value=ip.get("use_2x2x2", False))

    if not ip["use_2x2x2"]:
        ip["wholesale_margin_pct"] = st.slider(
            "Wholesale margin percent",
            min_value=0, max_value=90,
            value=int(ip.get("wholesale_margin_pct", 50)), step=1
        )
        ip["retail_multiplier"] = st.number_input(
            "Retail multiplier",
            min_value=1.0, value=float(ip.get("retail_multiplier", 2.2)), step=0.1
        )

    mode = st.radio("Glaze cost source", ["Recipe tab", "Manual table"], horizontal=True)
    if mode == "Manual table":
        glaze_pp_cost, _ = glaze_cost_from_piece_table(ss.glaze_piece_df)
    else:
        grams_pp = float(ss.get("recipe_grams_per_piece", 8.0))
        _, glaze_pp_cost = glaze_per_piece_from_recipe(ss.catalog_df, ss.recipe_df, grams_pp)

    other_pp, _, _ = other_materials_pp(ss.other_mat_df, int(ss.inputs["units_made"]))
    totals = calc_totals(ip, glaze_pp_cost, other_pp)

    st.subheader("Results")

    c = st.columns(3)
    c[0].metric("Wholesale", money(totals["wholesale"]))
    c[1].metric("Retail", money(totals["retail"]))
    if totals["distributor"] is not None:
        c[2].metric("Distributor", money(totals["distributor"]))

    c2 = st.columns(3)
    c2[0].metric("Clay", money(totals["clay_pp"]))
    c2[1].metric("Glaze", money(totals["glaze_pp"]))
    c2[2].metric("Packaging", money(totals["pack_pp"]))

    c3 = st.columns(3)
    c3[0].metric("Other materials", money(totals["other_pp"]))
    c3[1].metric("Energy", money(totals["energy_pp"]))
    c3[2].metric("Labor", money(totals["labor_pp"]))

    st.metric("Overhead", money(totals["oh_pp"]))
    st.metric("Total cost per piece", money(totals["total_pp"]))



# ---------------- Shipping & Tariffs (functionalized) ----------------
with tabs[8]:
    ip = ss.inputs
with tabs[tab_titles.index("Shipping & Tariffs")]:
    import math

    # ---------- helpers ----------
    def _money(v: float) -> str:
        # use your global money() if it exists, else local fallback
        try:
            return money(v)  # type: ignore[name-defined]
        except Exception:
            try:
                return f"${float(v):,.2f}"
            except Exception:
                return "$0.00"

    def _calc_dim_weight(l_in: float, w_in: float, h_in: float, divisor: int = 139) -> float:
        """Air dimensional weight (lb)."""
        if l_in <= 0 or w_in <= 0 or h_in <= 0:
            return 0.0
        return (l_in * w_in * h_in) / divisor

    def render_summary_band():
        """Top 4 metrics; returns the metric columns so downstream can update them."""
        sum_c1, sum_c2, sum_c3, sum_c4 = st.columns([1, 1, 1, 1])
        sum_c1.metric("Package weight", "—")
        sum_c2.metric("Ship cost", "$0.00")
        sum_c3.metric("Tariffs/VAT", "$0.00")
        sum_c4.metric("Landed total", "$0.00")
        return sum_c1, sum_c2, sum_c3, sum_c4

    def render_domestic(sum_cols):
        """Domestic shipping estimator and metric updater."""
        sum_c1, sum_c2, sum_c3, sum_c4 = sum_cols

        st.subheader("Domestic shipping (U.S.)")
        c1, c2, c3 = st.columns(3)
        with c1:
            pkg_weight_lb = st.number_input("Actual weight (lb)", min_value=0.0, step=0.1, value=3.0, key="dom_w")
            zone = st.selectbox("Zone", ["Local", "Zone 2–4", "Zone 5–8"], index=1, key="dom_zone")
        with c2:
            speed = st.selectbox("Service speed", ["Ground", "2-Day", "Overnight"], index=0, key="dom_speed")
            insurance = st.number_input("Insurance (declared value $)", min_value=0.0, step=10.0, value=0.0, key="dom_ins")
        with c3:
            handling = st.number_input("Packing/handling time (mins)", min_value=0, step=5, value=10, key="dom_handling")
            labor_rate = st.number_input("Shop labor $/hr", min_value=0.0, step=1.0, value=20.0, key="dom_rate")

        dim_wt = 0.0
        with st.expander("Box size & dimensional weight (optional)"):
            b1, b2, b3, b4 = st.columns(4)
            with b1: L = st.number_input("Length (in)", min_value=0.0, step=0.1, value=12.0, key="dom_L")
            with b2: W = st.number_input("Width (in)",  min_value=0.0, step=0.1, value=10.0, key="dom_W")
            with b3: H = st.number_input("Height (in)", min_value=0.0, step=0.1, value=8.0,  key="dom_H")
            with b4: dim_div = st.number_input("Dim divisor", min_value=100, step=1, value=139, key="dom_div")
            dim_wt = _calc_dim_weight(L, W, H, dim_div)
            st.caption(f"Dimensional weight ≈ **{dim_wt:.2f} lb** (billable uses max of actual vs dim).")

        billable_lb = max(pkg_weight_lb, dim_wt)

        # very simple base rate model (tweak to your table)
        zone_factor = {"Local": 0.9, "Zone 2–4": 1.0, "Zone 5–8": 1.25}[zone]
        speed_factor = {"Ground": 1.0, "2-Day": 1.9, "Overnight": 3.2}[speed]
        base = 8.00 + (billable_lb * 1.10)  # base + per-lb
        ship_cost = base * zone_factor * speed_factor

        # insurance & surcharges
        insurance_fee = 0.0 if insurance <= 0 else max(2.0, 0.01 * insurance)
        fuel_surcharge = 0.09 * ship_cost
        residential_fee = st.checkbox("Residential delivery", value=True, key="dom_res")
        residential = 4.25 if residential_fee else 0.0
        signature = st.checkbox("Signature required", value=False, key="dom_sig")
        signature_fee = 3.75 if signature else 0.0

        handling_cost = (handling / 60.0) * labor_rate

        domestic_total = ship_cost + fuel_surcharge + insurance_fee + residential + signature_fee + handling_cost

        # Breakdown
        st.markdown("**Breakdown**")
        st.write(
            f"- Billable weight: **{billable_lb:.2f} lb**  "
            f"\n- Base ship: {_money(ship_cost)}  "
            f"\n- Fuel (est.): {_money(fuel_surcharge)}  "
            f"\n- Insurance: {_money(insurance_fee)}  "
            f"\n- Residential: {_money(residential)}  "
            f"\n- Signature: {_money(signature_fee)}  "
            f"\n- Handling: {_money(handling_cost)}"
        )
        st.success(f"Estimated domestic ship cost: **{_money(domestic_total)}**")

        # update summary band
        sum_c1.metric("Package weight", f"{billable_lb:.2f} lb")
        sum_c2.metric("Ship cost", _money(domestic_total))
        sum_c3.metric("Tariffs/VAT", _money(0.0))
        sum_c4.metric("Landed total", _money(domestic_total))

    def render_international(sum_cols):
        """International shipping + tariffs/VAT and metric updater."""
        sum_c1, sum_c2, sum_c3, sum_c4 = sum_cols

        st.subheader("International shipping (optional details below)")
        i1, i2, i3 = st.columns(3)
        with i1:
            pkg_weight_kg = st.number_input("Actual weight (kg)", min_value=0.0, step=0.1, value=1.5, key="int_w")
            country = st.text_input("Destination country", value="Canada", key="int_country")
        with i2:
            ship_speed = st.selectbox("Service", ["Postal tracked", "Express courier"], index=0, key="int_speed")
            fx = st.number_input("FX rate (USD→local)", min_value=0.01, step=0.01, value=1.35, key="int_fx")
        with i3:
            declared = st.number_input("Declared customs value (USD)", min_value=0.0, step=5.0, value=120.0, key="int_decl")
            shipping_usd = st.number_input("Carrier shipping (USD)", min_value=0.0, step=1.0, value=28.0, key="int_ship")

        # Tariffs & taxes in an expander
        with st.expander("Tariffs / VAT / clearance (toggle as needed)", expanded=False):
            t1, t2, t3 = st.columns(3)
            with t1:
                duty_rate = st.number_input("Duty rate %", min_value=0.0, step=0.5, value=5.0, key="int_duty")
                de_minimis = st.number_input("De minimis threshold (local)", min_value=0.0, step=1.0, value=0.0, key="int_min")
            with t2:
                vat_rate = st.number_input("VAT / GST %", min_value=0.0, step=0.5, value=13.0, key="int_vat")
                vat_on_ship = st.checkbox("VAT applies to shipping?", value=True, key="int_vat_ship")
            with t3:
                brokerage = st.number_input("Brokerage/clearance fee (local)", min_value=0.0, step=1.0, value=12.0, key="int_broker")
                collection_fee = st.number_input("Carrier collection fee (local)", min_value=0.0, step=1.0, value=0.0, key="int_collect")

            customs_base_local = declared * fx
            duty_local = 0.0 if customs_base_local <= de_minimis else customs_base_local * (duty_rate / 100.0)
            vat_base_local = customs_base_local + (shipping_usd * fx if vat_on_ship else 0.0) + duty_local
            vat_local = 0.0 if customs_base_local <= de_minimis else vat_base_local * (vat_rate / 100.0)

            gov_charges_local = duty_local + vat_local
            fees_local = brokerage + collection_fee
            landed_local = (shipping_usd * fx) + gov_charges_local + fees_local
            landed_usd = landed_local / fx if fx else 0.0

            st.markdown("**Customs/tax breakdown (local currency)**")
            st.write(
                f"- Customs value: **{customs_base_local:,.2f}**  "
                f"\n- Duty: {duty_local:,.2f}  "
                f"\n- VAT/GST: {vat_local:,.2f}  "
                f"\n- Brokerage & fees: {fees_local:,.2f}"
            )
            st.info(f"International surcharges: **{(gov_charges_local + fees_local):,.2f} local**")

        border_usd = (gov_charges_local + fees_local) / fx if fx else 0.0
        total_usd = shipping_usd + border_usd

        st.success(
            f"Landed shipping + border cost: shipping **{_money(shipping_usd)}** + border **{_money(border_usd)}** "
            f"= **{_money(total_usd)}**"
        )

        sum_c1.metric("Package weight", f"{pkg_weight_kg:.2f} kg")
        sum_c2.metric("Ship cost", _money(shipping_usd))
        sum_c3.metric("Tariffs/VAT", _money(border_usd))
        sum_c4.metric("Landed total", _money(total_usd))

    # ---------- Tab body ----------
    st.header("Shipping & Tariffs")
    sum_cols = render_summary_band()
    st.divider()

    mode = st.radio(
        "What do you need to estimate?",
        ["Domestic (U.S.)", "International + Tariffs/VAT"],
        horizontal=True,
        key="ship_mode",
    )

    if mode == "Domestic (U.S.)":
        render_domestic(sum_cols)
    else:
        render_international(sum_cols)


# ------------ Save and load ------------
with tabs[8]:
    
    st.subheader("Save and load settings")
    state = dict(
        inputs=ss.inputs,
        glaze_piece_df=ensure_cols(ss.glaze_piece_df, {"Material": "", "Cost_per_lb": 0.0, "Grams_per_piece": 0.0}).to_dict(orient="list"),
        catalog_df=ensure_cols(ss.catalog_df, {"Material": "", "Cost_per_lb": 0.0, "Cost_per_kg": 0.0}).to_dict(orient="list"),
        recipe_df=ensure_cols(ss.recipe_df, {"Material": "", "Percent": 0.0}).to_dict(orient="list"),
        recipe_grams_per_piece=ss.recipe_grams_per_piece,
        other_mat_df=ensure_cols(ss.other_mat_df, {"Item":"", "Unit":"", "Cost_per_unit":0.0, "Quantity_for_project":0.0}).to_dict(orient="list"),
        unified_forms=ensure_cols(ss.unified_forms, UNIFIED_FORM_SCHEMA).to_dict(orient="list"),
    )
    st.download_button("Download settings JSON", to_json_bytes(state), file_name="pottery_pricing_settings.json")
    
    up = st.file_uploader("Upload settings JSON", type=["json"])
    if up is not None:
        try:
            data = from_json_bytes(up.read())
            ss.inputs.update(data.get("inputs", {}))

            def dict_to_df(d, cols):
                if not isinstance(d, dict) or not d:
                    return pd.DataFrame(columns=cols)
                df = pd.DataFrame(d)
                for c in cols:
                    if c not in df.columns:
                        df[c] = []
                return df[cols]

            ss.glaze_piece_df = dict_to_df(data.get("glaze_piece_df", {}), ["Material", "Cost_per_lb", "Grams_per_piece"])
            ss.catalog_df = dict_to_df(data.get("catalog_df", {}), ["Material", "Cost_per_lb", "Cost_per_kg"])
            ss.recipe_df = dict_to_df(data.get("recipe_df", {}), ["Material", "Percent"])
            ss.other_mat_df = dict_to_df(data.get("other_mat_df", {}), ["Item","Unit","Cost_per_unit","Quantity_for_project"])
            
            # Handle unified forms
            if "unified_forms" in data:
                ss.unified_forms = dict_to_df(data["unified_forms"], list(UNIFIED_FORM_SCHEMA.keys()))
                ss.unified_forms = ensure_cols(ss.unified_forms, UNIFIED_FORM_SCHEMA)
            else:
                # Backward compatibility - migrate from old format if present
                if any(key in data for key in ["form_presets_df", "production_forms", "custom_forms"]):
                    # Temporarily load old data to session state for migration
                    old_presets = dict_to_df(data.get("form_presets_df", {}), ["Form", "Clay_lb_wet", "Default_glaze_g", "Notes"])
                    old_production = dict_to_df(data.get("production_forms", {}), ["Form", "Throwing_min", "Trimming_min", "Handling_min", "Glazing_min", "Pieces_per_shelf", "Notes"])
                    old_custom = dict_to_df(data.get("custom_forms", {}), ["Form", "Throwing_min", "Trimming_min", "Handling_min", "Glazing_min", "Pieces_per_shelf", "Notes"])
                    
                    # Store temporarily
                    ss.form_presets_df = old_presets
                    ss.production_forms = old_production  
                    ss.custom_forms = old_custom
                    
                    # Migrate to unified
                    ss.unified_forms = migrate_to_unified_forms()
                    st.info("✨ Migrated your old form data to new unified system!")
                else:
                    # No form data in file, keep current
                    pass
            
            ss.recipe_grams_per_piece = float(data.get("recipe_grams_per_piece", ss.recipe_grams_per_piece))
            st.success("✅ Settings loaded successfully!")
            
        except Exception as e:
            st.error(f"Could not load settings. {e}")

    # Show current unified forms status
    with st.expander("📊 Current unified forms database", expanded=False):
        st.caption(f"You have {len(ss.unified_forms)} forms in your unified database")
        if not ss.unified_forms.empty:
            # Show summary
            has_clay = (ss.unified_forms["Clay_lb_wet"] > 0).sum()
            has_glaze = (ss.unified_forms["Default_glaze_g"] > 0).sum()
            has_timing = (ss.unified_forms["Throwing_min"] > 0).sum()
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            summary_col1.metric("Forms with clay data", has_clay)
            summary_col2.metric("Forms with glaze data", has_glaze) 
            summary_col3.metric("Forms with timing data", has_timing)
            
            # Option to export unified forms separately
            unified_csv = ss.unified_forms.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📄 Export unified forms as CSV",
                unified_csv,
                file_name="unified_forms_export.csv",
                mime="text/csv"
            )
        
         

# ------------ Report ------------
with tabs[10]:
    ip = ss.inputs
    grams_pp = float(ss.get("recipe_grams_per_piece", 8.0))
    _, glaze_pp_from_recipe = glaze_per_piece_from_recipe(ss.catalog_df, ss.recipe_df, grams_pp)
    other_pp, _, _ = other_materials_pp(ss.other_mat_df, int(ss.inputs["units_made"]))
    totals = calc_totals(ip, glaze_pp_from_recipe, other_pp)

    st.subheader("Per piece totals")

    r1 = st.columns(3)
    r1[0].markdown("Clay " + money(totals["clay_pp"]))
    r1[1].markdown("Glaze " + money(totals["glaze_pp"]))
    r1[2].markdown("Packaging " + money(totals["pack_pp"]))

    r2 = st.columns(3)
    r2[0].markdown("Other materials " + money(totals["other_pp"]))
    r2[1].markdown("Energy " + money(totals["energy_pp"]))
    r2[2].markdown("Labor " + money(totals["labor_pp"]))

    st.markdown("Overhead " + money(totals["oh_pp"]))
    st.markdown("**Total cost** " + money(totals["total_pp"]))

    st.subheader("Prices")
    st.markdown("Wholesale " + money(totals["wholesale"]))
    st.markdown("Retail " + money(totals["retail"]))
    if totals["distributor"] is not None:
        st.markdown("Distributor " + money(totals["distributor"]))

    fuel = str(ip.get("fuel_gas", "None"))
    if fuel == "Propane":
        st.caption(f"Fuel: Propane at {money(ip.get('lp_price_per_gal',0.0))} per gallon")
    elif fuel == "Natural Gas":
        st.caption(f"Fuel: Natural Gas at {money(ip.get('ng_price_per_therm',0.0))} per therm")
    elif fuel == "Wood":
        st.caption(f"Fuel: Wood at {money(ip.get('wood_price_per_cord',0.0))} per cord "
                   f"and {money(ip.get('wood_price_per_facecord',0.0))} per face cord")
    else:
        st.caption("Fuel: None (only electric firing costs included)")

    st.caption("Glaze costs calculated from Catalog cost per lb/kg and recipe percents.")

# ------------ About ------------
with tabs[11]:
    
    st.subheader("About this app")
    st.markdown("""
# Pottery Cost Analysis App – User Guide

This app was created to help potters understand the true costs behind every piece of work and run profitable pottery businesses. Each section focuses on one part of the complete pottery workflow, from initial pricing to kiln planning to international shipping.

---

## 1. Quick Start
- **2-minute pricing**: Get wholesale and retail prices for any piece quickly
- **Form presets**: Choose from 100+ pottery forms with clay weights and glaze amounts
- **Smart defaults**: Sensible starting values for clay, energy, and labor costs
- **Confidence scoring**: Visual feedback on estimate reliability
- **Easy navigation**: Direct links to detailed tabs for customization

## 2. Per Unit
- **Unified form management**: One database for clay weights, glaze amounts, timing data, and kiln info
- **Form presets**: Choose from extensive library or create custom forms
- **Clay costing**: Bag prices, yield calculations, and shrink rate helpers
- **Advanced shrink tools**: Wet-to-fired calculations, lid remake helper with gallery height
- **Glaze integration**: Connect to recipe tab or manual glaze costing
- **Project materials**: Add one-time costs (handles, corks, special glazes)
- Shows **complete per-piece cost breakdown**

## 3. Glaze Recipe
- **Material catalog**: Searchable database of 50+ common ceramic materials
- **Recipe calculator**: Percentage-based glaze formulas with cost tracking
- **Batch scaling**: Convert between grams, ounces, and pounds
- **Per-piece costing**: Exact glaze cost for any quantity per piece
- **Cost analysis**: See material costs, batch totals, and per-gram pricing

## 4. Energy
- **Multiple fuel types**: Electric, propane, natural gas, and wood firing
- **Real usage data**: Based on actual potter energy consumption
- **Firing cost breakdown**: Bisque, glaze, and third firings
- **Kiln efficiency**: Calculate cost per piece for different firing methods
- **Fuel comparison**: Compare energy costs across different kiln types

## 5. Production Planning
- **Order timeline**: Realistic delivery estimates with hands-on time and kiln schedules
- **Form integration**: Uses unified form database with timing data
- **Kiln scheduling**: Accounts for drying, firing, and cooling times
- **Cost estimation**: Labor and material costs for complete orders
- **Direct integration**: "Use in cost calculator" button applies data to pricing tabs

## 6. Kiln Load Planner
- **Visual kiln loading**: Plan shelf-by-shelf with capacity tracking
- **Bisque vs glaze modes**: Different packing rules and guidance
- **Dynamic shelves**: Add/remove shelves for any kiln size (wood, electric, gas)
- **Cost optimization**: Real energy cost per piece for actual mixed loads
- **Efficiency feedback**: Visual utilization and packing optimization
- **Load summary**: Total pieces, energy costs, and firing time estimates

## 7. Labor & Overhead
- **Time tracking**: Hours per piece with realistic labor rates
- **Overhead allocation**: Monthly expenses divided by production volume
- **Cost per piece**: Accurate labor and overhead calculations

## 8. Pricing
- **Professional margins**: 2x2x2 rule or custom wholesale margins
- **Market pricing**: Wholesale, retail, and distributor price points
- **Profit analysis**: Clear cost vs. selling price breakdowns

## 9. Save & Load
- **Complete backup**: Download all settings, forms, and recipes as JSON
- **Easy restore**: Upload saved settings to restore your complete setup
- **Form management**: Export/import unified forms database as CSV
- **Backward compatibility**: Automatically migrates old saved files

## 10. Shipping & Tariffs
- **Domestic shipping**: U.S. zones, dimensional weight, insurance calculations
- **International selling**: Customs values, tariffs, VAT, and brokerage fees
- **Pottery-specific**: Fragile item considerations and real shipping costs
- **Landed cost**: Complete cost to deliver pottery internationally

## 11. Report
- **Quick summary**: All costs and pricing in one view
- **Cost breakdown**: Material, energy, labor, and overhead details
- **Pricing overview**: Wholesale, retail, and distributor prices
- **Export ready**: Complete cost analysis for record-keeping

---

## Key Features

**🔗 Unified Form System**: One database stores clay weights, glaze amounts, timing data, and kiln info. Enter once, use everywhere.

**⚡ Real-Time Integration**: Production Planning connects to Cost Calculator. Kiln Load Planner calculates actual energy costs.

**🌍 Complete Business Tool**: From raw clay costs to international shipping - everything needed to run a profitable pottery business.

**💾 Data Persistence**: Save and restore complete setups. Never lose your custom forms, recipes, or cost data.

**🎯 Potter-Focused**: Built by potters, for potters. Every feature addresses real studio workflows and business needs.

---

This app was created with gratitude for the pottery community, generosity in sharing knowledge, and empathy for the challenges of running a creative business. Your data stays private in your browser - nothing is sent anywhere else.

**Alford Wayman**  
Artist and Owner  
Creek Road Pottery LLC

---
    """)

    
