import os
import unicodedata
import shutil


def safe_name(name: str) -> str:
    """
    Chuẩn hóa tên file/thư mục:
    - Bỏ dấu tiếng Việt
    - Thay 'Đ/đ' -> 'D/d'
    - Chỉ giữ chữ, số, '_'
    - Loại bỏ ký tự đặc biệt và khoảng trắng
    """
    normalized = unicodedata.normalize('NFD', name)
    no_accent = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    no_d = no_accent.replace('Đ', 'D').replace('đ', 'd')
    safe = ''.join(c if c.isalnum() or c == '_' else '_' for c in no_d)
    while '__' in safe:
        safe = safe.replace('__', '_')
    return safe.strip('_')


def rename_all(root_dir: str):
    """
    Đổi tên tất cả thư mục và file trong cây thư mục:
    - Xử lý đệ quy (dùng os.walk)
    - Giữ nguyên phần mở rộng file
    - Đảm bảo không ghi đè nếu tên mới đã tồn tại
    """
    # B1: Đổi tên thư mục từ dưới lên để tránh lỗi đường dẫn
    for folder_path, subdirs, files in os.walk(root_dir, topdown=False):
        # Đổi tên file trong folder hiện tại
        for file_name in files:
            name, ext = os.path.splitext(file_name)
            safe_file_name = safe_name(name) + ext.lower()
            old_file_path = os.path.join(folder_path, file_name)
            new_file_path = os.path.join(folder_path, safe_file_name)
            if safe_file_name != file_name:
                if not os.path.exists(new_file_path):
                    try:
                        os.rename(old_file_path, new_file_path)
                        print(f"✅ File: {file_name} → {safe_file_name}")
                    except Exception as e:
                        print(f"❌ Lỗi khi đổi tên file {file_name}: {e}")
                else:
                    print(f"⚠️ Bỏ qua file: {safe_file_name} đã tồn tại")

        # Đổi tên chính thư mục này (nếu cần)
        current_dir_name = os.path.basename(folder_path)
        parent_dir = os.path.dirname(folder_path)
        safe_dir_name = safe_name(current_dir_name)
        if safe_dir_name != current_dir_name:
            new_dir_path = os.path.join(parent_dir, safe_dir_name)
            if not os.path.exists(new_dir_path):
                try:
                    shutil.move(folder_path, new_dir_path)
                    print(f"✅ Folder: {current_dir_name} → {safe_dir_name}")
                except Exception as e:
                    print(f"❌ Lỗi khi đổi tên folder {current_dir_name}: {e}")
            else:
                print(f"⚠️ Bỏ qua folder: {safe_dir_name} đã tồn tại")


if __name__ == "__main__":
    root = r"E:\Data\Movie_Dataset\Film_Dataset"
    rename_all(root)
