import os
import unicodedata
import shutil


def safe_folder_name(name):
    # Chuẩn hóa chuỗi và loại bỏ dấu
    normalized = unicodedata.normalize('NFD', name)
    no_accent = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

    # Thay thế chữ Đ thành D
    no_d = no_accent.replace('Đ', 'D').replace('đ', 'd')

    # Loại bỏ ký tự đặc biệt, chỉ giữ lại chữ cái, số và dấu gạch dưới
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in no_d)
    return safe_name


def rename_all_subfolders(root_dir):
    for dir_name in os.listdir(root_dir):
        full_path = os.path.join(root_dir, dir_name)
        if os.path.isdir(full_path):
            safe_name = safe_folder_name(dir_name)
            if safe_name != dir_name:
                new_path = os.path.join(root_dir, safe_name)
                if not os.path.exists(new_path):
                    try:
                        shutil.move(full_path, new_path)
                        print(f"✅ Đổi tên: {dir_name} → {safe_name}")
                    except Exception as e:
                        print(f"❌ Lỗi khi đổi tên {dir_name}: {e}")
                else:
                    print(f"⚠️ Bỏ qua: {safe_name} đã tồn tại")


rename_all_subfolders('E:\\Data\\Film_Cut_Dataset')
