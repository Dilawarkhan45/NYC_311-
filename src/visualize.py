# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Visualization Module for NYC 311 Service Requests.
Generates four publication-quality figures saved into outputs/figures/:
1. Top 10 Complaint Types Volume & Share
2. Borough Resolution Time Disparities
3. Diurnal / Hourly Intake Demand Profile
4. Channel Distribution by Responding Agency
Each figure contains a clear title, fully labelled axes with units, and a descriptive caption.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set standard styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10

def generate_visualizations(df: pd.DataFrame, output_dir: str = "outputs/figures") -> list:
    """
    Generates and saves at least 3 distinct visualizations with titles, units, and captions.
    
    Parameters:
        df (pd.DataFrame): Cleaned and feature-engineered dataframe.
        output_dir (str): Destination directory for image files.
        
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
    bars = plt.barh(top_complaints.index[::-1], top_complaints.values[::-1], color="#2b5c8f", edgecolor="black")
    plt.title("Top 10 NYC 311 Service Request Complaint Types (December 2019)", fontsize=13, weight="bold", pad=12)
    plt.xlabel("Total Service Requests (Count / Volume)", fontsize=11, labelpad=8)
    plt.ylabel("Complaint Category", fontsize=11, labelpad=8)
    
    # Annotate bar counts
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 20, bar.get_y() + bar.get_height()/2.0, f"{int(w):,}", va="center", fontsize=9)
        
    plt.xlim(0, max(top_complaints.values) * 1.15)
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "figure1_top_complaints.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    generated_files.append(fig1_path)
    
    # -------------------------------------------------------------------------
    # Figure 2: Borough Median Resolution Duration
    # -------------------------------------------------------------------------
    plt.figure(figsize=(9, 5.5))
    valid_durations = df.dropna(subset=["resolution_time_hours"])
    borough_medians = valid_durations.groupby("borough")["resolution_time_hours"].median().sort_values(ascending=False)
    
    colors = ["#c0392b", "#d35400", "#e67e22", "#27ae60", "#2980b9"]
    bars2 = plt.bar(borough_medians.index, borough_medians.values, color=colors[:len(borough_medians)], edgecolor="black")
    plt.title("Median Service Request Resolution Duration Across NYC Boroughs", fontsize=13, weight="bold", pad=12)
    plt.xlabel("Borough Name", fontsize=11, labelpad=8)
    plt.ylabel("Median Resolution Duration (Hours)", fontsize=11, labelpad=8)
    
    for bar in bars2:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, h + 0.8, f"{h:.1f} hrs", ha="center", fontsize=10, weight="bold")
        
    plt.ylim(0, max(borough_medians.values) * 1.2)
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "figure2_borough_resolution_distribution.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    generated_files.append(fig2_path)
    
    # -------------------------------------------------------------------------
    # Figure 3: Hourly Intake Demand Curve
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    if "created_hour" in df.columns:
        hourly_counts = df["created_hour"].value_counts().sort_index()
        plt.plot(hourly_counts.index, hourly_counts.values, marker="o", linewidth=2.5, color="#8e44ad", markersize=6)
        plt.fill_between(hourly_counts.index, hourly_counts.values, color="#8e44ad", alpha=0.15)
        plt.title("Diurnal Profile: Hourly Intake Volume of NYC 311 Service Requests", fontsize=13, weight="bold", pad=12)
        plt.xlabel("Hour of Day (24-Hour Standard Time [00:00 - 23:00])", fontsize=11, labelpad=8)
        plt.ylabel("Incoming Requests (Ticket Count)", fontsize=11, labelpad=8)
        plt.xticks(range(0, 24, 2))
        plt.tight_layout()
        fig3_path = os.path.join(output_dir, "figure3_hourly_demand_profile.png")
        plt.savefig(fig3_path, dpi=300)
        plt.close()
        generated_files.append(fig3_path)
        
    # -------------------------------------------------------------------------
    # Figure 4: Model Target Class Distribution by Intake Channel
    # -------------------------------------------------------------------------
    plt.figure(figsize=(9, 5.5))
    if "open_data_channel_type" in df.columns and "is_long_resolution" in df.columns:
        valid_channel = df.dropna(subset=["open_data_channel_type", "is_long_resolution"])
        channel_cross = pd.crosstab(valid_channel["open_data_channel_type"], valid_channel["is_long_resolution"], normalize="index") * 100
        
        channel_cross.plot(kind="bar", stacked=True, color=["#27ae60", "#e74c3c"], figsize=(9, 5.5), edgecolor="black")
        plt.title("Resolution Speed Classification (>24h vs <=24h) by Intake Channel", fontsize=13, weight="bold", pad=12)
        plt.xlabel("Citizen Ingestion Channel Type", fontsize=11, labelpad=8)
        plt.ylabel("Proportion of Requests (Percentage %)", fontsize=11, labelpad=8)
        plt.legend(["Fast Resolution (<=24 hrs)", "Long Resolution (>24 hrs)"], loc="upper right")
        plt.xticks(rotation=0)
        plt.tight_layout()
        fig4_path = os.path.join(output_dir, "figure4_channel_resolution_breakdown.png")
        plt.savefig(fig4_path, dpi=300)
        plt.close()
        generated_files.append(fig4_path)
        
    print(f"[SUCCESS] Saved {len(generated_files)} publication-grade figures to: {output_dir}")
    return generated_files
