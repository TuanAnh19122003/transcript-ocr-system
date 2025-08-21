import easyocr
import os
import re
import json
import difflib

# --- Danh sách môn học chuẩn để fuzzy match ---
KNOWN_SUBJECTS = [
    "Toán học","Vật lý","Hóa học","Sinh học","Ngữ văn","Lịch sử","Địa lý",
    "Tiếng Anh","Ngoại ngữ","Tin học","GDQP","Thể dục","GDCD",
    "Công nghệ","Âm nhạc","Mỹ thuật","HĐ TN","Giáo dục địa phương",
    "GDKT&PL","KTCN"
]

# ========== CHUẨN HOÁ ==========
def normalize_subject_name(name: str) -> str:
    """Chuẩn hóa tên môn học bằng fuzzy match."""
    name = name.strip()
    if not name:
        return name
    match = difflib.get_close_matches(name, KNOWN_SUBJECTS, n=1, cutoff=0.65)
    return match[0] if match else name

def _normalize_class_token(tok: str) -> str:
    tok = tok.strip()
    tok = re.sub(r'[Il|]', '1', tok)
    tok = re.sub(r'[Oo]', '0', tok)
    if re.match(r'^[0-9]A[0-9]{2}$', tok):
        tok = "1" + tok
    if re.match(r'^[0-9]A[0-9]$', tok):
        tok = tok[0] + "2A1" + tok[-1]
    return tok

def correct_class_numbers(text: str) -> str:
    def repl_lop(m):
        token = m.group(1)
        fixed = _normalize_class_token(token)
        return f"Lớp: {fixed}"

    if re.search(r'(?:\bLớp\b|\blop\b)', text, re.IGNORECASE):
        return re.sub(
            r'(?:\bLớp\b|\blop\b)\s*[:：]?\s*([A-Za-z0-9Il|]+)',
            repl_lop, text, flags=re.IGNORECASE
        )

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
    return re.sub(r'\b\d{2}\b', fix_num, text)

def is_score_token(token: str) -> bool:
    token = token.strip()
    if re.match(r'^\d+(\.\d+)?$', token):
        return True
    if token.upper() in ["Đ", "CD", "CĐ", "DAT", "ĐẠT", "CHƯA ĐẠT"]:
        return True
    return False

# ========== TRÍCH XUẤT TÊN ==========
def extract_student_name(lines: list[str]) -> str | None:
    for idx, line in enumerate(lines):
        lower = line.lower()
        if "họ và tên" in lower or "tên học sinh" in lower or "học sinh" in lower:
            m = re.search(r'(?:họ và tên|tên học sinh|học sinh)\s*[:：]?\s*(.+)', line, flags=re.IGNORECASE)
            if m and m.group(1).strip():
                return m.group(1).strip().title()
            if idx + 1 < len(lines):
                next_line = lines[idx + 1].strip()
                if next_line:
                    return next_line.title()
    for line in lines:
        if re.match(r'^[A-ZĐ][a-zà-ỹ]+\s+[A-ZĐ][a-zà-ỹ]+', line):
            return line.strip().title()
    return None

# ========== PARSE ==========
def parse_ocr_results(lines: list[str]):
    data = {"name": extract_student_name(lines), "class": None, "subjects": []}

    # Lớp
    classes = []
    for line in lines:
        m = re.search(r'Lớp\s*[:：]?\s*([0-9A-Za-z]+)', line, flags=re.IGNORECASE)
        if m:
            classes.append(_normalize_class_token(m.group(1).strip()))
    if classes:
        data["class"] = max(classes, key=len)

    # Môn học + điểm
    subjects = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        subject_name = normalize_subject_name(line)
        j = i + 1
        scores = []

        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line or normalize_subject_name(next_line) in KNOWN_SUBJECTS or next_line.upper() == "ĐTB":
                break
            if is_score_token(next_line):
                if next_line.upper() in ["Đ", "CD", "CĐ", "DAT", "ĐẠT", "CHƯA ĐẠT"]:
                    scores.append(next_line.upper())
                else:
                    try:
                        scores.append(float(next_line))
                    except ValueError:
                        pass
            j += 1

        if scores:
            subj_data = {"subject": subject_name, "HK1": None, "HK2": None, "CN": None}
            if len(scores) >= 1: subj_data["HK1"] = scores[0]
            if len(scores) >= 2: subj_data["HK2"] = scores[1]
            if len(scores) >= 3: subj_data["CN"]  = scores[2]
            subjects.append(subj_data)

        i = j

    # Kiểm tra điểm trung bình (ĐTB) chỉ nếu chưa có
    if not any(s["subject"]=="ĐTB" for s in subjects):
        dtb_scores = []
        for idx, line in enumerate(lines):
            if line.strip().upper() == "ĐTB":
                j = idx + 1
                while j < len(lines):
                    token = lines[j].strip()
                    try:
                        dtb_scores.append(float(token))
                    except ValueError:
                        pass
                    j += 1
                break
        if dtb_scores:
            subjects.append({
                "subject": "ĐTB",
                "HK1": dtb_scores[0] if len(dtb_scores) > 0 else None,
                "HK2": dtb_scores[1] if len(dtb_scores) > 1 else None,
                "CN": dtb_scores[2] if len(dtb_scores) > 2 else None
            })

    data["subjects"] = subjects
    return data

# ========== OCR + HẬU XỬ LÝ ==========
def run_ocr(image_path, lang=["vi", "en"]):
    if not os.path.exists(image_path):
        print("Không tìm thấy ảnh:", image_path)
        return []
    print("Đang khởi tạo EasyOCR...")
    reader = easyocr.Reader(lang, gpu=False)
    print("Đang đọc ảnh:", image_path)
    results = reader.readtext(
        image_path,
        detail=1,
        text_threshold=0.4,
        low_text=0.3,
        link_threshold=0.4
    )

    print("\nKẾT QUẢ OCR (chưa sửa):")
    for bbox, text, prob in results:
        print(f"- {text}  (độ tin cậy: {prob:.2f})")

    extracted_texts = []
    for bbox, text, prob in results:
        if prob >= 0.5:
            text = correct_class_numbers(text)
            text = _normalize_scores(text)
            extracted_texts.append(text)

    with open("ocr_result.txt", "w", encoding="utf-8") as f:
        f.write("===== KẾT QUẢ VỚI NGƯỠNG 0.5 =====\n")
        f.write("\n".join(extracted_texts))
        f.write("\n")
    print("\nKết quả OCR đã lưu tại: ocr_result.txt")
    return extracted_texts

# ========== MAIN ==========
if __name__ == "__main__":
    input_path = "bang_diem_processed.jpg"
    lines = run_ocr(input_path, lang=["vi", "en"])
    parsed = parse_ocr_results(lines)

    print("\n=== DỮ LIỆU CẤU TRÚC ===")
    print(json.dumps(parsed, ensure_ascii=False, indent=2))

    with open("parsed_result.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    print("Đã lưu parsed_result.json")
