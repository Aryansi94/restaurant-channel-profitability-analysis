
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================================================
# RESTAURANT CHANNEL PROFITABILITY DASHBOARD
# =========================================================

st.set_page_config(
    page_title="Restaurant Profitability Dashboard",
    page_icon="🍽️",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "SkyCity Auckland Restaurants & Bars.csv"
OUTPUT_DIR = BASE_DIR / "project_outputs"

CHANNELS = {
    "In-store": {
        "orders": "InStoreOrders",
        "revenue": "InStoreRevenue",
        "profit": "InStoreNetProfit"
    },
    "Uber Eats": {
        "orders": "UberEatsOrders",
        "revenue": "UberEatsRevenue",
        "profit": "UberEatsNetProfit"
    },
    "DoorDash": {
        "orders": "DoorDashOrders",
        "revenue": "DoorDashRevenue",
        "profit": "DoorDashNetProfit"
    },
    "Self-delivery": {
        "orders": "SelfDeliveryOrders",
        "revenue": "SelfDeliveryRevenue",
        "profit": "SelfDeliveryNetProfit"
    }
}


@st.cache_data
def load_data():
    data = pd.read_csv(DATA_FILE)

    data["TotalRevenue"] = data[
        [
            "InStoreRevenue",
            "UberEatsRevenue",
            "DoorDashRevenue",
            "SelfDeliveryRevenue"
        ]
    ].sum(axis=1)

    data["TotalRecordedNetProfit"] = data[
        [
            "InStoreNetProfit",
            "UberEatsNetProfit",
            "DoorDashNetProfit",
            "SelfDeliveryNetProfit"
        ]
    ].sum(axis=1)

    data["OverallProfitMarginPct"] = np.where(
        data["TotalRevenue"] != 0,
        data["TotalRecordedNetProfit"]
        / data["TotalRevenue"] * 100,
        np.nan
    )

    data["AggregatorRevenue"] = (
        data["UberEatsRevenue"] + data["DoorDashRevenue"]
    )

    data["AggregatorProfit"] = (
        data["UberEatsNetProfit"] + data["DoorDashNetProfit"]
    )

    data["AggregatorProfitMarginPct"] = np.where(
        data["AggregatorRevenue"] != 0,
        data["AggregatorProfit"] / data["AggregatorRevenue"] * 100,
        np.nan
    )

    return data


def make_channel_summary(data):
    rows = []

    for channel, cols in CHANNELS.items():
        orders = data[cols["orders"]].sum()
        revenue = data[cols["revenue"]].sum()
        profit = data[cols["profit"]].sum()

        rows.append({
            "Channel": channel,
            "Orders": orders,
            "Revenue": revenue,
            "Recorded Net Profit": profit,
            "Profit Margin (%)": (
                profit / revenue * 100 if revenue else np.nan
            ),
            "Profit per Order": (
                profit / orders if orders else np.nan
            )
        })

    return pd.DataFrame(rows)


def money(value):
    return f"{value:,.2f}"


# =========================================================
# HEADER
# =========================================================

st.title("🍽️ Restaurant Channel Profitability Dashboard")

st.markdown(
    "Explore restaurant revenue, recorded net profit, channel margins, "
    "restaurant segments, cuisines, and individual restaurant performance."
)

if not DATA_FILE.exists():
    st.error(
        "Dataset not found. Place 'SkyCity Auckland Restaurants & Bars.csv' "
        "in the same folder as app.py."
    )
    st.stop()

df = load_data()

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Dashboard Filters")

segments = sorted(df["Segment"].dropna().unique())
cuisines = sorted(df["CuisineType"].dropna().unique())
subregions = sorted(df["Subregion"].dropna().unique())

selected_segments = st.sidebar.multiselect(
    "Restaurant segment",
    options=segments,
    default=segments
)

selected_cuisines = st.sidebar.multiselect(
    "Cuisine type",
    options=cuisines,
    default=cuisines
)

selected_subregions = st.sidebar.multiselect(
    "Subregion",
    options=subregions,
    default=subregions
)

filtered = df[
    df["Segment"].isin(selected_segments)
    & df["CuisineType"].isin(selected_cuisines)
    & df["Subregion"].isin(selected_subregions)
].copy()

if filtered.empty:
    st.warning("No restaurants match the selected filters.")
    st.stop()

# =========================================================
# KPI CARDS
# =========================================================

total_restaurants = filtered["RestaurantID"].nunique()
total_orders = filtered["MonthlyOrders"].sum()
total_revenue = filtered["TotalRevenue"].sum()
total_profit = filtered["TotalRecordedNetProfit"].sum()

overall_margin = (
    total_profit / total_revenue * 100 if total_revenue else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Restaurants", f"{total_restaurants:,}")
k2.metric("Monthly Orders", f"{total_orders:,}")
k3.metric("Total Revenue", money(total_revenue))
k4.metric("Recorded Net Profit", money(total_profit))
k5.metric("Overall Profit Margin", f"{overall_margin:.2f}%")

st.caption(
    "Financial amounts are shown in the dataset's currency units; "
    "the source file does not specify a currency."
)

st.divider()

# =========================================================
# CHANNEL PERFORMANCE
# =========================================================

st.header("1. Channel Performance")

channel_summary = make_channel_summary(filtered)

left, right = st.columns(2)

with left:
    fig_revenue = px.bar(
        channel_summary,
        x="Channel",
        y="Revenue",
        title="Revenue by Ordering Channel",
        text_auto=".3s"
    )
    fig_revenue.update_layout(
        xaxis_title="Channel",
        yaxis_title="Revenue"
    )
    st.plotly_chart(fig_revenue, use_container_width=True)

with right:
    fig_margin = px.bar(
        channel_summary,
        x="Channel",
        y="Profit Margin (%)",
        title="Recorded Profit Margin by Channel",
        text_auto=".2f"
    )
    fig_margin.add_hline(y=0, line_dash="dash")
    fig_margin.update_layout(
        xaxis_title="Channel",
        yaxis_title="Profit Margin (%)"
    )
    st.plotly_chart(fig_margin, use_container_width=True)

st.subheader("Channel Summary")

st.dataframe(
    channel_summary.style.format({
        "Orders": "{:,.0f}",
        "Revenue": "{:,.2f}",
        "Recorded Net Profit": "{:,.2f}",
        "Profit Margin (%)": "{:.2f}%",
        "Profit per Order": "{:.2f}"
    }),
    use_container_width=True,
    hide_index=True
)

# =========================================================
# SEGMENT ANALYSIS
# =========================================================

st.header("2. Restaurant Segment Analysis")

segment_rows = []

for channel, cols in CHANNELS.items():
    grouped = filtered.groupby("Segment").agg(
        Restaurants=("RestaurantID", "nunique"),
        Orders=(cols["orders"], "sum"),
        Revenue=(cols["revenue"], "sum"),
        Profit=(cols["profit"], "sum")
    ).reset_index()

    grouped["Channel"] = channel
    grouped["Profit Margin (%)"] = np.where(
        grouped["Revenue"] != 0,
        grouped["Profit"] / grouped["Revenue"] * 100,
        np.nan
    )

    segment_rows.append(grouped)

segment_summary = pd.concat(segment_rows, ignore_index=True)

segment_pivot = segment_summary.pivot(
    index="Segment",
    columns="Channel",
    values="Profit Margin (%)"
)

fig_segment = px.imshow(
    segment_pivot,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale="RdYlGn",
    color_continuous_midpoint=0,
    labels={
        "x": "Ordering Channel",
        "y": "Restaurant Segment",
        "color": "Margin (%)"
    },
    title="Recorded Profit Margin by Segment and Channel"
)

st.plotly_chart(fig_segment, use_container_width=True)

st.dataframe(
    segment_summary.style.format({
        "Restaurants": "{:,.0f}",
        "Orders": "{:,.0f}",
        "Revenue": "{:,.2f}",
        "Profit": "{:,.2f}",
        "Profit Margin (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# =========================================================
# CUISINE ANALYSIS
# =========================================================

st.header("3. Cuisine Analysis")

cuisine_summary = filtered.groupby("CuisineType").agg(
    Restaurants=("RestaurantID", "nunique"),
    Orders=("MonthlyOrders", "sum"),
    Revenue=("TotalRevenue", "sum"),
    Profit=("TotalRecordedNetProfit", "sum")
).reset_index()

cuisine_summary["Profit Margin (%)"] = np.where(
    cuisine_summary["Revenue"] != 0,
    cuisine_summary["Profit"] / cuisine_summary["Revenue"] * 100,
    np.nan
)

cuisine_summary = cuisine_summary.sort_values(
    "Profit", ascending=False
)

left, right = st.columns(2)

with left:
    fig_cuisine_profit = px.bar(
        cuisine_summary,
        x="CuisineType",
        y="Profit",
        title="Recorded Net Profit by Cuisine",
        text_auto=".3s"
    )
    fig_cuisine_profit.update_layout(
        xaxis_title="Cuisine",
        yaxis_title="Recorded Net Profit",
        xaxis_tickangle=-35
    )
    st.plotly_chart(fig_cuisine_profit, use_container_width=True)

with right:
    fig_cuisine_margin = px.bar(
        cuisine_summary,
        x="CuisineType",
        y="Profit Margin (%)",
        title="Profit Margin by Cuisine",
        text_auto=".2f"
    )
    fig_cuisine_margin.update_layout(
        xaxis_title="Cuisine",
        yaxis_title="Profit Margin (%)",
        xaxis_tickangle=-35
    )
    st.plotly_chart(fig_cuisine_margin, use_container_width=True)

# =========================================================
# RESTAURANT EXPLORER
# =========================================================

st.header("4. Restaurant Explorer")

search = st.text_input(
    "Search by restaurant name or restaurant ID"
)

restaurant_view = filtered.copy()

if search.strip():
    match_name = restaurant_view["RestaurantName"].astype(str).str.contains(
        search.strip(), case=False, na=False
    )

    match_id = restaurant_view["RestaurantID"].astype(str).str.contains(
        search.strip(), case=False, na=False
    )

    restaurant_view = restaurant_view[match_name | match_id]

sort_choice = st.selectbox(
    "Rank restaurants by",
    [
        "TotalRecordedNetProfit",
        "TotalRevenue",
        "OverallProfitMarginPct",
        "AggregatorProfit"
    ],
    format_func=lambda x: {
        "TotalRecordedNetProfit": "Total recorded net profit",
        "TotalRevenue": "Total revenue",
        "OverallProfitMarginPct": "Overall profit margin",
        "AggregatorProfit": "Combined aggregator profit"
    }[x]
)

sort_ascending = st.checkbox(
    "Show lowest values first",
    value=False
)

restaurant_view = restaurant_view.sort_values(
    sort_choice,
    ascending=sort_ascending
)

restaurant_columns = [
    "RestaurantID",
    "RestaurantName",
    "CuisineType",
    "Segment",
    "Subregion",
    "MonthlyOrders",
    "TotalRevenue",
    "TotalRecordedNetProfit",
    "OverallProfitMarginPct",
    "AggregatorProfit",
    "AggregatorProfitMarginPct"
]

st.dataframe(
    restaurant_view[restaurant_columns].style.format({
        "MonthlyOrders": "{:,.0f}",
        "TotalRevenue": "{:,.2f}",
        "TotalRecordedNetProfit": "{:,.2f}",
        "OverallProfitMarginPct": "{:.2f}%",
        "AggregatorProfit": "{:,.2f}",
        "AggregatorProfitMarginPct": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# =========================================================
# LOSS-MAKING AGGREGATOR ANALYSIS
# =========================================================

st.header("5. Aggregator Risk Analysis")

loss_making = filtered[
    filtered["AggregatorProfit"] < 0
].sort_values("AggregatorProfit")

high_revenue_low_margin = filtered[
    (filtered["TotalRevenue"] >= filtered["TotalRevenue"].quantile(0.75))
    & (filtered["OverallProfitMarginPct"] < 5)
].sort_values("OverallProfitMarginPct")

a, b = st.columns(2)

with a:
    st.metric(
        "Restaurants with negative aggregator profit",
        f"{len(loss_making):,}"
    )

    st.dataframe(
        loss_making[
            [
                "RestaurantID",
                "RestaurantName",
                "Segment",
                "AggregatorRevenue",
                "AggregatorProfit",
                "AggregatorProfitMarginPct"
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True
    )

with b:
    st.metric(
        "High-revenue restaurants with margin below 5%",
        f"{len(high_revenue_low_margin):,}"
    )

    st.dataframe(
        high_revenue_low_margin[
            [
                "RestaurantID",
                "RestaurantName",
                "Segment",
                "TotalRevenue",
                "TotalRecordedNetProfit",
                "OverallProfitMarginPct"
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# COST STRUCTURE
# =========================================================

st.header("6. Estimated Cost Structure")

cost_rows = []

for channel, cols in CHANNELS.items():
    revenue = filtered[cols["revenue"]].sum()
    cogs = (filtered[cols["revenue"]] * filtered["COGSRate"]).sum()
    opex = (filtered[cols["revenue"]] * filtered["OPEXRate"]).sum()

    commission = 0.0
    delivery_cost = 0.0

    if channel in ["Uber Eats", "DoorDash"]:
        commission = (
            filtered[cols["revenue"]] * filtered["CommissionRate"]
        ).sum()

    if channel == "Self-delivery":
        delivery_cost = filtered["SD_DeliveryTotalCost"].sum()

    cost_rows.append({
        "Channel": channel,
        "Revenue": revenue,
        "Estimated COGS": cogs,
        "Estimated OPEX": opex,
        "Estimated Commission": commission,
        "Delivery Cost": delivery_cost
    })

cost_summary = pd.DataFrame(cost_rows)

cost_summary["Estimated Total Costs"] = (
    cost_summary["Estimated COGS"]
    + cost_summary["Estimated OPEX"]
    + cost_summary["Estimated Commission"]
    + cost_summary["Delivery Cost"]
)

fig_cost = px.bar(
    cost_summary,
    x="Channel",
    y=[
        "Estimated COGS",
        "Estimated OPEX",
        "Estimated Commission",
        "Delivery Cost"
    ],
    title="Estimated Cost Components by Channel",
    barmode="stack"
)

st.plotly_chart(fig_cost, use_container_width=True)

st.dataframe(
    cost_summary.style.format({
        col: "{:,.2f}"
        for col in cost_summary.columns
        if col != "Channel"
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Cost components are estimates derived from the supplied rates and "
    "delivery-cost field. They are not independently verified invoices."
)

# =========================================================
# DOWNLOADS
# =========================================================

st.header("7. Download Analysis Results")

download_items = {
    "Channel profitability": channel_summary,
    "Segment profitability": segment_summary,
    "Cuisine profitability": cuisine_summary,
    "Restaurant profitability": restaurant_view[restaurant_columns],
    "Cost structure": cost_summary,
    "Loss-making aggregator restaurants": loss_making
}

for label, data in download_items.items():
    st.download_button(
        label=f"Download {label} CSV",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=label.lower().replace(" ", "_") + ".csv",
        mime="text/csv",
        key=label
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Restaurant Channel Profitability Analysis | "
    "Figures use the dataset's recorded profit fields. "
    "Currency is unspecified in the source data."
)
