
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# =========================================================
# RESTAURANT CHANNEL PROFITABILITY ANALYSIS
# CONSOLIDATED PROJECT ANALYSIS
# =========================================================

OUTPUT = Path("project_outputs")
OUTPUT.mkdir(exist_ok=True)

df = pd.read_csv("SkyCity Auckland Restaurants & Bars.csv")

sns.set_theme(style="whitegrid")

channels = {
    "In-store": ("InStoreOrders", "InStoreRevenue", "InStoreNetProfit"),
    "Uber Eats": ("UberEatsOrders", "UberEatsRevenue", "UberEatsNetProfit"),
    "DoorDash": ("DoorDashOrders", "DoorDashRevenue", "DoorDashNetProfit"),
    "Self-delivery": (
        "SelfDeliveryOrders",
        "SelfDeliveryRevenue",
        "SelfDeliveryNetProfit"
    )
}

print("=" * 65)
print("RESTAURANT PROFITABILITY PROJECT")
print("=" * 65)

# ---------------------------------------------------------
# 1. DATA QUALITY
# ---------------------------------------------------------

quality = pd.DataFrame({
    "Check": [
        "Total rows",
        "Total columns",
        "Missing values",
        "Duplicate complete rows",
        "Duplicate RestaurantIDs"
    ],
    "Result": [
        len(df),
        len(df.columns),
        int(df.isna().sum().sum()),
        int(df.duplicated().sum()),
        int(df["RestaurantID"].duplicated().sum())
    ]
})

print("\nDATA QUALITY")
print(quality.to_string(index=False))
quality.to_csv(OUTPUT / "data_quality_report.csv", index=False)

# ---------------------------------------------------------
# 2. VALIDATE ORDER TOTALS AND REVENUE
# ---------------------------------------------------------

order_cols = [
    "InStoreOrders",
    "UberEatsOrders",
    "DoorDashOrders",
    "SelfDeliveryOrders"
]

df["CalculatedTotalOrders"] = df[order_cols].sum(axis=1)
df["OrderDifference"] = df["MonthlyOrders"] - df["CalculatedTotalOrders"]

revenue_checks = []

for channel, (orders_col, revenue_col, profit_col) in channels.items():
    calculated_revenue = df[orders_col] * df["AOV"]
    difference = (df[revenue_col] - calculated_revenue).abs()

    revenue_checks.append({
        "Channel": channel,
        "MaximumRevenueDifference": difference.max(),
        "RowsWithOrderMismatch": int((df["OrderDifference"] != 0).sum())
    })

revenue_validation = pd.DataFrame(revenue_checks)
revenue_validation.to_csv(
    OUTPUT / "revenue_validation.csv", index=False
)

print("\nREVENUE VALIDATION")
print(revenue_validation.round(6).to_string(index=False))

# ---------------------------------------------------------
# 3. CHANNEL-WISE PROFITABILITY
# ---------------------------------------------------------

channel_results = []

for channel, (orders_col, revenue_col, profit_col) in channels.items():
    orders = df[orders_col].sum()
    revenue = df[revenue_col].sum()
    profit = df[profit_col].sum()

    channel_results.append({
        "Channel": channel,
        "TotalOrders": orders,
        "TotalRevenue": revenue,
        "RecordedNetProfit": profit,
        "ProfitMarginPct": profit / revenue * 100 if revenue else np.nan,
        "ProfitPerOrder": profit / orders if orders else np.nan
    })

channel_summary = pd.DataFrame(channel_results)
channel_summary.to_csv(
    OUTPUT / "channel_profitability.csv", index=False
)

print("\nCHANNEL PROFITABILITY")
print(channel_summary.round(2).to_string(index=False))

# ---------------------------------------------------------
# 4. ESTIMATED COST STRUCTURE
# ---------------------------------------------------------

cost_rows = []

for channel, (_, revenue_col, _) in channels.items():
    revenue = df[revenue_col].sum()
    cogs = (df[revenue_col] * df["COGSRate"]).sum()
    opex = (df[revenue_col] * df["OPEXRate"]).sum()

    commission = 0.0
    delivery_cost = 0.0

    if channel in ["Uber Eats", "DoorDash"]:
        commission = (
            df[revenue_col] * df["CommissionRate"]
        ).sum()

    if channel == "Self-delivery":
        delivery_cost = df["SD_DeliveryTotalCost"].sum()

    estimated_costs = cogs + opex + commission + delivery_cost

    cost_rows.append({
        "Channel": channel,
        "Revenue": revenue,
        "EstimatedCOGS": cogs,
        "EstimatedOPEX": opex,
        "EstimatedCommission": commission,
        "DeliveryCost": delivery_cost,
        "EstimatedTotalCosts": estimated_costs,
        "EstimatedProfit": revenue - estimated_costs,
        "EstimatedCostPct": (
            estimated_costs / revenue * 100 if revenue else np.nan
        )
    })

cost_summary = pd.DataFrame(cost_rows)
cost_summary.to_csv(OUTPUT / "cost_structure.csv", index=False)

print("\nESTIMATED COST STRUCTURE")
print(cost_summary.round(2).to_string(index=False))

# ---------------------------------------------------------
# 5. VERIFY CANDIDATE PROFIT FORMULAS
# ---------------------------------------------------------

candidate_profit = {
    "In-store": (
        df["InStoreRevenue"]
        - df["InStoreRevenue"] * df["COGSRate"]
        - df["InStoreRevenue"] * df["OPEXRate"]
    ),
    "Uber Eats": (
        df["UberEatsRevenue"]
        - df["UberEatsRevenue"] * df["COGSRate"]
        - df["UberEatsRevenue"] * df["OPEXRate"]
        - df["UberEatsRevenue"] * df["CommissionRate"]
    ),
    "DoorDash": (
        df["DoorDashRevenue"]
        - df["DoorDashRevenue"] * df["COGSRate"]
        - df["DoorDashRevenue"] * df["OPEXRate"]
        - df["DoorDashRevenue"] * df["CommissionRate"]
    ),
    "Self-delivery": (
        df["SelfDeliveryRevenue"]
        - df["SelfDeliveryRevenue"] * df["COGSRate"]
        - df["SelfDeliveryRevenue"] * df["OPEXRate"]
        - df["SD_DeliveryTotalCost"]
    )
}

profit_validation_rows = []

for channel, calculated_profit in candidate_profit.items():
    actual_col = channels[channel][2]
    difference = calculated_profit - df[actual_col]

    profit_validation_rows.append({
        "Channel": channel,
        "MeanAbsoluteDifference": difference.abs().mean(),
        "MaximumAbsoluteDifference": difference.abs().max(),
        "RowsWithin001": int((difference.abs() <= 0.01).sum()),
        "TotalRows": len(df)
    })

profit_validation = pd.DataFrame(profit_validation_rows)
profit_validation.to_csv(
    OUTPUT / "profit_formula_validation.csv", index=False
)

print("\nPROFIT FORMULA VALIDATION")
print(profit_validation.round(5).to_string(index=False))

# ---------------------------------------------------------
# 6. SEGMENT-WISE CHANNEL PROFITABILITY
# ---------------------------------------------------------

segment_rows = []

for channel, (orders_col, revenue_col, profit_col) in channels.items():
    grouped = df.groupby("Segment").agg(
        Restaurants=("RestaurantID", "nunique"),
        Orders=(orders_col, "sum"),
        Revenue=(revenue_col, "sum"),
        NetProfit=(profit_col, "sum")
    ).reset_index()

    grouped["Channel"] = channel
    grouped["ProfitMarginPct"] = (
        grouped["NetProfit"] / grouped["Revenue"] * 100
    )
    grouped["ProfitPerOrder"] = (
        grouped["NetProfit"] / grouped["Orders"]
    )

    segment_rows.append(grouped)

segment_summary = pd.concat(segment_rows, ignore_index=True)
segment_summary.to_csv(
    OUTPUT / "segment_channel_profitability.csv", index=False
)

# ---------------------------------------------------------
# 7. RESTAURANT-LEVEL PROFITABILITY
# ---------------------------------------------------------

df["TotalRevenue"] = df[
    [
        "InStoreRevenue",
        "UberEatsRevenue",
        "DoorDashRevenue",
        "SelfDeliveryRevenue"
    ]
].sum(axis=1)

df["TotalRecordedNetProfit"] = df[
    [
        "InStoreNetProfit",
        "UberEatsNetProfit",
        "DoorDashNetProfit",
        "SelfDeliveryNetProfit"
    ]
].sum(axis=1)

df["OverallProfitMarginPct"] = np.where(
    df["TotalRevenue"] != 0,
    df["TotalRecordedNetProfit"] / df["TotalRevenue"] * 100,
    np.nan
)

df["AggregatorRevenue"] = (
    df["UberEatsRevenue"] + df["DoorDashRevenue"]
)

df["AggregatorProfit"] = (
    df["UberEatsNetProfit"] + df["DoorDashNetProfit"]
)

df["AggregatorProfitMarginPct"] = np.where(
    df["AggregatorRevenue"] != 0,
    df["AggregatorProfit"] / df["AggregatorRevenue"] * 100,
    np.nan
)

restaurant_cols = [
    "RestaurantID",
    "RestaurantName",
    "CuisineType",
    "Segment",
    "Subregion",
    "MonthlyOrders",
    "TotalRevenue",
    "TotalRecordedNetProfit",
    "OverallProfitMarginPct",
    "UberEatsNetProfit",
    "DoorDashNetProfit",
    "AggregatorRevenue",
    "AggregatorProfit",
    "AggregatorProfitMarginPct"
]

restaurant_summary = df[restaurant_cols].copy()

top10 = restaurant_summary.nlargest(
    10, "TotalRecordedNetProfit"
)

bottom10 = restaurant_summary.nsmallest(
    10, "TotalRecordedNetProfit"
)

loss_making_aggregator = restaurant_summary[
    restaurant_summary["AggregatorProfit"] < 0
].sort_values("AggregatorProfit")

high_revenue_low_margin = restaurant_summary[
    (restaurant_summary["TotalRevenue"] >=
     restaurant_summary["TotalRevenue"].quantile(0.75))
    & (restaurant_summary["OverallProfitMarginPct"] < 5)
].sort_values("OverallProfitMarginPct")

top10.to_csv(OUTPUT / "top_10_restaurants.csv", index=False)
bottom10.to_csv(OUTPUT / "bottom_10_restaurants.csv", index=False)

loss_making_aggregator.to_csv(
    OUTPUT / "loss_making_aggregator_restaurants.csv", index=False
)

high_revenue_low_margin.to_csv(
    OUTPUT / "high_revenue_low_margin_restaurants.csv", index=False
)

restaurant_summary.to_csv(
    OUTPUT / "restaurant_level_profitability.csv", index=False
)

print("\nTOP 10 RESTAURANTS BY TOTAL RECORDED PROFIT")
print(top10.round(2).to_string(index=False))

print("\nBOTTOM 10 RESTAURANTS BY TOTAL RECORDED PROFIT")
print(bottom10.round(2).to_string(index=False))

print("\nRESTAURANTS WITH NEGATIVE COMBINED AGGREGATOR PROFIT")
print("Count:", len(loss_making_aggregator))
print(loss_making_aggregator.head(20).round(2).to_string(index=False))

print("\nHIGH-REVENUE RESTAURANTS WITH MARGINS BELOW 5%")
print("Count:", len(high_revenue_low_margin))
print(high_revenue_low_margin.head(20).round(2).to_string(index=False))

# ---------------------------------------------------------
# 8. CUISINE-WISE PROFITABILITY
# ---------------------------------------------------------

cuisine_summary = df.groupby("CuisineType").agg(
    Restaurants=("RestaurantID", "nunique"),
    Orders=("MonthlyOrders", "sum"),
    TotalRevenue=("TotalRevenue", "sum"),
    TotalRecordedNetProfit=("TotalRecordedNetProfit", "sum")
).reset_index()

cuisine_summary["ProfitMarginPct"] = (
    cuisine_summary["TotalRecordedNetProfit"]
    / cuisine_summary["TotalRevenue"] * 100
)

cuisine_summary = cuisine_summary.sort_values(
    "TotalRecordedNetProfit", ascending=False
)

cuisine_summary.to_csv(
    OUTPUT / "cuisine_profitability.csv", index=False
)

print("\nCUISINE PROFITABILITY")
print(cuisine_summary.round(2).to_string(index=False))

# ---------------------------------------------------------
# 9. CHARTS
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))
sns.barplot(
    data=channel_summary,
    x="Channel",
    y="TotalRevenue"
)
plt.title("Total Revenue by Channel")
plt.ylabel("Revenue (currency units)")
plt.xlabel("Channel")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(OUTPUT / "channel_revenue.png", dpi=300)
plt.close()

plt.figure(figsize=(10, 6))
sns.barplot(
    data=channel_summary,
    x="Channel",
    y="ProfitMarginPct"
)
plt.title("Recorded Profit Margin by Channel")
plt.ylabel("Profit Margin (%)")
plt.xlabel("Channel")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(OUTPUT / "channel_profit_margin.png", dpi=300)
plt.close()

margin_pivot = segment_summary.pivot(
    index="Segment",
    columns="Channel",
    values="ProfitMarginPct"
)

plt.figure(figsize=(11, 6))
sns.heatmap(
    margin_pivot,
    annot=True,
    fmt=".2f",
    cmap="RdYlGn",
    center=0
)
plt.title("Profit Margin by Segment and Channel")
plt.tight_layout()
plt.savefig(OUTPUT / "segment_margin_heatmap.png", dpi=300)
plt.close()

plt.figure(figsize=(12, 7))
sns.barplot(
    data=cost_summary,
    x="Channel",
    y="EstimatedTotalCosts"
)
plt.title("Estimated Total Costs by Channel")
plt.ylabel("Estimated costs (currency units)")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(OUTPUT / "estimated_channel_costs.png", dpi=300)
plt.close()

plt.figure(figsize=(10, 6))
sns.barplot(
    data=cuisine_summary,
    x="CuisineType",
    y="TotalRecordedNetProfit"
)
plt.title("Total Recorded Profit by Cuisine")
plt.xlabel("Cuisine")
plt.ylabel("Recorded net profit (currency units)")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(OUTPUT / "cuisine_profitability.png", dpi=300)
plt.close()

# ---------------------------------------------------------
# 10. EXECUTIVE SUMMARY
# ---------------------------------------------------------

best_channel = channel_summary.loc[
    channel_summary["ProfitMarginPct"].idxmax()
]

highest_revenue_channel = channel_summary.loc[
    channel_summary["TotalRevenue"].idxmax()
]

highest_profit_channel = channel_summary.loc[
    channel_summary["RecordedNetProfit"].idxmax()
]

with open(OUTPUT / "executive_summary.txt", "w", encoding="utf-8") as f:
    f.write("RESTAURANT CHANNEL PROFITABILITY ANALYSIS\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Restaurant records analysed: {len(df):,}\n")
    f.write(f"Total revenue: {df['TotalRevenue'].sum():,.2f}\n")
    f.write(
        f"Total recorded net profit: "
        f"{df['TotalRecordedNetProfit'].sum():,.2f}\n\n"
    )
    f.write(
        f"Highest-margin channel: {best_channel['Channel']} "
        f"({best_channel['ProfitMarginPct']:.2f}%)\n"
    )
    f.write(
        f"Highest-revenue channel: {highest_revenue_channel['Channel']} "
        f"({highest_revenue_channel['TotalRevenue']:,.2f})\n"
    )
    f.write(
        f"Highest total-profit channel: {highest_profit_channel['Channel']} "
        f"({highest_profit_channel['RecordedNetProfit']:,.2f})\n\n"
    )
    f.write(
        f"Restaurants with negative combined aggregator profit: "
        f"{len(loss_making_aggregator)}\n"
    )
    f.write(
        f"High-revenue restaurants with margin below 5%: "
        f"{len(high_revenue_low_margin)}\n\n"
    )
    f.write(
        "Note: Currency is not specified in the source dataset. "
        "Cost figures are estimates based on supplied rates. "
        "Recorded profit is not independent evidence that every "
        "real-world expense has been included.\n"
    )

# ---------------------------------------------------------
# 11. FINAL STATUS
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("CONSOLIDATED ANALYSIS COMPLETED")
print("All outputs saved in the project_outputs folder.")
print("=" * 65)

print("\nGenerated deliverables include:")
for path in sorted(OUTPUT.iterdir()):
    print(path)
