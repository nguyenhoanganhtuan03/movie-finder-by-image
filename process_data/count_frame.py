import os

def count_images_per_folder(root_dir, image_extensions=None):
    if image_extensions is None:
        image_extensions = ['.jpg']

    total = 0
    for subdir, dirs, files in os.walk(root_dir):
        count = sum(1 for file in files if any(file.lower().endswith(ext) for ext in image_extensions))
        if count > 0:
            relative_path = os.path.relpath(subdir, root_dir)
            print(f"Thư mục '{relative_path}': {count} ảnh")
            total += count

    print(f"\nTổng số ảnh: {total}")

print("====Thư mục Train====")
folder_train_path = 'E:\\Data\\Movie_Dataset\\Process_Frames_1\\Train'
count_images_per_folder(folder_train_path)

print("====Thư mục Test====")
folder_test_path = 'E:\\Data\\Movie_Dataset\\Process_Frames_1\\Test'
count_images_per_folder(folder_test_path)

# Dataset 1: Train 51777-- Test 17011 - 3917 = 13094
# Dataset 2: Train 90750 -- Test 27860 - 3869 = 23991 --> Main

# Processed Dataset 1: Train 51210 -- Test 16864 - 3876 = 12988
# Processed Dataset 2: Train 89853 -- Test 27612 - 3869 = 23743