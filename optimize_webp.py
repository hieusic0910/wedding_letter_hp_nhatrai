from PIL import Image
import os

def optimize_images(input_folder, output_folder, quality=70, max_width=1200):
    """
    Nén & resize tất cả ảnh trong input_folder, lưu thành JPG ở output_folder.
    - quality: mức nén (0-100, thường 70-85 là đẹp)
    - max_width: resize theo chiều rộng tối đa (giữ tỉ lệ gốc)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            img = Image.open(file_path).convert("RGB")  # Convert RGB để tránh lỗi ảnh PNG có alpha

            # Resize nếu ảnh quá lớn
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Lưu dưới dạng JPG
            base_name, _ = os.path.splitext(filename)
            output_path = os.path.join(output_folder, f"{base_name}.jpg")

            img.save(output_path, "JPEG", quality=quality, optimize=True)
            print(f"✅ Đã nén: {filename} -> {output_path}")

        except Exception as e:
            print(f"❌ Lỗi với {filename}: {e}")
if __name__ == "__main__":
    input_folder = "C:/Users/ADMIN/Desktop/ANH DANG-20250811T155753Z-1-001/ANH DANG/1"   # Thư mục chứa ảnh gốc
    output_folder = "ziu_clone/img" # Thư mục lưu ảnh WebP
    optimize_images(input_folder, output_folder, quality=70, max_width=1200)
