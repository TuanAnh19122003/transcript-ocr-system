import easyocr
import os
import re

def correct_class_numbers(text):
    text = re.sub(r'(?<=\d)[Il|](?=\d)', '1', text)

    if re.search(r'\b[Ll]ớp\b', text):
        parts = text.split()
        fixed_parts = []
        for p in parts:
            if re.match(r'\d+[A-Za-z]+\d+', p):
                m = re.match(r'(\d+)([A-Za-z]+)(\d+)', p)
                if m:
                    num1, letters, num2 = m.groups()
                    fixed_parts.append(f"{num1}{letters}{num2}")
                else:
                    fixed_parts.append(p)
            else:
                fixed_parts.append(p)
        return " ".join(fixed_parts)
    elif re.match(r'^\d+[A-Za-z]+\d+$', text):
        return "Lớp: " + text

    return text


def run_ocr(image_path, lang=["vi", "en"]):
    # 1. Kiểm tra file ảnh
    if not os.path.exists(image_path):
        print("Không tìm thấy ảnh:", image_path)
        return []
    
    # 2. Tạo reader
    print("Đang khởi tạo EasyOCR...")
    reader = easyocr.Reader(lang, gpu=False)
    
    # 3. Chạy OCR
    print("Đang đọc ảnh:", image_path)
    results = reader.readtext(
        image_path,
        detail=1,
        text_threshold=0.4,
        low_text=0.3,
        link_threshold=0.4
    )
    
    # 4. Hiển thị toàn bộ kết quả OCR
    print("\nKẾT QUẢ OCR (chưa sửa):")
    for bbox, text, prob in results:
        print(f"- {text}  (độ tin cậy: {prob:.2f})")

    # 5. Lọc theo ngưỡng 0.3 và hậu xử lý
    extracted_texts = []
    for bbox, text, prob in results:
        if prob >= 0.3:
            text = correct_class_numbers(text)  # ✅ sửa lỗi lớp
            extracted_texts.append(text)

    # 6. Lưu ra file
    with open("ocr_result.txt", "w", encoding="utf-8") as f:
        f.write("===== KẾT QUẢ VỚI NGƯỠNG 0.3 =====\n")
        f.write("\n".join(extracted_texts))
        f.write("\n")
    
    print("\nKết quả OCR đã lưu tại: ocr_result.txt")

    return extracted_texts


# --- MAIN ---
if __name__ == "__main__":
    input_path = "bang_diem_processed.jpg"
    run_ocr(input_path, lang=["vi", "en"])
