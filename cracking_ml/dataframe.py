import numpy as np
import pandas as pd

df = pd.DataFrame({
    "age":    [25, np.nan, 35, 40, np.nan, 50],
    "salary": [3000, 4000, np.nan, 8000, 5000, 100000],   # 100000 = outlier
    "city":   ["HCM", "HN", "HCM", np.nan, "DN", "HN"],
    "size":   ["S", "M", "L", "M", "S", "L"],              # ordered category
})

df = df.copy()

for col in df:
    if df[col].dtype != "float64":
        df[col] = df[col].fillna(df[col].mode()[0])
    else:
        df[col] = df[col].fillna(df[col].median())

for city in df["city"].unique():
    df["city_" + city] = (df["city"] == city).astype(int)

num_cols = ["age", "salary"]

for col in num_cols:
    x = df[col]

    mean = x.mean()
    std = x.std()
    df[col + "_standard"] = (x - mean) / std

    min_val = x.min()
    max_val = x.max()
    df[col + "_minmax"] = (x - min_val) / (max_val - min_val)

    median = x.median()
    q1 = x.quantile(0.25)
    q3 = x.quantile(0.75)
    iqr = q3 - q1
    df[col + "_robust"] = (x - median) / iqr


x = df["salary"]
q1 = x.quantile(0.25)
q3 = x.quantile(0.75)
iqr = q3 - q1

lower = q1 - 1.5*iqr
upper = q3 + 1.5*iqr

df["salary_outlier_iqr"] = (x < lower) | (x > upper)

print(df)

# Cosine
a = np.array([1, 2, 3])
b = np.array([4, 0 ,3])

# Step 1: dot product (multiply pairwise, then add)
# 1*4 + 2*0 + 3*3 = 13
dot = 0
for i in range(len(a)):
    dot += a[i] * b[i]

# Step 2: length of each vector
# |a| = sqrt(1² + 2² + 3²) = sqrt(14) = 3.74
# |b| = sqrt(4² + 0² + 3²) = sqrt(25) = 5
sum_sqr_a = 0.0
sum_sqr_b = 0.0
for i in range(len(a)):
    sum_sqr_a += a[i] ** 2
    sum_sqr_b += b[i] ** 2

len_a = np.sqrt(sum_sqr_a)
len_b = np.sqrt(sum_sqr_b)

# Step 3: cosine similarity & distance
# 13 / (3.74 * 5) = 0.695
cosine_sim = dot / (len_a * len_b)
cosine_dist = 1 - cosine_sim

print("Dot:", dot)
print("Length a:", len_a, "Length b:", len_b)
print("Cosine similarity:", cosine_sim)
print("Cosine distance:", cosine_dist)

x = np.array([1, 1])
y = np.array([10, 10])
print("Same direction sim:", (x @ y) / (np.linalg.norm(x) * np.linalg.norm(y)))