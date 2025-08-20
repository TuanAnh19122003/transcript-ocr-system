import re

# Từ điển chuẩn hóa tên môn học
SUBJECT_MAP = {
    "Toán học": "Toán học",
    "Vật 1í": "Vật lý",
    "Hóa học": "Hóa học",
    "Sinh học": "Sinh học",
    "Tin học": "Tin học",
    "Ngữ văn": "Ngữ văn",
    "Lịch sử": "Lịch sử",
    "Địa 1í": "Địa lý",
    "Ngoại ngữ": "Tiếng Anh",
    "GDCD": "GDCD",
    "Công nghệ": "Công nghệ",
    "Thể dục": "Thể dục",
    "GDQP": "GDQP",
}

def clean_text(text):
    # Xóa ký tự rác
    text = re.sub(r'[\[\]{}%UJmouOe//]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_scores(text):
    """
    Chuẩn hóa điểm: nếu OCR thành 83 -> 8.3
    """
    def fix_score(match):
        s = match.group()
        try:
            val = int(s)
            if 80 <= val <= 99:  # ví dụ 83 -> 8.3
                return f"{str(val)[0]}.{str(val)[1]}"
            elif val <= 10:
                return str(val)
            return s
        except:
            return s
    return re.sub(r'\b\d{1,2}\b', fix_score, text)

def normalize_subjects(text):
    for wrong, correct in SUBJECT_MAP.items():
        text = text.replace(wrong, correct)
    return text

def extract_scores(text):
    """
    Tách thành danh sách (môn, HK1, HK2, CN)
    """
    lines = text.split("\n")
    data = []
    for line in lines:
        parts = line.split()
        for subj in SUBJECT_MAP.values():
            if subj in line:
                numbers = re.findall(r'\d\.\d|\d', line)
                if len(numbers) >= 3:
                    hk1, hk2, cn = numbers[:3]
                else:
                    hk1 = hk2 = cn = ""
                data.append([subj, hk1, hk2, cn])
                break
    return data

if __name__ == "__main__":
    with open("bang_diem.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    text = clean_text(raw_text)
    text = normalize_scores(text)
    text = normalize_subjects(text)
    
    # Xuất dữ liệu dạng bảng
    scores = extract_scores(text)

    print("===== Bảng điểm chuẩn hóa =====")
    for row in scores:
        print(row[0], row[1], row[2], row[3])
