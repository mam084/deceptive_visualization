import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ======================
# Load and Prepare Data
# ======================
df = pd.read_csv("emissions.csv")

def ytrim_from(data_like, ax=None, pad=0.05, exaggerate=False, floor0=True, strength=0.3):
    """
    Adjust y-limits to tighten the view or exaggerate differences slightly.
    strength: how strong the exaggeration is (0.0–1.0). 0.3 = show top 70%.
    """
    import pandas as pd
    vals = pd.DataFrame(data_like).stack().astype(float)
    dmin, dmax = float(vals.min()), float(vals.max())
    span = max(dmax - dmin, 1e-9)

    if exaggerate:
        # Keep more of the range visible (gentle zoom)
        ymin = dmax - span * (1 - strength)
    else:
        ymin = dmin - span * pad

    ymax = dmax + span * pad
    if floor0:
        ymin = max(0.0, ymin)

    (ax or plt.gca()).set_ylim(ymin, ymax)



# Columns that look like quarters e.g., 2010Q1, 2015Q3, etc.
time_cols = [c for c in df.columns if c.startswith(tuple(str(y) for y in range(2010, 2025)))]

def to_long(_df, id_vars):
    """Wide → long; parse quarter; numeric; clamp to 2010–2024 inclusive."""
    long = _df.melt(id_vars=id_vars, value_vars=time_cols,
                    var_name="Quarter", value_name="Emissions")
    long["Quarter"] = pd.PeriodIndex(long["Quarter"], freq="Q").to_timestamp(how="end")
    long["Emissions"] = pd.to_numeric(long["Emissions"], errors="coerce")
    return long[(long["Quarter"].dt.year >= 2010) & (long["Quarter"].dt.year <= 2024)]

# ============================================
# 1) OVERALL LINE: Total Emissions Over Time
# ============================================
totals = df[df["Industry"] == "Total Industry and Households"].copy()
long_total = to_long(totals, id_vars=["Country", "Industry"])

global_q = (long_total.groupby("Quarter", as_index=True)["Emissions"]
            .sum().sort_index().to_frame())
global_q["MA_4q"] = global_q["Emissions"].rolling(4, min_periods=1).mean()

# plt.figure(figsize=(10,5))
# plt.plot(global_q.index, global_q["Emissions"], label="Quarterly total", linewidth=1)
# plt.plot(global_q.index, global_q["MA_4q"], label="4-quarter moving average", linewidth=2)
# plt.title("Global Greenhouse Gas Emissions (Total, 2010–2024)")
# plt.xlabel("Quarter"); plt.ylabel("Mt CO₂e")
# plt.legend(); plt.tight_layout(); plt.show()

# ============================================
# 2) GROUPED BAR: Emissions by Sector & Year
# ============================================
# Map to short display names (don’t mutate original)
SHORT = {
    "Electricity, Gas, Steam and Air Conditioning Supply": "Energy",
    "Transportation and Storage": "Transport",
    "Water supply; sewerage, waste management and remediation activities": "Waste/Water",
    "Agriculture, Forestry and Fishing": "Agriculture",
    "Other Services Industries": "Other Services",
    "Manufacturing": "Manufacturing",
    "Mining": "Mining",
    "Construction": "Construction",
    "Total Households": "Households",
}

sectors = df[df["Industry"] != "Total Industry and Households"].copy()
sectors["Industry_short"] = sectors["Industry"].map(SHORT).fillna(sectors["Industry"])

sector_long = to_long(sectors, id_vars=["Industry", "Industry_short"])
sector_long["Year"] = sector_long["Quarter"].dt.year

sector_yearly = (sector_long
                 .groupby(["Industry_short", "Year"], as_index=False)["Emissions"]
                 .sum()
                 .rename(columns={"Emissions": "Total Emissions"}))

selected_years = [2010, 2015, 2020, 2024]
bar_data = sector_yearly[sector_yearly["Year"].isin(selected_years)]

pivot_bar = (bar_data
             .pivot(index="Industry_short", columns="Year", values="Total Emissions")
             .sort_index())

ax = pivot_bar.plot(kind="bar", figsize=(12,5))
plt.title("Energy and Manufacturing Lead Surge in Emissions")
plt.xlabel("Sector"); plt.ylabel("Mt CO₂e")
plt.legend(title="Year", loc="upper right", bbox_to_anchor=(1,1))
plt.xticks(rotation=30, ha="right")
# Example: exaggerate changes
#ytrim_from(pivot_bar, ax=ax, exaggerate=True, strength=0.1, pad=0.05, floor0=True)
# plt.ylim(global_q["Emissions"].min() * 0.95,
#          global_q["Emissions"].max() * 1.05)
plt.yscale("log")


plt.tight_layout(); plt.show()


# === Compare Electricity vs Total Emissions by Year ===

selected_years = [2010, 2015, 2020, 2024]

# Get total industry & households separately
total_data = df[df["Industry"] == "Total Industry and Households"].copy()
electricity_data = df[df["Industry"].str.contains("Electricity", case=False)].copy()

# Reshape both into long format
long_total = to_long(total_data, id_vars=["Industry"])
long_elec = to_long(electricity_data, id_vars=["Industry"])

# Sum both by year
total_yearly = long_total.groupby(long_total["Quarter"].dt.year)["Emissions"].sum().rename("Total Emissions")
elec_yearly = long_elec.groupby(long_elec["Quarter"].dt.year)["Emissions"].sum().rename("Energy Emissions")

# Combine into one DataFrame
compare_df = pd.concat([total_yearly, elec_yearly], axis=1)
compare_df = compare_df.loc[selected_years].reset_index(names="Year")

# Make a grouped bar chart
compare_df.plot(
    x="Year",
    y=["Total Emissions", "Energy Emissions"],
    kind="bar",
    figsize=(8,5),
    color=["gray", "orange"],
    width=0.75
)

plt.title("Energy’s Share of Total Emissions Has Stayed Consistently Low")
plt.xlabel("Year")
plt.ylabel("Mt CO₂e")
plt.legend(title="Category", loc="upper right")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
#ytrim_from(compare_df[["Total Emissions", "Energy Emissions"]],
           #ax=ax, exaggerate=True, strength=0.15, pad=0.05, floor0=True)
plt.yscale("log")
#plt.yscale("symlog", linthresh=1000)

plt.show()


# Select a few representative years
# selected_years = [2010, 2015, 2020, 2024]
# sector_subset = sector_yearly[sector_yearly["Quarter"].isin(selected_years)]
# pivot_bar = sector_subset.pivot(index="Industry", columns="Quarter", values="Total Emissions")

# pivot_bar.plot(kind="bar", figsize=(12,5))  # reduce height
# plt.title("Greenhouse Gas Emissions by Industry and Year", fontsize=12, pad=10)
# plt.xlabel("Industry", fontsize=10)
# plt.ylabel("Million metric tons of CO₂e", fontsize=10)
# plt.legend(title="Year", fontsize=8, title_fontsize=9)
# plt.xticks(rotation=45, ha="right", fontsize=8)
# plt.tight_layout()
# plt.show()

# pivot_sector = (sector_yearly
#                 .pivot(index="Quarter", columns="Industry_short", values="Total Emissions")
#                 .sort_index())
# sector_pct = pivot_sector.div(pivot_sector.sum(axis=1), axis=0) * 100

# plt.figure(figsize=(12,5))
# sector_pct.plot.area(ax=plt.gca(), alpha=0.9)
# plt.title("Share of Total GHG Emissions by Sector (%, 2010–2024)", fontsize=12, pad=10)
# plt.xlabel("Year", fontsize=10); plt.ylabel("Percent of total", fontsize=10)
# plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1), title="Sector")
# plt.tight_layout(); plt.show()

# ============================================
# 3️⃣ 100% STACKED AREA: Share of Total Emissions by Industry
# ============================================
# pivot_sector = sector_yearly.pivot(index="Quarter", columns="Industry", values="Total Emissions")
# sector_pct = pivot_sector.apply(lambda x: x / x.sum() * 100, axis=1)

# plt.figure(figsize=(12,6))
# sector_pct.plot.area(ax=plt.gca(), cmap="tab20", alpha=0.9)
# plt.title("Share of Total Greenhouse Gas Emissions by Industry (Percentage of Global Total)")
# plt.xlabel("Year")
# plt.ylabel("Percent of Total Emissions")
# plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1), title="Industry")
# plt.tight_layout()
# plt.show()
