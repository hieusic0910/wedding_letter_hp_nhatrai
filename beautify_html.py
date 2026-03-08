from bs4 import BeautifulSoup
import sys
import os

def beautify_html(input_file, output_file=None):
    # Đọc file HTML gốc
    with open(input_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Parse bằng BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Làm đẹp
    pretty_html = soup.prettify()

    # Nếu không truyền output_file -> tự động tạo
    if not output_file:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_pretty{ext}"

    # Ghi ra file mới
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_html)

    print(f"✅ Đã làm đẹp HTML và lưu tại: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: python beautify_html.py <input.html> [output.html]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    beautify_html(input_path, output_path)
