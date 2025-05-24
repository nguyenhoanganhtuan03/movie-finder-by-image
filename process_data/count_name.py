import os

# Đường dẫn đến thư mục cha
folder_path = "E:\\Data\\Movie_Dataset\\Film_Cut_Dataset"

# Lấy danh sách thư mục con
subfolders = [
    f for f in os.listdir(folder_path)
    if os.path.isdir(os.path.join(folder_path, f))
]

# In số lượng thư mục con
print(f"Số lượng thư mục con: {len(subfolders)}")

# In tên từng thư mục
for folder_name in subfolders:
    print(folder_name)