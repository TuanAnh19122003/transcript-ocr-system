import easyocr
import os
import re

def _normalize_class_token(tok: str) -> str:
    tok = tok.strip()
    m = re.match(r'^([0-9Il|]+)([A-Za-z0O48Bb]+)([0-9Il|]+)$', tok)
    if not m:
        return tok

    left, mid, right = m.groups()

    left  = re.sub(r'[Il|]', '1', left)
    right = re.sub(r'[Il|]', '1', right)

    mid_up = mid.upper()
    if re.fullmatch(r'[40]+', mid_up):
        mid_letter = 'A'
    elif re.fullmatch(r'[8]+', mid_up):
        mid_letter = 'B'
    else:
        letters_only = ''.join(ch for ch in mid_up if ch.isalpha())
        mid_letter = letters_only[0] if letters_only else 'A'

    return f"{left}{mid_letter}{right}"


def correct_class_numbers(text: str) -> str:
    def repl_lop(m):
        token = m.group(1)
        fixed = _normalize_class_token(token)
        return f"Lớp: {fixed}"
    
    if re.search(r'(?:\bLớp\b|\blop\b)', text, re.IGNORECASE):
        return re.sub(r'(?:\bLớp\b|\blop\b)\s*[:：]?\s*([A-Za-z0-9Il|]+)', repl_lop, text, flags=re.IGNORECASE)

    only = text.strip()
    if re.fullmatch(r'[0-9Il|]+[A-Za-z0O48Bb]+[0-9Il|]+', only):
        return "Lớp: " + _normalize_class_token(only)

    return text

def _normalize_scores(text: str) -> str:
    text = re.sub(r'(\d),(\d)', r'\1.\2', text)
    def fix_num(m):
        val = m.group(0)
        if len(val) == 2 and val.isdigit():
            num = int(val)
            if 0 < num <= 10:
                return f"{val[0]}.{val[1]}"
        return val

    text = re.sub(r'\b\d{2}\b', fix_num, text)

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
    
    # 4. Hiển thị toàn bộ kết quả OCR thô
    print("\nKẾT QUẢ OCR (chưa sửa):")
    for bbox, text, prob in results:
        print(f"- {text}  (độ tin cậy: {prob:.2f})")

    # 5. Lọc theo ngưỡng 0.3 và hậu xử lý
    extracted_texts = []
    for bbox, text, prob in results:
        if prob >= 0.3:
            text = correct_class_numbers(text)
            text = _normalize_scores(text)
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
