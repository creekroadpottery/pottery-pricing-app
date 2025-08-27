import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Pottery Cost Analysis App", layout="wide")

def df_safe(df, cols):
    if df is None:
        return pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df[cols].fillna(0.0)

def money(n):
    try:
        return f"${n:,.2f}"
    except Exception:
        return "$0.00"

def to_json_bytes(obj):
    return json.dumps(obj, indent=2).encode("utf-8")

def from_json_bytes(b):
    return json.loads(b.decode("utf-8"))

ss = st.session_state

if "inputs" not in ss:
    ss.inputs = dict(
        units_made=1,
        clay_price_per_bag=25.0,
        clay_bag_weight_lb=25.0,
        clay_weight_per_piece_lb=1.0,
        clay_yield=0.9,
        packaging_per_piece=0.5,
        # energy
        kwh_rate=0.15, kwh_bisque=30.0, kwh_glaze=35.0, pieces_per_electric_firing=40,
        gas_rate=2.50, gas_units_bisque=0.0, gas_units_glaze=0.0, pieces_per_gas_firing=40,
        # labor and overhead
        labor_rate=25.0, hours_per_piece=0.25,
        overhead_per_month=500.0, pieces_per_month=200,
        # pricing
        use_2x2x2=False, wholesale_margin_pct=50, retail_multiplier=2.2,
        # glaze by piece
        grams_glaze_per_piece=8.0
    )

if "glaze_piece_df" not in ss:
    ss.glaze_piece_df = pd.DataFrame([
        {"Material":"Frit 3134","Cost_per_kg":4.50,"Grams_per_piece":5.0},
        {"Material":"EPK Kaolin","Cost_per_kg":1.20,"Grams_per_piece":3.0},
    ])

if "catalog_df" not in ss:
    ss.catalog_df = pd.DataFrame([
        {"Material": "Custer Feldspar", "Cost_per_lb": 1.72},
        {"Material": "Silica 325m",     "Cost_per_lb": 0.82},
        {"Material": "EPK Kaolin",      "Cost_per_lb": 0.54},
        {"Material": "Frit 3134",       "Cost_per_lb": 2.04},
    ])

if "recipe_df" not in ss:
    ss.recipe_df = pd.DataFrame([
        {"Material":"Custer Feldspar","Percent":40.0},
        {"Material":"Silica 325m","Percent":20.0},
        {"Material":"EPK Kaolin","Percent":20.0},
        {"Material":"Frit 3134","Percent":20.0},
    ])

if "recipe_grams_per_piece" not in ss:
    ss.recipe_grams_per_piece = 8.0
# shared math
def glaze_cost_from_piece_table(df):
    gdf = df_safe(df, ["Material","Cost_per_kg","Grams_per_piece"]).copy()
    gdf["Cost_per_g"] = gdf["Cost_per_kg"] / 1000.0
    gdf["Cost_per_piece"] = gdf["Cost_per_g"] * gdf["Grams_per_piece"]
    return float(gdf["Cost_per_piece"].sum()), gdf

def percent_recipe_table(catalog_df, recipe_df, batch_g):
    price_map = {str(r["Material"]).strip().lower(): float(r["Cost_per_kg"])/1000.0
                 for _, r in df_safe(catalog_df, ["Material","Cost_per_kg"]).iterrows()}
    rdf = df_safe(recipe_df, ["Material","Percent"]).copy()
    tot = float(rdf["Percent"].sum()) or 100.0
    rows = []
    for _, r in rdf.iterrows():
        name = str(r["Material"]).strip()
        pct = float(r["Percent"])
        grams = batch_g * pct / tot
        cost = grams * price_map.get(name.lower(), 0.0)
        rows.append({
            "Material":name, "Percent":pct, "Grams":round(grams,2),
            "Ounces":round(grams/28.3495,2), "Pounds":round(grams/453.592,3),
            "Cost":cost
        })
    out = pd.DataFrame(rows)
    batch_total = float(out["Cost"].sum()) if not out.empty else 0.0
    cost_per_g = batch_total / batch_g if batch_g else 0.0
    cost_per_oz = cost_per_g * 28.3495
    cost_per_lb = cost_per_g * 453.592
    return out, batch_total, cost_per_g, cost_per_oz, cost_per_lb

def calc_energy(ip):
    e_cost = (ip["kwh_bisque"]+ip["kwh_glaze"]) * ip["kwh_rate"]
    e_pp = e_cost / max(1, int(ip["pieces_per_electric_firing"]))
    g_cost = (ip["gas_units_bisque"]+ip["gas_units_glaze"]) * ip["gas_rate"]
    g_pp = g_cost / max(1, int(ip["pieces_per_gas_firing"]))
    return e_pp + g_pp

def calc_totals(ip, glaze_per_piece_cost):
    clay_cost_per_lb = ip["clay_price_per_bag"] / ip["clay_bag_weight_lb"] if ip["clay_bag_weight_lb"] else 0.0
    clay_pp = (ip["clay_weight_per_piece_lb"] / max(ip["clay_yield"], 1e-9)) * clay_cost_per_lb
    energy_pp = calc_energy(ip)
    labor_pp = ip["labor_rate"] * ip["hours_per_piece"]
    overhead_pp = ip["overhead_per_month"] / max(1, int(ip["pieces_per_month"]))
    material_pp = clay_pp + glaze_per_piece_cost + ip["packaging_per_piece"]
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
        energy_pp=energy_pp, labor_pp=labor_pp, oh_pp=overhead_pp,
        total_pp=total_pp, wholesale=wholesale, retail=retail, distributor=distributor
    )
st.title("Pottery Cost Analysis App")

tabs = st.tabs(["Per unit","Glaze recipe","Energy","Labor and overhead","Pricing","Compare","Save and load","Report","About"])

# Per Unit
with tabs[0]:
    ip = ss.inputs
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Clay and packaging")
        ip["units_made"] = st.number_input("Units in this batch", min_value=1, value=int(ip["units_made"]), step=1)
        ip["clay_price_per_bag"] = st.number_input("Clay price per bag", min_value=0.0, value=float(ip["clay_price_per_bag"]), step=0.5)
        ip["clay_bag_weight_lb"] = st.number_input("Clay bag weight lb", min_value=0.1, value=float(ip["clay_bag_weight_lb"]), step=0.1)
        ip["clay_weight_per_piece_lb"] = st.number_input("Clay weight per piece lb wet", min_value=0.0, value=float(ip["clay_weight_per_piece_lb"]), step=0.1)
        ip["clay_yield"] = st.slider("Clay yield after trimming and loss", min_value=0.5, max_value=1.0, value=float(ip["clay_yield"]), step=0.01)
        ip["packaging_per_piece"] = st.number_input("Packaging per piece", min_value=0.0, value=float(ip["packaging_per_piece"]), step=0.1)

        st.subheader("Glaze per piece table")
        ss.glaze_piece_df = st.data_editor(
            df_safe(ss.glaze_piece_df, ["Material","Cost_per_kg","Grams_per_piece"]),
            num_rows="dynamic",
            use_container_width=True,
            key="glaze_piece_editor",
        )
    with c2:
        st.subheader("Glaze cost from this table")
        glaze_pp_cost, gdetail = glaze_cost_from_piece_table(ss.glaze_piece_df)
        st.metric("Glaze cost per piece", money(glaze_pp_cost))
        st.dataframe(gdetail, use_container_width=True)

        st.subheader("Per piece totals")
        totals = calc_totals(ip, glaze_pp_cost)
        c = st.columns(3)
        c[0].metric("Clay", money(totals["clay_pp"]))
        c[1].metric("Glaze", money(totals["glaze_pp"]))
        c[2].metric("Packaging", money(totals["pack_pp"]))
        c = st.columns(3)
        c[0].metric("Energy", money(totals["energy_pp"]))
        c[1].metric("Labor", money(totals["labor_pp"]))
        c[2].metric("Overhead", money(totals["oh_pp"]))
        st.metric("Total cost per piece", money(totals["total_pp"]))

# Glaze Recipe
with tabs[1]:
    st.subheader("Catalog (Cost per lb)")
    ss.catalog_df = st.data_editor(
        df_safe(ss.catalog_df, ["Material","Cost_per_lb"]),
        num_rows="dynamic", use_container_width=True, key="catalog_editor"
    )

    st.subheader("Recipe in percent")
    ss.recipe_df = st.data_editor(
        df_safe(ss.recipe_df, ["Material","Percent"]),
        num_rows="dynamic", use_container_width=True, key="recipe_editor"
    )

    colA, colB = st.columns([2,1])
    with colA:
        batch_str = st.text_input("Batch size", value="100")
    with colB:
        unit = st.selectbox("Units", ["g","oz","lb"], index=0)

    def _to_float(s):
        try:
            return float(str(s).strip())
        except Exception:
            return 0.0

    batch_val = _to_float(batch_str)
    if unit == "g":
        batch_g = batch_val
    elif unit == "oz":
        batch_g = batch_val * 28.3495
    else:
        batch_g = batch_val * 453.592

    if batch_g <= 0:
        st.warning("Enter a positive batch size")

    # price map now uses cost per lb → convert to per gram
    price_map = {
        str(r["Material"]).strip().lower(): float(r["Cost_per_lb"]) / 453.592
        for _, r in df_safe(ss.catalog_df, ["Material","Cost_per_lb"]).iterrows()
    }

    total_percent = float(ss.recipe_df["Percent"].sum() if "Percent" in ss.recipe_df else 0.0) or 100.0

    rows = []
    for _, r in ss.recipe_df.iterrows():
        name = str(r.get("Material", "")).strip()
        pct = float(r.get("Percent", 0.0))
        grams = batch_g * pct / total_percent
        ppg = price_map.get(name.lower(), 0.0)  # cost per gram
        cost = grams * ppg
        rows.append({
            "Material": name,
            "Percent": round(pct, 2),
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

    st.caption(f"Batch size {batch_g:.0f} g  •  {batch_g/28.3495:.2f} oz  •  {batch_g/453.592:.3f} lb")

    show = out.copy()
    show["Cost"] = show["Cost"].map(money)
    st.dataframe(show, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Batch total", money(batch_total))
    col2.metric("Cost per gram", money(cost_per_g))
    col3.metric("Cost per ounce", money(cost_per_oz))

    col4, col5 = st.columns(2)
    col4.metric("Cost per pound", money(cost_per_lb))
    grams_str = st.text_input("Grams used per piece", value=str(ss.recipe_grams_per_piece))

    try:
        ss.recipe_grams_per_piece = float(grams_str)
    except ValueError:
        ss.recipe_grams_per_piece = 0.0
        st.warning("Please enter a number")

    st.metric("Glaze cost per piece from this recipe", money(cost_per_g * ss.recipe_grams_per_piece))


try:
    ss.recipe_grams_per_piece = float(grams_str)
except ValueError:
    ss.recipe_grams_per_piece = 0.0
    st.warning("Please enter a number")
st.metric("Glaze cost per piece from this recipe", money(cost_per_g * ss.recipe_grams_per_piece))

# Energy
with tabs[2]:
    ip = ss.inputs
    st.subheader("Electric")
    ip["kwh_rate"] = st.number_input("Rate per kWh", min_value=0.0, value=float(ip["kwh_rate"]), step=0.01)
    ip["kwh_bisque"] = st.number_input("kWh per bisque", min_value=0.0, value=float(ip["kwh_bisque"]), step=1.0)
    ip["kwh_glaze"] = st.number_input("kWh per glaze", min_value=0.0, value=float(ip["kwh_glaze"]), step=1.0)
    ip["pieces_per_electric_firing"] = st.number_input("Pieces per electric firing", min_value=1, value=int(ip["pieces_per_electric_firing"]), step=1)

    st.subheader("Gas")
    ip["gas_rate"] = st.number_input("Gas rate per unit", min_value=0.0, value=float(ip["gas_rate"]), step=0.05)
    ip["gas_units_bisque"] = st.number_input("Gas units per bisque", min_value=0.0, value=float(ip["gas_units_bisque"]), step=0.1)
    ip["gas_units_glaze"] = st.number_input("Gas units per glaze", min_value=0.0, value=float(ip["gas_units_glaze"]), step=0.1)
    ip["pieces_per_gas_firing"] = st.number_input("Pieces per gas firing", min_value=1, value=int(ip["pieces_per_gas_firing"]), step=1)

    st.subheader("Per piece energy now")
    st.metric("Energy per piece", money(calc_energy(ip)))

# Labor and Overhead
with tabs[3]:
    ip = ss.inputs
    st.subheader("Labor")
    ip["labor_rate"] = st.number_input("Labor rate per hour", min_value=0.0, value=float(ip["labor_rate"]), step=1.0)
    ip["hours_per_piece"] = st.number_input("Hours per piece", min_value=0.0, value=float(ip["hours_per_piece"]), step=0.05)

    st.subheader("Overhead")
    ip["overhead_per_month"] = st.number_input("Overhead per month", min_value=0.0, value=float(ip["overhead_per_month"]), step=10.0)
    ip["pieces_per_month"] = st.number_input("Pieces per month", min_value=1, value=int(ip["pieces_per_month"]), step=10)

# Pricing
with tabs[4]:
    ip = ss.inputs
    st.subheader("Method")
    ip["use_2x2x2"] = st.checkbox("Use 2 by 2 by 2", value=bool(ip["use_2x2x2"]))
    if not ip["use_2x2x2"]:
        ip["wholesale_margin_pct"] = st.slider("Wholesale margin percent", min_value=0, max_value=80, value=int(ip["wholesale_margin_pct"]), step=1)
        ip["retail_multiplier"] = st.number_input("Retail multiplier on wholesale", min_value=1.0, value=float(ip["retail_multiplier"]), step=0.1)

    st.subheader("Pick glaze source")
    mode = st.radio("Choose glaze cost input", ["Per piece table","Percent recipe"], horizontal=True)
    if mode == "Per piece table":
        glaze_pp_cost, _ = glaze_cost_from_piece_table(ss.glaze_piece_df)
    else:
        # reuse last recipe batch cost per gram by simulating a 100 g batch if needed
        out, batch_total, cpg, _, _ = percent_recipe_table(ss.catalog_df, ss.recipe_df, 100.0)
        glaze_pp_cost = cpg * ss.recipe_grams_per_piece

    totals = calc_totals(ip, glaze_pp_cost)
    st.subheader("Results")
    c = st.columns(3)
    c[0].metric("Wholesale", money(totals["wholesale"]))
    c[1].metric("Retail", money(totals["retail"]))
    if totals["distributor"] is not None:
        c[2].metric("Distributor", money(totals["distributor"]))
    st.metric("Total cost per piece", money(totals["total_pp"]))

# Compare
with tabs[5]:
    st.subheader("Compare to your spreadsheet")
    app_total = calc_totals(ss.inputs, glaze_cost_from_piece_table(ss.glaze_piece_df)[0])["total_pp"]
    expected = st.number_input("Enter total cost per piece from Excel", min_value=0.0, value=float(app_total), step=0.01)
    diff = app_total - expected
    st.write(f"App total {money(app_total)}")
    st.write(f"Excel total {money(expected)}")
    st.write(f"Difference {money(diff)}")
# Save and Load
with tabs[6]:
    st.subheader("Save and load settings")
    state = dict(
        inputs=ss.inputs,
        glaze_piece_df=df_safe(ss.glaze_piece_df, ["Material","Cost_per_kg","Grams_per_piece"]).to_dict(orient="list"),
        catalog_df=df_safe(ss.catalog_df, ["Material","Cost_per_kg"]).to_dict(orient="list"),
        recipe_df=df_safe(ss.recipe_df, ["Material","Percent"]).to_dict(orient="list"),
        recipe_grams_per_piece=ss.recipe_grams_per_piece
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
            ss.glaze_piece_df = dict_to_df(data.get("glaze_piece_df", {}), ["Material","Cost_per_kg","Grams_per_piece"])
            ss.catalog_df = dict_to_df(data.get("catalog_df", {}), ["Material","Cost_per_kg"])
            ss.recipe_df = dict_to_df(data.get("recipe_df", {}), ["Material","Percent"])
            ss.recipe_grams_per_piece = float(data.get("recipe_grams_per_piece", ss.recipe_grams_per_piece))
            st.success("Loaded")
        except Exception as e:
            st.error(f"Could not load. {e}")

# Report
with tabs[7]:
    ip = ss.inputs
    glaze_pp_cost, _ = glaze_cost_from_piece_table(ss.glaze_piece_df)
    totals = calc_totals(ip, glaze_pp_cost)
    st.subheader("Per piece totals")
    r = st.columns(3)
    r[0].markdown("Clay " + money(totals["clay_pp"]))
    r[1].markdown("Glaze " + money(totals["glaze_pp"]))
    r[2].markdown("Packaging " + money(totals["pack_pp"]))
    r = st.columns(3)
    r[0].markdown("Energy " + money(totals["energy_pp"]))
    r[1].markdown("Labor " + money(totals["labor_pp"]))
    r[2].markdown("Overhead " + money(totals["oh_pp"]))
    st.markdown("**Total cost** " + money(totals["total_pp"]))
    st.subheader("Prices")
    st.markdown("Wholesale " + money(totals["wholesale"]))
    st.markdown("Retail " + money(totals["retail"]))

# About
with tabs[8]:
    st.subheader("About this app")
    st.markdown("""
This tool mirrors a simple pottery cost sheet.
Use it free and share it.
Built by Creek Road Pottery.

Privacy
Your numbers stay in your browser while the app runs.
When you save settings the app downloads a JSON file to your computer.
""")

