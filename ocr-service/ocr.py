import easyocr
import cv2
import re

def read_scorecard(image_path, lang_list=['vi', 'en']):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

    reader = easyocr.Reader(lang_list, gpu=False)
    results = reader.readtext(img)

    extracted_text = "\n".join([text for bbox, text, conf in results])
    return extracted_text

def correct_class_numbers(text):
    # Sửa ký tự 1 bị nhận nhầm
    text = re.sub(r'[Il|]', '1', text)

    def fix_match(match):
        s = match.group()
        m = re.match(r'(\d+)([A-Za-z]+)(\d+)', s)
        if m:
            num1, letters, num2 = m.groups()
            return f"{num1}{letters}{num2}"
        return s
    
    pattern = r'\d+[A-Za-z]+\d+'
    corrected_text = re.sub(pattern, fix_match, text)

    # Thêm từ "Lớp" nếu phát hiện số lớp học đứng một mình
    corrected_text = re.sub(r'(?m)^(?P<class>\d+[A-Za-z]+\d+)$', r'Lớp: \g<class>', corrected_text)

    return corrected_text



def save_text_to_file(text, output_txt_path):
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Văn bản OCR đã được lưu tại: {output_txt_path}")

if __name__ == "__main__":
    processed_file = "bang_diem_processed.jpg"
    output_txt_file = "bang_diem.txt"

    text = read_scorecard(processed_file)
    text = correct_class_numbers(text)
    save_text_to_file(text, output_txt_file)
