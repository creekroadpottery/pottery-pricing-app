

import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Pottery Cost Analysis App", layout="wide")
ss = st.session_state

# ------------ Helpers ------------
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
            {"Form": "Mug (12 oz)",              "Clay_lb_wet": 0.90, "Default_glaze_g": 40,  "Notes": "straight"},
            {"Form": "Mug (14 oz)",              "Clay_lb_wet": 1.00, "Default_glaze_g": 45,  "Notes": ""},
            {"Form": "Creamer (small)",          "Clay_lb_wet": 0.75, "Default_glaze_g": 30,  "Notes": ""},
            {"Form": "Pitcher (medium)",         "Clay_lb_wet": 2.50, "Default_glaze_g": 85,  "Notes": ""},
            {"Form": "Bowl (cereal)",            "Clay_lb_wet": 1.25, "Default_glaze_g": 55,  "Notes": "≈6\""},
            {"Form": "Bowl (small)",             "Clay_lb_wet": 1.00, "Default_glaze_g": 45,  "Notes": ""},
            {"Form": "Bowl (medium)",            "Clay_lb_wet": 2.00, "Default_glaze_g": 80,  "Notes": ""},
            {"Form": "Bowl (large)",             "Clay_lb_wet": 4.50, "Default_glaze_g": 140, "Notes": ""},
            {"Form": "Plate (10 in dinner)",     "Clay_lb_wet": 2.50, "Default_glaze_g": 110, "Notes": ""},
            {"Form": "Pie plate",                "Clay_lb_wet": 3.25, "Default_glaze_g": 120, "Notes": "3¼–3½ lb"},
            {"Form": "Sugar jar",                "Clay_lb_wet": 1.00, "Default_glaze_g": 35,  "Notes": ""},
            {"Form": "Honey jar",                "Clay_lb_wet": 1.25, "Default_glaze_g": 45,  "Notes": ""},
            {"Form": "Crock (small)",            "Clay_lb_wet": 1.75, "Default_glaze_g": 60,  "Notes": ""},
            {"Form": "Crock (medium)",           "Clay_lb_wet": 3.00, "Default_glaze_g": 95,  "Notes": ""},
            {"Form": "Crock (large)",            "Clay_lb_wet": 4.00, "Default_glaze_g": 130, "Notes": ""},
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
        kwh_rate=0.15, kwh_bisque=30.0, kwh_glaze=35.0, kwh_third=0.0, pieces_per_electric_firing=40,
        labor_rate=25.0, hours_per_piece=0.25,
        overhead_per_month=500.0, pieces_per_month=200,
        use_2x2x2=False, wholesale_margin_pct=50, retail_multiplier=2.2,
        # fuel defaults
        fuel_gas="None",
        lp_price_per_gal=3.50, lp_gal_bisque=0.0, lp_gal_glaze=0.0, pieces_per_gas_firing=40,
        ng_price_per_therm=1.20, ng_therms_bisque=0.0, ng_therms_glaze=0.0,
        # wood firing
        wood_price_per_cord=300.0, wood_price_per_facecord=120.0,
        wood_cords_bisque=0.0, wood_cords_glaze=0.0, wood_cords_third=0.0,
        wood_facecords_bisque=0.0, wood_facecords_glaze=0.0, wood_facecords_third=0.0,
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
        {"Item":"Hand pump","Unit":"each","Cost_per_unit":0.85,"Quantity_for_project":16.0},
    ])

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

tabs = st.tabs([
    "Per unit", "Glaze recipe", "Energy", "Labor and overhead",
    "Pricing", "Save and load", "Report", "About"
])

# ------------- Per unit -------------
with tabs[0]:
    ip = ss.inputs
    left, right = st.columns(2)

    # ---------------- LEFT ----------------
    with left:
        # --- Form preset picker (with options) ---
        st.subheader("Form preset")
        preset_df = ensure_cols(
            ss.get("form_presets_df", pd.DataFrame()),
            {"Form": "", "Clay_lb_wet": 0.0, "Default_glaze_g": 0.0, "Notes": ""}
        )
        forms = list(preset_df["Form"]) if not preset_df.empty else []
        choice = st.selectbox("Choose a form", ["None"] + forms, index=0, key="form_choice")

        if choice != "None" and not preset_df.empty:
            row = preset_df.loc[preset_df["Form"] == choice].iloc[0]
            preset_clay_lb = float(row.get("Clay_lb_wet", 0.0))
            preset_glaze_g = float(row.get("Default_glaze_g", 0.0))
            note = str(row.get("Notes", "")).strip()

            c1, c2, c3 = st.columns([1, 1, 2])
            c1.metric("Preset clay", f"{preset_clay_lb:.2f} lb")
            c2.metric("Preset glaze", f"{preset_glaze_g:.0f} g")
            if note:
                c3.caption(note)

        # --- Clay and packaging ---
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
            "Clay weight per piece lb wet", min_value=0.0, value=float(ip["clay_weight_per_piece_lb"]), step=0.1
        )
        ip["clay_yield"] = st.slider(
            "Clay yield after trimming and loss",
            min_value=0.5, max_value=1.0,
            value=float(ip.get("clay_yield", 0.9)), step=0.01,
            help="Fraction of the starting ball that ends up in the piece after trimming and losses."
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

            st.caption("Reverse check if you already threw a lid")
            lid_wet_id = st.number_input(
                f"Wet gallery inner diameter you threw ({u})",
                min_value=0.0,
                value=float(ss.get("lid_wet_id", wet_gallery_needed)),
                step=0.001,
                key="lid_wet_id",
            )
            expected_fired_id = lid_wet_id * (1.0 - rate)
            st.write(f"Expected fired gallery inner diameter: **{expected_fired_id:.3f} {u}**")

        # --- Glaze source ---
        st.subheader("Glaze source")
        glaze_source = st.radio(
            "Glaze cost comes from", ["Recipe tab", "Manual table"], index=0, horizontal=True
        )

        if glaze_source == "Manual table":
            st.caption("Edit names, cost per lb, and grams per piece.")
            ss.glaze_piece_df = st.data_editor(
                ensure_cols(ss.glaze_piece_df, {"Material": "", "Cost_per_lb": 0.0, "Grams_per_piece": 0.0}),
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
        show_df = source_df.copy()
        if "Cost_per_piece" in show_df.columns:
            show_df["Cost_per_piece"] = show_df["Cost_per_piece"].map(money)
        st.dataframe(show_df, use_container_width=True)

    # ---------------- RIGHT ----------------
    with right:
        # Other project materials editor
        st.subheader("Other project materials")
        st.caption("Add one-time items for this batch. The cost is divided by the number of pieces in this batch.")

        pieces = max(1, int(ip["units_made"]))
        base = ensure_cols(
            ss.get("other_mat_df", pd.DataFrame()),
            {"Item":"", "Unit":"", "Cost_per_unit":0.0, "Quantity_for_project":0.0}
        ).copy()
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
with tabs[1]:
    st.subheader("Catalog (choose cost unit)")
    if "catalog_unit" not in ss:
        ss.catalog_unit = "lb"
    ss.catalog_unit = st.radio("Catalog cost unit", ["lb", "kg"], horizontal=True, index=0 if ss.catalog_unit=="lb" else 1)

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

    st.subheader("Recipe in percent")
    ss.recipe_df = st.data_editor(
        ensure_cols(ss.recipe_df, {"Material": "", "Percent": 0.0}),
        column_config={
            "Material": st.column_config.TextColumn("Material"),
            "Percent": st.column_config.NumberColumn("Percent", min_value=0.0, step=0.1),
        },
        num_rows="dynamic", use_container_width=True, key="recipe_editor"
    )

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

    out, batch_total, cpg, cpo, cpl = percent_recipe_table(ss.catalog_df, ss.recipe_df, batch_g)

    st.caption(f"Batch size {batch_g:.0f} g  •  {batch_g/28.3495:.2f} oz  •  {batch_g/453.592:.3f} lb")
    show = out.copy()
    show["Cost"] = show["Cost"].map(money)
    st.dataframe(show, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Batch total", money(batch_total))
    col2.metric("Cost per gram", money(cpg))
    col3.metric("Cost per ounce", money(cpo))
    st.metric("Cost per pound", money(cpl))

    grams_str = st.text_input("Grams used per piece", value=str(ss.get("recipe_grams_per_piece", 8.0)))
    try:
        ss.recipe_grams_per_piece = float(grams_str)
    except ValueError:
        st.warning("Please enter a number")

    st.metric("Glaze cost per piece from this recipe", money(cpg * ss.recipe_grams_per_piece))

# ------------ Energy ------------
with tabs[2]:
    ip = ss.inputs
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Electric")
        ip["kwh_rate"] = st.number_input("Rate per kWh", min_value=0.0, value=float(ip.get("kwh_rate", 0.0)), step=0.01)
        ip["kwh_bisque"] = st.number_input("kWh per bisque", min_value=0.0, value=float(ip.get("kwh_bisque", 0.0)), step=1.0)
        ip["kwh_glaze"]  = st.number_input("kWh per glaze",  min_value=0.0, value=float(ip.get("kwh_glaze", 0.0)),  step=1.0)
        ip["kwh_third"]  = st.number_input("kWh per third firing", min_value=0.0, value=float(ip.get("kwh_third", 0.0)), step=1.0)
        ip["pieces_per_electric_firing"] = st.number_input("Pieces per electric firing", min_value=1, value=int(ip.get("pieces_per_electric_firing", 40)), step=1)

    with col2:
        st.subheader("Fuel")
        ip["fuel_gas"] = st.selectbox("Fuel source", ["None", "Propane", "Natural Gas", "Wood"],
                                      index=["None","Propane","Natural Gas","Wood"].index(str(ip.get("fuel_gas","None"))))

        if ip["fuel_gas"] == "Propane":
            ip["lp_price_per_gal"] = st.number_input("Propane price per gallon", min_value=0.0, value=float(ip.get("lp_price_per_gal", 3.50)), step=0.05)
            ip["lp_gal_bisque"] = st.number_input("Gallons per bisque firing", min_value=0.0, value=float(ip.get("lp_gal_bisque", 0.0)), step=0.1)
            ip["lp_gal_glaze"]  = st.number_input("Gallons per glaze firing",  min_value=0.0, value=float(ip.get("lp_gal_glaze", 0.0)),  step=0.1)
            ip["pieces_per_gas_firing"] = st.number_input("Pieces per gas firing", min_value=1, value=int(ip.get("pieces_per_gas_firing", 40)), step=1)

        elif ip["fuel_gas"] == "Natural Gas":
            ip["ng_price_per_therm"] = st.number_input("Natural gas price per therm", min_value=0.0, value=float(ip.get("ng_price_per_therm", 1.20)), step=0.05)
            ip["ng_therms_bisque"] = st.number_input("Therms per bisque firing", min_value=0.0, value=float(ip.get("ng_therms_bisque", 0.0)), step=0.1)
            ip["ng_therms_glaze"]  = st.number_input("Therms per glaze firing",  min_value=0.0, value=float(ip.get("ng_therms_glaze", 0.0)),  step=0.1)
            ip["pieces_per_gas_firing"] = st.number_input("Pieces per gas firing", min_value=1, value=int(ip.get("pieces_per_gas_firing", 40)), step=1)

        elif ip["fuel_gas"] == "Wood":
            ip["wood_price_per_cord"] = st.number_input("Wood price per cord", min_value=0.0, value=float(ip.get("wood_price_per_cord", 300.0)), step=1.0)
            ip["wood_price_per_facecord"] = st.number_input("Wood price per face cord", min_value=0.0, value=float(ip.get("wood_price_per_facecord", 120.0)), step=1.0)
            st.caption("Enter wood used per firing. You can mix cords and face cords. Face cord is typically one third of a full cord.")
            cA, cB = st.columns(2)
            with cA:
                ip["wood_cords_bisque"] = st.number_input("Cords per bisque", min_value=0.0, value=float(ip.get("wood_cords_bisque", 0.0)), step=0.05)
                ip["wood_cords_glaze"]  = st.number_input("Cords per glaze",  min_value=0.0, value=float(ip.get("wood_cords_glaze", 0.0)),  step=0.05)
                ip["wood_cords_third"]  = st.number_input("Cords per third firing", min_value=0.0, value=float(ip.get("wood_cords_third", 0.0)), step=0.05)
            with cB:
                ip["wood_facecords_bisque"] = st.number_input("Face cords per bisque", min_value=0.0, value=float(ip.get("wood_facecords_bisque", 0.0)), step=0.1)
                ip["wood_facecords_glaze"]  = st.number_input("Face cords per glaze",  min_value=0.0, value=float(ip.get("wood_facecords_glaze", 0.0)),  step=0.1)
                ip["wood_facecords_third"]  = st.number_input("Face cords per third", min_value=0.0, value=float(ip.get("wood_facecords_third", 0.0)), step=0.1)
            ip["pieces_per_wood_firing"] = st.number_input("Pieces per wood firing", min_value=1, value=int(ip.get("pieces_per_wood_firing", 40)), step=1)
        else:
            st.caption("No fuel costs included.")

    st.subheader("Per piece energy now")
    st.metric("Energy per piece", money(calc_energy(ip)))

# ------------ Labor and overhead ------------
with tabs[3]:
    ip = ss.inputs
    st.subheader("Labor")
    ip["labor_rate"] = st.number_input("Labor rate per hour", min_value=0.0, value=float(ip["labor_rate"]), step=1.0)
    ip["hours_per_piece"] = st.number_input("Hours per piece", min_value=0.0, value=float(ip["hours_per_piece"]), step=0.05)

    st.subheader("Overhead")
    ip["overhead_per_month"] = st.number_input("Overhead per month", min_value=0.0, value=float(ip["overhead_per_month"]), step=10.0)
    ip["pieces_per_month"] = st.number_input("Pieces per month", min_value=1, value=int(ip["pieces_per_month"]), step=10)
# ------------ Pricing ------------
with tabs[4]:
    ip = ss.inputs

    st.subheader("Pricing options")
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

# ------------ Save and load ------------
with tabs[5]:
    st.subheader("Save and load settings")
    state = dict(
        inputs=ss.inputs,
        glaze_piece_df=ensure_cols(ss.glaze_piece_df, {"Material": "", "Cost_per_lb": 0.0, "Grams_per_piece": 0.0}).to_dict(orient="list"),
        catalog_df=ensure_cols(ss.catalog_df, {"Material": "", "Cost_per_lb": 0.0, "Cost_per_kg": 0.0}).to_dict(orient="list"),
        recipe_df=ensure_cols(ss.recipe_df, {"Material": "", "Percent": 0.0}).to_dict(orient="list"),
        recipe_grams_per_piece=ss.recipe_grams_per_piece,
        other_mat_df=ensure_cols(ss.other_mat_df, {"Item":"", "Unit":"", "Cost_per_unit":0.0, "Quantity_for_project":0.0}).to_dict(orient="list"),
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
            ss.recipe_grams_per_piece = float(data.get("recipe_grams_per_piece", ss.recipe_grams_per_piece))
            st.success("Loaded")
        except Exception as e:
            st.error(f"Could not load. {e}")

# ------------ Report ------------
with tabs[6]:
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
with tabs[7]:
    st.subheader("About this app")
    st.markdown("""
This app was created to help potters understand the true cost of their work.
It began as a simple spreadsheet and grew into something I wanted to share.

The project is guided by gratitude, generosity, and empathy.
Gratitude for the teachers, friends, and makers who showed me the way.
Generosity in making the tool free for anyone who might find it useful.
Empathy for the many potters balancing time, resources, and creativity.

Your numbers stay private while the app runs in your browser.
When you save settings, a small JSON file is downloaded to your computer.
No data is sent anywhere else.

Alford Wayman
Artist and owner
Creek Road Pottery LLC
""")
