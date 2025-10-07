import pandas as pd
import numpy as np

# Đọc dữ liệu từ file CSV (ví dụ tên: report.csv)
df = pd.read_csv("models_audio/features_faiss/densenet201/classification_report_faiss.csv")

# Loại bỏ các dòng không phải class
exclude = ["accuracy", "macro avg", "weighted avg"]
class_df = df[~df.iloc[:,0].isin(exclude)].copy()

# Lấy các cột quan trọng
f1_scores = class_df["f1-score"].astype(float)
precision = class_df["precision"].astype(float)
recall = class_df["recall"].astype(float)
support = class_df["support"].astype(float)

# ----- Macro F1 -----
macro_f1 = f1_scores.mean()

# ----- Weighted F1 -----
weighted_f1 = np.average(f1_scores, weights=support)

# ----- Micro F1 -----
# Với multi-class đơn nhãn, micro F1 = accuracy = (tổng TP / tổng mẫu)
# Nên có thể lấy từ bảng (cột accuracy) hoặc tính lại từ recall * support
total_samples = support.sum()
micro_recall = np.sum(recall * support) / total_samples
micro_precision = np.sum(precision * support) / total_samples
micro_f1 = (2 * micro_precision * micro_recall) / (micro_precision + micro_recall)

print("Macro F1-score   :", macro_f1)
print("Weighted F1-score:", weighted_f1)
print("Micro F1-score   :", micro_f1)
