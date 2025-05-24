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
folder_train_path = 'E:\\Data\\Movie_Dataset\\Extract_Frames_1\\Train'
count_images_per_folder(folder_train_path)

print("====Thư mục Test====")
folder_test_path = 'E:\\Data\\Movie_Dataset\\Extract_Frames_1\\Test'
count_images_per_folder(folder_test_path)

# Dataset 1: Train 56899 -- Test 32553 - 3454 = 29099
# Dataset 2: Train 81601 -- Test 25607 - 3997 = 21610

# Processed Dataset 1: Train 56899 -- Test 13813 - 1972 = 11841
# Processed Dataset 2: Train 80617 -- Test 25341 - 3919  = 21422