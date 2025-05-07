#!/usr/bin/env python3
"""
analysis_script.py

Usage:
    python analysis_script.py results_prop1.json results_prop2.json results_prop3.json

This script:

1. Reads three JSON files corresponding to proportions 0.2, 0.5, 0.8.
2. Concatenates all results into a single DataFrame, filtering out the "degree" method.
3. Creates 3 tables (CSV):
   - Table 1 (extensional metrics): extension_deviation, CE-CO, CE-PR, CE-ST
   - Table 2 (structural metrics): structural_deviation, density, avg_degree, weak_connectivity, reciprocity
   - Table 3 (overall metric): overall_deviation
   Each table is grouped by [method, proportion], taking mean values across all input files.
4. Produces 3 bar charts (PNG) for the key aggregate metrics:
   - extension_deviation
   - structural_deviation
   - overall_deviation
   x-axis = method, hue = proportion, no error bars, and a muted color palette.
"""

import sys
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_json_data(json_file, proportion_label):
    """
    Loads a JSON file with structure:
    {
      "method_name": {
        "filename": {
          "extension_deviation": float,
          "extension_deviation_details": { ... },
          "structural_deviation": float,
          "structural_deviation_details": { ... },
          "overall_deviation": float
        },
        ...
      },
      ...
    }

    Returns a DataFrame with columns:
      [proportion, method, filename,
       extension_deviation, CE-CO, CE-PR, CE-ST,
       structural_deviation, density, avg_degree, weak_connectivity, reciprocity,
       overall_deviation]
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    rows = []
    for method_name, file_dict in data.items():
        for file_name, metrics in file_dict.items():
            # High-level deviations
            extension_dev = metrics.get("extension_deviation", None)
            structural_dev = metrics.get("structural_deviation", None)
            overall_dev = metrics.get("overall_deviation", None)

            # Extension details
            ext_details = metrics.get("extension_deviation_details", {})
            ce_co = ext_details.get("CE-CO", None)
            ce_pr = ext_details.get("CE-PR", None)
            ce_st = ext_details.get("CE-ST", None)

            # Structural details
            struct_details = metrics.get("structural_deviation_details", {})
            density = struct_details.get("density", None)
            avg_deg = struct_details.get("avg_degree", None)
            weak_conn = struct_details.get("weak_connectivity", None)
            reciprocity = struct_details.get("reciprocity", None)

            rows.append({
                "proportion": proportion_label,
                "method": method_name,
                "filename": file_name,
                "extension_deviation": extension_dev,
                "CE-CO": ce_co,
                "CE-PR": ce_pr,
                "CE-ST": ce_st,
                "structural_deviation": structural_dev,
                "density": density,
                "avg_degree": avg_deg,
                "weak_connectivity": weak_conn,
                "reciprocity": reciprocity,
                "overall_deviation": overall_dev
            })
    return pd.DataFrame(rows)

def plot_bar_chart(df, metric, outfile):
    """
    Creates a simple bar chart for `metric`, with:
      x-axis = method,
      hue = proportion,
      y-axis = mean of the metric,
    no error bars (ci=None),
    and saves as PNG to `outfile`.
    """
    plt.figure(figsize=(6, 5))
    sns.set_theme(style="whitegrid", palette="Set2")

    sns.barplot(
        data=df,
        x="method",
        y=metric,
        hue="proportion",
        ci=None
    )
    plt.title(f"{metric} by Method and Proportion")
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()

def main():
    if len(sys.argv) != 4:
        print("Usage: python analysis_script.py results_prop1.json results_prop2.json results_prop3.json")
        sys.exit(1)

    # File inputs for proportions 0.2, 0.5, 0.8
    file_02, file_05, file_08 = sys.argv[1], sys.argv[2], sys.argv[3]

    # Load & label data
    df_02 = load_json_data(file_02, "0.2")
    df_05 = load_json_data(file_05, "0.5")
    df_08 = load_json_data(file_08, "0.8")

    # Combine
    df = pd.concat([df_02, df_05, df_08], ignore_index=True)

    # Filter out "degree" method
    df = df[df["method"] != "degree"]

    # ------------------------
    # 1) Create Three Tables
    # ------------------------
    # We'll group by (method, proportion) and compute means of relevant columns.

    # Table 1: Extensional metrics
    ext_cols = ["extension_deviation", "CE-CO", "CE-PR", "CE-ST"]
    table_ext = (
        df.groupby(["method", "proportion"], as_index=False)[ext_cols]
        .mean(numeric_only=True)
    )
    table_ext.to_csv("table1_extensional_metrics.csv", index=False)

    # Table 2: Structural metrics
    str_cols = ["structural_deviation", "density", "avg_degree",
                "weak_connectivity", "reciprocity"]
    table_str = (
        df.groupby(["method", "proportion"], as_index=False)[str_cols]
        .mean(numeric_only=True)
    )
    table_str.to_csv("table2_structural_metrics.csv", index=False)

    # Table 3: Overall metric
    ov_cols = ["overall_deviation"]
    table_ov = (
        df.groupby(["method", "proportion"], as_index=False)[ov_cols]
        .mean(numeric_only=True)
    )
    table_ov.to_csv("table3_overall_metric.csv", index=False)

    # ------------------------
    # 2) Create Three Charts
    # ------------------------
    # a) extension_deviation
    plot_bar_chart(df, "extension_deviation", "figure1_extension_deviation.png")

    # b) structural_deviation
    plot_bar_chart(df, "structural_deviation", "figure2_structural_deviation.png")

    # c) overall_deviation
    plot_bar_chart(df, "overall_deviation", "figure3_overall_deviation.png")

    print("Done! Generated 3 tables and 3 figures:")
    print("Tables (CSV):")
    print("  - table1_extensional_metrics.csv")
    print("  - table2_structural_metrics.csv")
    print("  - table3_overall_metric.csv")
    print("Figures (PNG):")
    print("  - figure1_extension_deviation.png")
    print("  - figure2_structural_deviation.png")
    print("  - figure3_overall_deviation.png")

if __name__ == "__main__":
    main()
