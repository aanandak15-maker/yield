import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

# ===========================
# Ensure output folder exists
# ===========================
os.makedirs("plots", exist_ok=True)

# ===========================
# Part 1: Train & Evaluate Model (2019–2023)
# ===========================

# Load historical training data (2019–2023)
df_train = pd.read_csv("crop_yield_climate_soil_data_2019_2023.csv")
df_train.columns = df_train.columns.str.strip()  # Clean column names

# Create a date column if 'year' and 'month' exist (for time-series plots)
if 'year' in df_train.columns and 'month' in df_train.columns:
    df_train['date'] = pd.to_datetime(
        df_train['year'].astype(int).astype(str) + '-' +
        df_train['month'].astype(int).astype(str) + '-01'
    )

# Define features and target - updated to match processed data column names
features = ['Fpar', 'NDVI', 'precipitation', 'solar_radiation', 'soil_ph', 'temp_mean']
target = 'yield_proxy'  # Use yield proxy from processed data

# Extract features and target from training data
X = df_train[features]
y = df_train[target]

# Split the dataset into training and test sets (80%/20%)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Standardize the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# Apply polynomial feature expansion (degree 2)
poly = PolynomialFeatures(degree=2, include_bias=False)
X_train_poly = poly.fit_transform(X_train_scaled)
X_test_poly  = poly.transform(X_test_scaled)

# Train a Ridge Regression model
model = Ridge(alpha=0.1)
model.fit(X_train_poly, y_train)

# Evaluate the model on the test set
y_pred_test = model.predict(X_test_poly)
residuals    = y_test - y_pred_test
r2 = r2_score(y_test, y_pred_test)
print(f"R² Score on Test Subset (2019–2023): {r2:.5f}")

# ===========================
# Visualizations (At least 12 Plots)
# ===========================

# 1. Predicted vs Actual Crop Yield
plt.figure(figsize=(12, 6))
sns.scatterplot(x=y_test, y=y_pred_test, color='blue')
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel("Actual Combined Crop Yield")
plt.ylabel("Predicted Combined Crop Yield")
plt.title("Predicted vs Actual Crop Yield (Test Subset)")
plt.savefig("plots/01_pred_vs_actual.png", bbox_inches="tight")
plt.show()

# 2. Residual Plot
plt.figure(figsize=(12, 6))
sns.scatterplot(x=y_pred_test, y=residuals, color='red')
plt.axhline(0, color='black', linestyle='--')
plt.xlabel("Predicted Combined Crop Yield")
plt.ylabel("Residuals")
plt.title("Residual Plot")
plt.savefig("plots/02_residuals.png", bbox_inches="tight")
plt.show()

# 3. Scatter Plot: Fpar vs Combined Crop Yield
plt.figure(figsize=(6, 4))
sns.scatterplot(
    x=df_train['Fpar'], y=df_train[target],
    hue=df_train['year'] if 'year' in df_train.columns else None,
    palette='viridis'
)
plt.xlabel("Fpar")
plt.ylabel("Combined Crop Yield")
plt.title("Fpar vs Combined Crop Yield")
plt.savefig("plots/03_fpar_vs_yield.png", bbox_inches="tight")
plt.show()

# 4. Scatter Plot: NDVI vs Combined Crop Yield
plt.figure(figsize=(6, 4))
sns.scatterplot(
    x=df_train['NDVI'], y=df_train[target],
    hue=df_train['year'] if 'year' in df_train.columns else None,
    palette='viridis'
)
plt.xlabel("NDVI")
plt.ylabel("Combined Crop Yield")
plt.title("NDVI vs Combined Crop Yield")
plt.savefig("plots/04_ndvi_vs_yield.png", bbox_inches="tight")
plt.show()

# 5. Scatter Plot: Rainfall vs Combined Crop Yield
plt.figure(figsize=(6, 4))
sns.scatterplot(
    x=df_train['Rainfall'], y=df_train[target],
    hue=df_train['year'] if 'year' in df_train.columns else None,
    palette='viridis'
)
plt.xlabel("Rainfall")
plt.ylabel("Combined Crop Yield")
plt.title("Rainfall vs Combined Crop Yield")
plt.savefig("plots/05_rainfall_vs_yield.png", bbox_inches="tight")
plt.show()

# 6. Scatter Plot: Sunlight vs Combined Crop Yield
plt.figure(figsize=(6, 4))
sns.scatterplot(
    x=df_train['Sunlight'], y=df_train[target],
    hue=df_train['year'] if 'year' in df_train.columns else None,
    palette='viridis'
)
plt.xlabel("Sunlight")
plt.ylabel("Combined Crop Yield")
plt.title("Sunlight vs Combined Crop Yield")
plt.savefig("plots/06_sunlight_vs_yield.png", bbox_inches="tight")
plt.show()

# 7. Scatter Plot: Soil_PH vs Combined Crop Yield
plt.figure(figsize=(6, 4))
sns.scatterplot(
    x=df_train['Soil_PH'], y=df_train[target],
    hue=df_train['year'] if 'year' in df_train.columns else None,
    palette='viridis'
)
plt.xlabel("Soil_PH")
plt.ylabel("Combined Crop Yield")
plt.title("Soil_PH vs Combined Crop Yield")
plt.savefig("plots/07_soilph_vs_yield.png", bbox_inches="tight")
plt.show()

# 8. Scatter Plot: Temperature vs Combined Crop Yield
plt.figure(figsize=(6, 4))
sns.scatterplot(
    x=df_train['Temperature'], y=df_train[target],
    hue=df_train['year'] if 'year' in df_train.columns else None,
    palette='viridis'
)
plt.xlabel("Temperature")
plt.ylabel("Combined Crop Yield")
plt.title("Temperature vs Combined Crop Yield")
plt.savefig("plots/08_temperature_vs_yield.png", bbox_inches="tight")
plt.show()

# 9. Pairplot of Features and Target (include 'year' if exists)
if 'year' in df_train.columns:
    sns.pairplot(
        df_train[features + [target] + ['year']],
        hue='year', palette='viridis'
    )
else:
    sns.pairplot(df_train[features + [target]])
plt.suptitle("Pairplot of Features and Combined Crop Yield", y=1.02)
plt.savefig("plots/09_pairplot.png", bbox_inches="tight")
plt.show()

# 10. Correlation Heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(
    df_train[features + [target]].corr(),
    annot=True, cmap="coolwarm", fmt=".2f"
)
plt.title("Feature Correlation Heatmap")
plt.savefig("plots/10_heatmap_corr.png", bbox_inches="tight")
plt.show()

# 11. Boxplot of Combined Crop Yield by Year (if year exists)
if 'year' in df_train.columns:
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        x=df_train['year'].astype(int),
        y=df_train[target],
        palette='viridis'
    )
    plt.title("Combined Crop Yield by Year")
    plt.xlabel("Year")
    plt.ylabel("Combined Crop Yield")
    plt.savefig("plots/11_boxplot_year.png", bbox_inches="tight")
    plt.show()

# 12. Line Plot: Combined Crop Yield Over Time (if date exists)
if 'date' in df_train.columns:
    df_train_sorted = df_train.sort_values('date')
    plt.figure(figsize=(12, 6))
    plt.plot(
        df_train_sorted['date'],
        df_train_sorted[target],
        marker='o', linestyle='-'
    )
    plt.title("Combined Crop Yield Over Time")
    plt.xlabel("Date")
    plt.ylabel("Combined Crop Yield")
    plt.xticks(rotation=45)
    plt.savefig("plots/12_timeseries.png", bbox_inches="tight")
    plt.show()

# ===========================
# Part 2: Predict 2024 Crop Yield Using New Data
# ===========================

# Load new 2024 parameters
df_2024 = pd.read_csv("2024_params.csv")
df_2024.columns = df_2024.columns.str.strip()
print("2024 Data Preview:")
print(df_2024.head())

# Extract features from the new 2024 data
X_new = df_2024[features]

# Apply the same standardization and polynomial feature transformation
X_new_scaled = scaler.transform(X_new)
X_new_poly   = poly.transform(X_new_scaled)

# Predict the crop yield for 2024 using the trained model
y_2024_pred = model.predict(X_new_poly)
df_2024["Predicted_Combined_Crop_Yield"] = y_2024_pred

print("Predictions for 2024:")
print(df_2024)

# Visualization for 2024 Predictions: If a 'month' column exists, plot by month; otherwise, scatter plot by index
if 'month' in df_2024.columns:
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        x='month', y='Predicted_Combined_Crop_Yield',
        data=df_2024, marker='o', color='green'
    )
    plt.title("Predicted Combined Crop Yield for 2024 (Monthly)")
    plt.xlabel("Month")
    plt.ylabel("Predicted Combined Crop Yield")
    plt.xticks(sorted(df_2024['month'].unique()))
    plt.savefig("plots/13_2024_monthly_line.png", bbox_inches="tight")
    plt.show()
else:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        x=df_2024.index,
        y="Predicted_Combined_Crop_Yield",
        data=df_2024, color='green'
    )
    plt.title("Predicted Combined Crop Yield for 2024")
    plt.xlabel("Sample Index")
    plt.ylabel("Predicted Combined Crop Yield")
    plt.savefig("plots/13_2024_index_scatter.png", bbox_inches="tight")
    plt.show()

# ===========================
# Part 3: 12 Prediction‑Focused Visualizations
# ===========================

# 1. Monthly Barplot (if month exists)
if 'month' in df_2024.columns:
    plt.figure(figsize=(10,6))
    sns.barplot(
        x='month', 
        y='Predicted_Combined_Crop_Yield', 
        data=df_2024, 
        palette='Blues_d'
    )
    plt.title("Avg Predicted Yield by Month (2024)")
    plt.savefig("plots/01_monthly_barplot.png", bbox_inches="tight")
    plt.show()

# 2. Overall Boxplot
plt.figure(figsize=(6,6))
sns.boxplot(
    y=df_2024["Predicted_Combined_Crop_Yield"], 
    color='lightblue'
)
plt.title("Distribution of Predicted Yields (2024)")
plt.ylabel("Predicted Yield")
plt.savefig("plots/02_overall_boxplot.png", bbox_inches="tight")
plt.show()

# 3. Histogram + KDE
plt.figure(figsize=(8,5))
sns.histplot(
    df_2024["Predicted_Combined_Crop_Yield"], 
    kde=True, 
    color='green', 
    bins=10
)
plt.title("Histogram & KDE of Predicted Yields")
plt.xlabel("Predicted Yield")
plt.savefig("plots/03_hist_kde.png", bbox_inches="tight")
plt.show()

# 4. Scatter: Index vs Prediction
plt.figure(figsize=(8,5))
sns.scatterplot(
    x=df_2024.index, 
    y="Predicted_Combined_Crop_Yield", 
    data=df_2024, 
    color='purple'
)
plt.title("Predicted Yield by Sample Index")
plt.xlabel("Sample Index")
plt.ylabel("Predicted Yield")
plt.savefig("plots/04_index_scatter.png", bbox_inches="tight")
plt.show()

# 5. Residuals Boxplot
plt.figure(figsize=(6,6))
sns.boxplot(
    y=residuals, 
    color='salmon'
)
plt.title("Boxplot of Residuals (Test Set)")
plt.ylabel("Residual")
plt.savefig("plots/05_residuals_boxplot.png", bbox_inches="tight")
plt.show()

# 6. Residuals vs Prediction Heatmap
resid_df = pd.DataFrame({
    "predicted": y_pred_test,
    "residual": residuals
})
plt.figure(figsize=(5,4))
sns.heatmap(
    resid_df.corr(), 
    annot=True, 
    cmap="coolwarm", 
    fmt=".2f"
)
plt.title("Corr: Predicted vs Residuals")
plt.savefig("plots/06_residuals_heatmap.png", bbox_inches="tight")
plt.show()

# 7. Pred vs Actual with Trend Line
plt.figure(figsize=(8,6))
sns.regplot(
    x=y_test, 
    y=y_pred_test, 
    scatter_kws={'s':20}, 
    line_kws={'color':'red'}
)
plt.title("Predicted vs Actual with Regression Line")
plt.xlabel("Actual Yield")
plt.ylabel("Predicted Yield")
plt.savefig("plots/07_trendline.png", bbox_inches="tight")
plt.show()

# 8. Cumulative Predicted Yield Over Samples
plt.figure(figsize=(8,5))
plt.plot(
    np.arange(len(y_2024_pred)), 
    np.cumsum(y_2024_pred), 
    marker='o', 
    linestyle='-'
)
plt.title("Cumulative Predicted Yield (2024)")
plt.xlabel("Sample Index")
plt.ylabel("Cumulative Yield")
plt.savefig("plots/08_cumulative_line.png", bbox_inches="tight")
plt.show()

# 9. Violin Plot by Month (if month exists)
if 'month' in df_2024.columns:
    plt.figure(figsize=(10,6))
    sns.violinplot(
        x='month', 
        y='Predicted_Combined_Crop_Yield', 
        data=df_2024, 
        palette='Pastel1'
    )
    plt.title("Violin Plot of Predicted Yields by Month")
    plt.savefig("plots/09_violin_month.png", bbox_inches="tight")
    plt.show()

# 10. Pairplot: Predictions vs Features
pair_df = df_2024[features + ["Predicted_Combined_Crop_Yield"]]
sns.pairplot(pair_df, diag_kind='kde')
plt.suptitle("Pairplot: Features & Predicted Yield", y=1.02)
plt.savefig("plots/10_pairplot_pred.png", bbox_inches="tight")
plt.show()

# 11. Scatter Matrix Heatmap
corr_pred = pair_df.corr()
plt.figure(figsize=(8,6))
sns.heatmap(
    corr_pred, 
    annot=True, 
    cmap="YlGnBu", 
    fmt=".2f"
)
plt.title("Correlation Matrix: Features & Predicted Yield")
plt.savefig("plots/11_corr_matrix_pred.png", bbox_inches="tight")
plt.show()

# 12. Time Series of Predicted Yield (if date exists)
if 'month' in df_2024.columns and 'year' in df_2024.columns:
    df_2024['date'] = pd.to_datetime(
        df_2024['year'].astype(int).astype(str) + '-' +
        df_2024['month'].astype(int).astype(str) + '-01'
    )
if 'date' in df_2024.columns:
    df_2024_sorted = df_2024.sort_values('date')
    plt.figure(figsize=(10,6))
    plt.plot(
        df_2024_sorted['date'], 
        df_2024_sorted["Predicted_Combined_Crop_Yield"], 
        marker='o', 
        linestyle='-'
    )
    plt.title("Predicted Yield Over Time (2024)")
    plt.xlabel("Date")
    plt.ylabel("Predicted Yield")
    plt.xticks(rotation=45)
    plt.savefig("plots/12_pred_timeseries.png", bbox_inches="tight")
    plt.show()
