import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Pottery Cost Analysis App", layout="wide")

# Helpers
def df_safe(df, cols):
    if df is None:
        return pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df[cols].fillna(0.0)

def to_json_bytes(obj):
    return json.dumps(obj, indent=2).encode("utf-8")

def from_json_bytes(b):
    return json.loads(b.decode("utf-8"))

def money(n):
    try:
        return f"${n:,.2f}"
    except Exception:
        return "$0.00"

# Session defaults
ss = st.session_state

if "inputs" not in ss:
    ss.inputs = dict(
        units_made=1,
        clay_price_per_bag=25.0,
        clay_bag_weight_lb=25.0,
        clay_weight_per_piece_lb=1.0,
        clay_shrink_yield=0.9,
        packaging_per_piece=0.5,
        kwh_rate=0.15,
        kwh_bisque=30.0,
        kwh_glaze=35.0,
        pieces_per_electric_firing=40,
        gas_rate=2.50,
        gas_units_bisque=0.0,
        gas_units_glaze=0.0,
        pieces_per_gas_firing=40,
        labor_rate=25.0,
        hours_per_piece=0.25,
        overhead_per_month=500.0,
        pieces_per_month=200,
        wholesale_margin_pct=50,
        retail_multiplier=2.2,
        use_2x2x2=False,
    )

if "glaze_table_piece" not in ss:
    ss.glaze_table_piece = pd.DataFrame([
        {"Material": "Frit 3134", "Cost_per_kg": 4.5, "Grams_per_piece": 5.0},
        {"Material": "EPK Kaolin", "Cost_per_kg": 0.9, "Grams_per_piece": 3.0},
    ])

if "materials_catalog" not in ss:
    ss.materials_catalog = pd.DataFrame([
        {"Material": "Sample", "Cost_per_kg": 0.00},
        {"Material": "Sample", "Cost_per_kg": 0.00},
        {"Material": "Sample", "Cost_per_kg": 0.00},
        {"Material": "Sample", "Cost_per_kg": 0.00},
    ])

if "recipe_percent" not in ss:
    ss.recipe_percent = pd.DataFrame([
        {"Material": "", "Percent": 00.0},
        {"Material": "", "Percent": 00.0},
        {"Material": "", "Percent": 00.0},
        {"Material": "", "Percent": 00.0},
    ])

if "recipe_batch_g" not in ss:
    ss.recipe_batch_g = 100.0

if "recipe_grams_per_piece" not in ss:
    ss.recipe_grams_per_piece = 8.0
# Core calc
def calc_piece(ip, glaze_df):
    clay_cost_per_lb = ip["clay_price_per_bag"] / ip["clay_bag_weight_lb"] if ip["clay_bag_weight_lb"] else 0.0
    clay_cost_per_piece = (ip["clay_weight_per_piece_lb"] / ip["clay_shrink_yield"]) * clay_cost_per_lb if ip["clay_shrink_yield"] else 0.0

    gdf = df_safe(glaze_df, ["Material", "Cost_per_kg", "Grams_per_piece"]).copy()
    gdf["Cost_per_gram"] = gdf["Cost_per_kg"] / 1000.0
    gdf["Cost_per_piece"] = gdf["Cost_per_gram"] * gdf["Grams_per_piece"]
    glaze_cost_per_piece = float(gdf["Cost_per_piece"].sum())

    electric_cost_bisque = ip["kwh_bisque"] * ip["kwh_rate"]
    electric_cost_glaze = ip["kwh_glaze"] * ip["kwh_rate"]
    electric_per_piece = (electric_cost_bisque + electric_cost_glaze) / max(1, ip["pieces_per_electric_firing"])

    gas_cost_bisque = ip["gas_units_bisque"] * ip["gas_rate"]
    gas_cost_glaze = ip["gas_units_glaze"] * ip["gas_rate"]
    gas_per_piece = (gas_cost_bisque + gas_cost_glaze) / max(1, ip["pieces_per_gas_firing"])
    energy_per_piece = electric_per_piece + gas_per_piece

    labor_per_piece = ip["labor_rate"] * ip["hours_per_piece"]
    overhead_per_piece = ip["overhead_per_month"] / max(1, ip["pieces_per_month"])

    material_per_piece = clay_cost_per_piece + glaze_cost_per_piece + ip["packaging_per_piece"]
    total_cost_per_piece = material_per_piece + energy_per_piece + labor_per_piece + overhead_per_piece

    if ip["use_2x2x2"]:
        wholesale_price = total_cost_per_piece * 2.0
        retail_price = wholesale_price * 2.0
        distributor_price = retail_price * 2.0
    else:
        margin = ip["wholesale_margin_pct"] / 100.0
        wholesale_price = total_cost_per_piece / max(1e-9, 1.0 - margin) if margin < 1 else float("inf")
        retail_price = wholesale_price * ip["retail_multiplier"]
        distributor_price = None

    return dict(
        clay_cost_per_piece=clay_cost_per_piece,
        glaze_cost_per_piece=glaze_cost_per_piece,
        packaging_per_piece=ip["packaging_per_piece"],
        energy_per_piece=energy_per_piece,
        labor_per_piece=labor_per_piece,
        overhead_per_piece=overhead_per_piece,
        total_cost_per_piece=total_cost_per_piece,
        wholesale_price=wholesale_price,
        retail_price=retail_price,
        distributor_price=distributor_price,
        glaze_detail=gdf,
    )

# UI header and tabs
st.title("Pottery Cost Analysis App v0.5")
tabs = st.tabs(["Calculator", "Glaze by percent", "Save and load", "Report", "About"])

# Calculator tab
with tabs[0]:
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.subheader("Inputs")
        ip = ss.inputs

        ip["units_made"] = st.number_input("Units made in the batch", min_value=1, value=int(ip["units_made"]), step=1)

        st.markdown("Clay")
        ip["clay_price_per_bag"] = st.number_input("Clay price per bag", min_value=0.0, value=float(ip["clay_price_per_bag"]), step=0.5)
        ip["clay_bag_weight_lb"] = st.number_input("Clay bag weight lb", min_value=0.1, value=float(ip["clay_bag_weight_lb"]), step=0.1)
        ip["clay_weight_per_piece_lb"] = st.number_input("Clay weight per piece lb wet", min_value=0.0, value=float(ip["clay_weight_per_piece_lb"]), step=0.1)
        ip["clay_shrink_yield"] = st.slider("Clay yield factor after trimming and loss", min_value=0.5, max_value=1.0, value=float(ip["clay_shrink_yield"]), step=0.01)

        st.markdown("Glaze materials per piece")
        ss.glaze_table_piece = st.data_editor(
            df_safe(ss.glaze_table_piece, ["Material", "Cost_per_kg", "Grams_per_piece"]),
            num_rows="dynamic",
            use_container_width=True,
            key="glaze_editor_piece",
        )

        st.markdown("Packaging")
        ip["packaging_per_piece"] = st.number_input("Packaging cost per piece", min_value=0.0, value=float(ip["packaging_per_piece"]), step=0.1)

        st.markdown("Energy costs")
        st.caption("Enter values for electric and gas. Set units per firing to zero if not used.")
        ip["kwh_rate"] = st.number_input("Rate per kWh", min_value=0.0, value=float(ip["kwh_rate"]), step=0.01)
        ip["kwh_bisque"] = st.number_input("kWh used per bisque firing", min_value=0.0, value=float(ip["kwh_bisque"]), step=1.0)
        ip["kwh_glaze"] = st.number_input("kWh used per glaze firing", min_value=0.0, value=float(ip["kwh_glaze"]), step=1.0)
        ip["pieces_per_electric_firing"] = st.number_input("Pieces per electric firing", min_value=1, value=int(ip["pieces_per_electric_firing"]), step=1)

        ip["gas_rate"] = st.number_input("Gas rate per unit", min_value=0.0, value=float(ip["gas_rate"]), step=0.05)
        ip["gas_units_bisque"] = st.number_input("Gas units per bisque", min_value=0.0, value=float(ip["gas_units_bisque"]), step=0.1)
        ip["gas_units_glaze"] = st.number_input("Gas units per glaze", min_value=0.0, value=float(ip["gas_units_glaze"]), step=0.1)
        ip["pieces_per_gas_firing"] = st.number_input("Pieces per gas firing", min_value=1, value=int(ip["pieces_per_gas_firing"]), step=1)

        st.markdown("Labor and overhead")
        ip["labor_rate"] = st.number_input("Labor rate per hour", min_value=0.0, value=float(ip["labor_rate"]), step=1.0)
        ip["hours_per_piece"] = st.number_input("Hours per piece", min_value=0.0, value=float(ip["hours_per_piece"]), step=0.05)
        ip["overhead_per_month"] = st.number_input("Overhead per month", min_value=0.0, value=float(ip["overhead_per_month"]), step=10.0)
        ip["pieces_per_month"] = st.number_input("Pieces per month", min_value=1, value=int(ip["pieces_per_month"]), step=10)

        st.markdown("Pricing targets")
        ip["wholesale_margin_pct"] = st.slider("Wholesale margin percent", min_value=0, max_value=80, value=int(ip["wholesale_margin_pct"]), step=1)
        ip["retail_multiplier"] = st.number_input("Retail multiplier on wholesale", min_value=1.0, value=float(ip["retail_multiplier"]), step=0.1)
        ip["use_2x2x2"] = st.checkbox("Use 2 by 2 by 2 preset", value=bool(ip["use_2x2x2"]))

    res = calc_piece(ip, ss.glaze_table_piece)

    with right:
        st.subheader("Breakdown")
        c1, c2, c3 = st.columns(3)
        c1.metric("Clay", money(res["clay_cost_per_piece"]))
        c2.metric("Glaze", money(res["glaze_cost_per_piece"]))
        c3.metric("Packaging", money(res["packaging_per_piece"]))
        c1.metric("Energy", money(res["energy_per_piece"]))
        c2.metric("Labor", money(res["labor_per_piece"]))
        c3.metric("Overhead", money(res["overhead_per_piece"]))
        st.metric("Total cost", money(res["total_cost_per_piece"]))

        st.subheader("Prices")
        if ip["use_2x2x2"]:
            st.metric("Wholesale", money(res["wholesale_price"]))
            st.metric("Retail", money(res["retail_price"]))
            st.metric("Distributor", money(res["distributor_price"]))
        else:
            st.metric("Wholesale from margin", money(res["wholesale_price"]))
            st.metric("Retail from multiplier", money(res["retail_price"]))

        with st.expander("Glaze detail"):
            st.dataframe(res["glaze_detail"], use_container_width=True)
# Glaze by percent tab
with tabs[1]:
    st.subheader("Glaze cost from percent recipe")
    st.caption("Enter material costs per kilo. Enter a recipe in percents and a batch size in grams.")

    ss.materials_catalog = st.data_editor(
        df_safe(ss.materials_catalog, ["Material", "Cost_per_kg"]),
        num_rows="dynamic",
        use_container_width=True,
        key="materials_catalog_editor",
    )

    ss.recipe_percent = st.data_editor(
        df_safe(ss.recipe_percent, ["Material", "Percent"]),
        num_rows="dynamic",
        use_container_width=True,
        key="recipe_percent_editor",
    )

    colA, colB = st.columns(2)
    with colA:
        ss.recipe_batch_g = st.number_input("Batch size in grams", min_value=1.0, value=float(ss.recipe_batch_g), step=10.0)
    with colB:
        ss.recipe_grams_per_piece = st.number_input("Grams used per piece", min_value=0.0, value=float(ss.recipe_grams_per_piece), step=0.5)

    price_map = {str(r["Material"]).strip().lower(): float(r["Cost_per_kg"]) / 1000.0 for _, r in ss.materials_catalog.iterrows()}
    total_percent = float(ss.recipe_percent["Percent"].sum() if "Percent" in ss.recipe_percent else 0.0) or 100.0

    rows = []
    for _, r in ss.recipe_percent.iterrows():
        name = str(r.get("Material", "")).strip()
        pct = float(r.get("Percent", 0.0))
        grams = ss.recipe_batch_g * pct / total_percent
        ppg = price_map.get(name.lower(), 0.0)
        cost = grams * ppg
        rows.append({"Material": name, "Percent": pct, "Grams": round(grams, 2), "Cost": cost})

    out_df = pd.DataFrame(rows)
    batch_total = float(out_df["Cost"].sum()) if not out_df.empty else 0.0
    cost_per_gram = batch_total / ss.recipe_batch_g if ss.recipe_batch_g else 0.0
    cost_per_piece = cost_per_gram * ss.recipe_grams_per_piece

    show_df = out_df.copy()
    show_df["Cost"] = show_df["Cost"].map(money)
    st.dataframe(show_df, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Batch total", money(batch_total))
    c2.metric("Cost per gram", money(cost_per_gram))
    c3.metric("Cost per piece", money(cost_per_piece))

# Save and load tab
with tabs[2]:
    st.subheader("Save and load settings")
    st.caption("Download a JSON of your inputs. Upload it later to restore.")

    current_state = dict(
        inputs=ss.inputs,
        glaze_table_piece=df_safe(ss.glaze_table_piece, ["Material", "Cost_per_kg", "Grams_per_piece"]).to_dict(orient="list"),
        materials_catalog=df_safe(ss.materials_catalog, ["Material", "Cost_per_kg"]).to_dict(orient="list"),
        recipe_percent=df_safe(ss.recipe_percent, ["Material", "Percent"]).to_dict(orient="list"),
        recipe_batch_g=ss.recipe_batch_g,
        recipe_grams_per_piece=ss.recipe_grams_per_piece,
    )

    st.download_button("Download settings JSON", to_json_bytes(current_state), file_name="pottery_pricing_settings.json")

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

            ss.glaze_table_piece = dict_to_df(data.get("glaze_table_piece", {}), ["Material", "Cost_per_kg", "Grams_per_piece"])
            ss.materials_catalog = dict_to_df(data.get("materials_catalog", {}), ["Material", "Cost_per_kg"])
            ss.recipe_percent = dict_to_df(data.get("recipe_percent", {}), ["Material", "Percent"])
            ss.recipe_batch_g = float(data.get("recipe_batch_g", ss.recipe_batch_g))
            ss.recipe_grams_per_piece = float(data.get("recipe_grams_per_piece", ss.recipe_grams_per_piece))
            st.success("Settings loaded. Switch tabs to see them applied.")
        except Exception as e:
            st.error(f"Could not load. {e}")
# Report tab
with tabs[3]:
    st.subheader("Print friendly report")
    st.caption("Use your browser print command to save as PDF.")

    try:
        res_full = calc_piece(ss.inputs, ss.glaze_table_piece)
    except Exception:
        res_full = {}

    st.markdown("### Per piece totals")
    cols = st.columns(3)
    cols[0].markdown("Clay " + money(res_full.get("clay_cost_per_piece", 0)))
    cols[1].markdown("Glaze " + money(res_full.get("glaze_cost_per_piece", 0)))
    cols[2].markdown("Packaging " + money(res_full.get("packaging_per_piece", 0)))
    cols = st.columns(3)
    cols[0].markdown("Energy " + money(res_full.get("energy_per_piece", 0)))
    cols[1].markdown("Labor " + money(res_full.get("labor_per_piece", 0)))
    cols[2].markdown("Overhead " + money(res_full.get("overhead_per_piece", 0)))
    st.markdown("**Total cost** " + money(res_full.get("total_cost_per_piece", 0)))

    st.markdown("### Prices")
    if ss.inputs.get("use_2x2x2"):
        st.markdown("Wholesale " + money(res_full.get("wholesale_price", 0)))
        st.markdown("Retail " + money(res_full.get("retail_price", 0)))
    else:
        st.markdown("Wholesale from margin " + money(res_full.get("wholesale_price", 0)))
        st.markdown("Retail from multiplier " + money(res_full.get("retail_price", 0)))

    st.markdown("### Glaze detail")
    if "glaze_detail" in res_full:
        gdf = res_full["glaze_detail"].copy()
        gdf["Cost_per_piece"] = gdf["Cost_per_piece"].map(lambda x: f"{x:.4f}")
        st.dataframe(gdf, use_container_width=True)

# About tab
with tabs[4]:
    st.subheader("About")
    st.write("Created by Alford Wayman of Creek Road Pottery LLC, 917 Creek Road, Laceyville, PA, 18623. A gift to makers, offered in the spirit of generosity, gratitude, and empathy. Open cost analysis calculator for studio potters. Share and copy freely.")
