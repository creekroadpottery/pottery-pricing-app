
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pottery Pricing App", layout="wide")

st.title("Pottery Pricing App")
st.write("Per unit cost and price calculator for studio pottery.")

# Sidebar inputs
st.sidebar.header("Batch and units")
units_made = st.sidebar.number_input("Units made in the batch", min_value=1, value=1, step=1)

st.sidebar.header("Clay")
clay_price_per_bag = st.sidebar.number_input("Clay price per bag", min_value=0.0, value=25.0, step=0.5)
clay_bag_weight_lb = st.sidebar.number_input("Clay bag weight lb", min_value=0.1, value=25.0, step=0.1)
clay_weight_per_piece_lb = st.sidebar.number_input("Clay weight per piece lb wet", min_value=0.0, value=1.0, step=0.1)
clay_shrink_yield = st.sidebar.slider("Clay yield factor after trimming and loss", min_value=0.5, max_value=1.0, value=0.9, step=0.01)

st.sidebar.header("Glaze materials")
st.sidebar.caption("Enter glaze inputs per piece. Cost per kg and grams used per piece.")
glaze_df = st.data_editor(
    pd.DataFrame([
        {"Material": "Frit 3134", "Cost_per_kg": 4.5, "Grams_per_piece": 5.0},
        {"Material": "EPK Kaolin", "Cost_per_kg": 0.9, "Grams_per_piece": 3.0},
    ]),
    num_rows="dynamic",
    use_container_width=True,
    key="glaze_editor",
)

st.sidebar.header("Packaging")
packaging_per_piece = st.sidebar.number_input("Packaging cost per piece", min_value=0.0, value=0.5, step=0.1)

st.sidebar.header("Energy costs")
st.sidebar.subheader("Electric")
kwh_rate = st.sidebar.number_input("Rate per kWh", min_value=0.0, value=0.15, step=0.01)
kwh_bisque = st.sidebar.number_input("kWh used per bisque firing", min_value=0.0, value=30.0, step=1.0)
kwh_glaze = st.sidebar.number_input("kWh used per glaze firing", min_value=0.0, value=35.0, step=1.0)
pieces_per_electric_firing = st.sidebar.number_input("Pieces per electric firing", min_value=1, value=40, step=1)

st.sidebar.subheader("Gas")
gas_rate = st.sidebar.number_input("Rate per unit of gas", min_value=0.0, value=2.50, step=0.05)
gas_units_bisque = st.sidebar.number_input("Gas units per bisque", min_value=0.0, value=0.0, step=0.1)
gas_units_glaze = st.sidebar.number_input("Gas units per glaze", min_value=0.0, value=0.0, step=0.1)
pieces_per_gas_firing = st.sidebar.number_input("Pieces per gas firing", min_value=1, value=40, step=1)

st.sidebar.header("Labor and overhead")
labor_rate = st.sidebar.number_input("Labor rate per hour", min_value=0.0, value=25.0, step=1.0)
hours_per_piece = st.sidebar.number_input("Hours per piece", min_value=0.0, value=0.25, step=0.05)
overhead_per_month = st.sidebar.number_input("Overhead per month", min_value=0.0, value=500.0, step=10.0)
pieces_per_month = st.sidebar.number_input("Pieces per month", min_value=1, value=200, step=10)

st.sidebar.header("Pricing targets")
wholesale_margin_pct = st.sidebar.slider("Wholesale margin percent", min_value=0, max_value=80, value=50, step=1)
retail_multiplier = st.sidebar.number_input("Retail multiplier on wholesale", min_value=1.0, value=2.2, step=0.1)
use_2x2x2 = st.sidebar.checkbox("Use 2x2x2 preset", value=False, help="Sets wholesale = cost x 2, retail = wholesale x 2, show a distributor x 2 suggestion.")

# Calculations
# Clay per piece
clay_cost_per_lb = clay_price_per_bag / clay_bag_weight_lb if clay_bag_weight_lb else 0
clay_cost_per_piece = (clay_weight_per_piece_lb / clay_shrink_yield) * clay_cost_per_lb if clay_shrink_yield else 0

# Glaze per piece
if glaze_df is not None and len(glaze_df) > 0:
    glaze_df = glaze_df.fillna(0.0)
    glaze_df["Cost_per_gram"] = glaze_df["Cost_per_kg"] / 1000.0
    glaze_df["Cost_per_piece"] = glaze_df["Cost_per_gram"] * glaze_df["Grams_per_piece"]
    glaze_cost_per_piece = glaze_df["Cost_per_piece"].sum()
else:
    glaze_cost_per_piece = 0.0

# Energy
electric_cost_bisque = kwh_bisque * kwh_rate
electric_cost_glaze = kwh_glaze * kwh_rate
electric_per_piece = (electric_cost_bisque + electric_cost_glaze) / max(1, pieces_per_electric_firing)

gas_cost_bisque = gas_units_bisque * gas_rate
gas_cost_glaze = gas_units_glaze * gas_rate
gas_per_piece = (gas_cost_bisque + gas_cost_glaze) / max(1, pieces_per_gas_firing)

energy_per_piece = electric_per_piece + gas_per_piece

# Labor and overhead
labor_per_piece = labor_rate * hours_per_piece
overhead_per_piece = overhead_per_month / max(1, pieces_per_month)

# Total cost
material_per_piece = clay_cost_per_piece + glaze_cost_per_piece + packaging_per_piece
total_cost_per_piece = material_per_piece + energy_per_piece + labor_per_piece + overhead_per_piece

# Pricing logic
if use_2x2x2:
    wholesale_price = total_cost_per_piece * 2.0
    retail_price = wholesale_price * 2.0
    distributor_price = retail_price * 2.0
else:
    # Mirror the workbook style: wholesale from margin, retail from wholesale * multiplier
    margin = wholesale_margin_pct / 100.0
    wholesale_price = total_cost_per_piece / max(1e-9, 1.0 - margin) if margin < 1 else float("inf")
    retail_price = wholesale_price * retail_multiplier
    distributor_price = None

# Output columns
c1, c2 = st.columns(2, gap="large")

with c1:
    st.subheader("Per piece breakdown")
    st.metric("Clay", f"${clay_cost_per_piece:,.2f}")
    st.metric("Glaze", f"${glaze_cost_per_piece:,.2f}")
    st.metric("Packaging", f"${packaging_per_piece:,.2f}")
    st.metric("Energy", f"${energy_per_piece:,.2f}")
    st.metric("Labor", f"${labor_per_piece:,.2f}")
    st.metric("Overhead", f"${overhead_per_piece:,.2f}")
    st.metric("Total cost", f"${total_cost_per_piece:,.2f}")

with c2:
    st.subheader("Target prices")
    if use_2x2x2:
        st.metric("Wholesale", f"${wholesale_price:,.2f}")
        st.metric("Retail", f"${retail_price:,.2f}")
        st.metric("Distributor", f"${distributor_price:,.2f}")
        st.caption("2x2x2 preset. Adjust inputs to see effects.")
    else:
        st.metric("Wholesale (from margin)", f"${wholesale_price:,.2f}")
        st.metric("Retail (multiplier)", f"${retail_price:,.2f}")
        st.caption("Wholesale is cost divided by 1 minus margin. Retail equals wholesale times multiplier.")

# Glaze table echo
with st.expander("Glaze detail"):
    st.dataframe(glaze_df, use_container_width=True)

# Report table
report = pd.DataFrame([{
    "Units_made": units_made,
    "Clay_per_piece": round(clay_cost_per_piece, 4),
    "Glaze_per_piece": round(glaze_cost_per_piece, 4),
    "Packaging_per_piece": round(packaging_per_piece, 4),
    "Energy_per_piece": round(energy_per_piece, 4),
    "Labor_per_piece": round(labor_per_piece, 4),
    "Overhead_per_piece": round(overhead_per_piece, 4),
    "Total_cost_per_piece": round(total_cost_per_piece, 4),
    "Wholesale_price": round(wholesale_price, 4),
    "Retail_price": round(retail_price, 4),
}] )

st.download_button("Download report CSV", report.to_csv(index=False).encode("utf-8"), "pottery_pricing_report.csv", "text/csv")

st.caption("This app is an open calculator. Copy and share freely.")
