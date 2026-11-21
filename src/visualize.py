# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Visualization Module for NYC 311 Service Requests (Part A).
Dataset: NYC Open Data 311 Service Requests (2010 - 2019)

Generates publication-grade figures saved to outputs/figures/:
1. Figure 1: Top 10 Complaint Types Volume & Share.
2. Figure 2: Resolution Hours Across Boroughs (Median & Mean in Hours).
3. Figure 3: Diurnal / Hourly Distribution of Ticket Volume (Hour of Day [0-23]).
4. Figure 4: Distribution of Log(1 + Resolution Hours) showing skew and outliers.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10

def generate_visualizations(df: pd.DataFrame, output_dir: str = "outputs/figures") -> list:
    """
    Renders and saves publication-grade figures with clear titles, units, and descriptions.
    
    Parameters:
        df (pd.DataFrame): Cleaned and enriched dataframe.
        output_dir (str): Directory where figures will be stored.
        
    Returns:
        list: Filepaths of generated figures.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    # -------------------------------------------------------------------------
    # Figure 1: Top 10 Complaint Types
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    top_complaints = df["complaint_type"].value_counts().head(10)
    bars = plt.barh(top_complaints.index[::-1], top_complaints.values[::-1], color="#1f77b4", edgecolor="black")
    plt.title("Top 10 NYC 311 Service Request Complaint Types (2010 - 2019)", fontsize=13, weight="bold", pad=12)
    plt.xlabel("Total Service Requests (Count / Volume)", fontsize=11, labelpad=8)
    plt.ylabel("Complaint Category", fontsize=11, labelpad=8)
    
    for bar in bars:
        w = bar.get_width()
        plt.text(w + max(top_complaints.values)*0.01, bar.get_y() + bar.get_height()/2.0, f"{int(w):,}", va="center", fontsize=9)
        
    plt.xlim(0, max(top_complaints.values) * 1.15)
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "figure1_top_complaints.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    generated_files.append(fig1_path)
    
    # -------------------------------------------------------------------------
    # Figure 2: Borough Resolution Duration Disparities (Median vs Mean)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    valid_durations = df.dropna(subset=["resolution_hours"])
    b_stats = valid_durations.groupby("borough")["resolution_hours"].agg(["median", "mean"]).sort_values(by="median", ascending=False)
    
    x = np.arange(len(b_stats))
    width = 0.35
    
    rects1 = plt.bar(x - width/2, b_stats["median"], width, label="Median Duration", color="#2ca02c", edgecolor="black")
    rects2 = plt.bar(x + width/2, b_stats["mean"], width, label="Mean Duration", color="#d62728", edgecolor="black")
    
    plt.title("NYC 311 Ticket Resolution Duration by Borough (Median vs Mean Hours)", fontsize=13, weight="bold", pad=12)
    plt.xlabel("Borough Name", fontsize=11, labelpad=8)
    plt.ylabel("Resolution Duration (Hours)", fontsize=11, labelpad=8)
    plt.xticks(x, b_stats.index)
    plt.legend(frameon=True)
    
    for rect in rects1:
        h = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, h + 5, f"{h:.1f}h", ha="center", fontsize=9, weight="bold")
        
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "figure2_borough_resolution_distribution.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    generated_files.append(fig2_path)
    
    # -------------------------------------------------------------------------
    # Figure 3: Diurnal Ingestion Profile
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    if "created_hour" in df.columns:
        hourly_counts = df["created_hour"].value_counts().sort_index()
        plt.plot(hourly_counts.index, hourly_counts.values, marker="o", linewidth=2.5, color="#9467bd", markersize=6)
        plt.fill_between(hourly_counts.index, hourly_counts.values, color="#9467bd", alpha=0.15)
        plt.title("Diurnal Ingestion Profile: Hourly Volume of 311 Service Requests", fontsize=13, weight="bold", pad=12)
        plt.xlabel("Hour of Day (24-Hour Standard Time [00:00 - 23:00])", fontsize=11, labelpad=8)
        plt.ylabel("Incoming Service Requests (Ticket Count)", fontsize=11, labelpad=8)
        plt.xticks(range(0, 24, 2))
        plt.tight_layout()
        fig3_path = os.path.join(output_dir, "figure3_hourly_demand_profile.png")
        plt.savefig(fig3_path, dpi=300)
        plt.close()
        generated_files.append(fig3_path)
        
    # -------------------------------------------------------------------------
    # Figure 4: Log-Transformed Resolution Hours Distribution
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 5.5))
    if "log_resolution_hours" in df.columns:
        valid_log = df["log_resolution_hours"].dropna()
        sns.histplot(valid_log, bins=40, kde=True, color="#ff7f0e", edgecolor="black")
        plt.title("Distribution of Log(1 + Resolution Hours) Regression Target", fontsize=13, weight="bold", pad=12)
        plt.xlabel("Log(1 + Resolution Duration in Hours)", fontsize=11, labelpad=8)
        plt.ylabel("Frequency (Number of Service Requests)", fontsize=11, labelpad=8)
        plt.axvline(valid_log.median(), color="red", linestyle="--", linewidth=2, label=f"Median Log-Duration: {valid_log.median():.2f}")
        plt.legend(frameon=True)
        plt.tight_layout()
        fig4_path = os.path.join(output_dir, "figure4_resolution_skew_log.png")
        plt.savefig(fig4_path, dpi=300)
        plt.close()
        generated_files.append(fig4_path)
        
    print(f"[SUCCESS] Saved {len(generated_files)} figures to: {output_dir}")
    return generated_files
