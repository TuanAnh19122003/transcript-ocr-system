import re
import json

def normalize_number(num: str) -> str:
    num = num.replace(",", ".")
    if re.fullmatch(r"\d{2}", num):  # 83 -> 8.3
        num = f"{num[0]}.{num[1]}"
    return num
def extract_grade_info(raw_text: str):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    data = {"Họ và tên": "", "Lớp": "", "Môn học": []}

    current_subject = None
    temp_scores = []

    # --- Gán Họ và tên một lần duy nhất ---
    for line in lines:
        if re.search(r"họ\s*(?:và)?\s*tên", line, flags=re.IGNORECASE):
            name = re.sub(r"họ\s*(?:và)?\s*tên\s*:?", "", line, flags=re.IGNORECASE).strip()
            data["Họ và tên"] = name
            break

    # --- Xử lý Lớp và Môn học ---
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # --- Lớp ---
        if re.match(r"lớp", line, flags=re.IGNORECASE):
            match = re.search(r"(\d{1,2}[A-Z]?\d*)", line)
            if match:
                data["Lớp"] = match.group(1)
            continue

        # --- Nếu là dòng điểm ---
        if re.fullmatch(r"[0-9., ]+", line):
            nums = re.findall(r"\d+[.,]?\d*", line)
            nums = [normalize_number(n) for n in nums]
            temp_scores.extend(nums)
            continue

        # --- Nếu là chữ (môn học), bỏ qua dòng Họ tên ---
        if re.search(r"[A-Za-zÀ-Ỵà-ỵ]", line) and not re.search(r"\d", line):
            if "họ" in line.lower() and "tên" in line.lower():
                continue  # bỏ qua dòng Họ và tên
            # Lưu môn trước nếu có điểm
            if current_subject and temp_scores:
                data["Môn học"].append((current_subject, temp_scores))
            current_subject = line
            temp_scores = []
            continue

        # --- Nếu là "Đ" (môn thể dục) ---
        if line == "Đ" and current_subject:
            temp_scores.append("Đ")

    # Lưu môn cuối cùng
    if current_subject and temp_scores:
        data["Môn học"].append((current_subject, temp_scores))

    return data

# ---------------- MAIN ----------------
if __name__ == "__main__":
    input_txt = "bang_diem.txt"
    output_json = "bang_diem.json"

    with open(input_txt, "r", encoding="utf-8") as f:
        raw_text = f.read()

    data = extract_grade_info(raw_text)

    # Ghi ra JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Dữ liệu đã được lưu vào {output_json}")
