import re
import json

def normalize_number(num: str) -> str:
    """Chuẩn hóa số: đổi , thành ., 83 -> 8.3"""
    num = num.replace(",", ".")
    if re.fullmatch(r"\d{2}", num):
        num = f"{num[0]}.{num[1]}"
    return num

VALID_SUBJECTS = [
    "Toán", "Ngữ văn", "Ngoại ngữ (Anh)", "Ngoại ngữ", 
    "Vật lý", "Hóa học", "Sinh học", "Lịch sử", "Địa lý",
    "Công nghệ", "Tin học", "GDCD", "GDQP", "Thể dục", "Nghề PT", "Điểm TB"
]

ALIASES = {
    "Anh": "Ngoại ngữ (Anh)",
    "Ngoại ngữ (Tiếng Anh)": "Ngoại ngữ (Anh)",
    "Ngoại ngữ": "Ngoại ngữ (Anh)",
    "Vật 1í": "Vật lý",
    "Địa 1í": "Địa lý",
    "nghệ": "Công nghệ",
    "Ơv nghệ": "Công nghệ",
    "CN": "Công nghệ",
    "Tin": "Tin học",
    "Sinh": "Sinh học",
    "GD CD": "GDCD"
}

def clean_subject_name(name: str) -> str:
    name = name.strip()
    if name in ALIASES:
        return ALIASES[name]
    return name

def is_valid_subject(name: str) -> bool:
    n = clean_subject_name(name)
    return any(n.startswith(s) for s in VALID_SUBJECTS)

def extract_grade_info(raw_text: str):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    data = {"Họ và tên": "", "Lớp": "", "Bảng điểm": []}

    current_subject, temp_scores = None, []

    # Lấy Họ và tên
    for line in lines:
        if re.search(r"họ\s*(?:và)?\s*tên", line, flags=re.IGNORECASE):
            name = re.sub(r"họ\s*(?:và)?\s*tên\s*:?", "", line, flags=re.IGNORECASE).strip()
            data["Họ và tên"] = name
            break

    # Lấy Lớp
    for line in lines:
        if re.search(r"lớp", line, flags=re.IGNORECASE):
            match = re.search(r"(\d{1,2}[A-Z]\d*)", line)
            if match:
                data["Lớp"] = match.group(1)
            break

    # Nhận dạng môn học & điểm
    for line in lines:
        if is_valid_subject(line):
            # lưu môn cũ
            if current_subject and temp_scores:
                data["Bảng điểm"].append({
                    "Tên môn": current_subject,
                    "Điểm": format_scores(temp_scores, current_subject)
                })
            # ghi môn mới
            current_subject = clean_subject_name(line)
            temp_scores = []
            continue

        # Nhận điểm
        nums = re.findall(r"\d+[.,]?\d*|Đ|CĐ", line)
        if nums and current_subject:
            for n in nums:
                if n in ["Đ", "CĐ"]:
                    if current_subject in ["Thể dục", "Nghề PT"]:
                        temp_scores.append(n)
                else:
                    temp_scores.append(normalize_number(n))

    # lưu môn cuối
    if current_subject and temp_scores:
        data["Bảng điểm"].append({
            "Tên môn": current_subject,
            "Điểm": format_scores(temp_scores, current_subject)
        })

    return data


def format_scores(scores, subject):
    if subject in ["Thể dục", "Nghề PT"]:
        return scores
    if len(scores) >= 3:
        return {"HK1": scores[0], "HK2": scores[1], "CN": scores[2]}
    return scores

# ---------------- MAIN ----------------
if __name__ == "__main__":
    input_txt = "bang_diem.txt"
    output_json = "bang_diem.json"

    with open(input_txt, "r", encoding="utf-8") as f:
        raw_text = f.read()

    data = extract_grade_info(raw_text)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Dữ liệu đã được lưu vào {output_json}")
