import cv2
import numpy as np

def sharpen_image(image, alpha=1.5, beta=-0.5):
    """Làm nét ảnh nhẹ nhàng."""
    blurred = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, alpha, blurred, beta, 0)
    return sharpened

def normalize_text_thickness(image):
    """Giảm độ dày của chữ quá đậm, giữ chi tiết cho OCR."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)

def deskew_image(image):
    """Căn chỉnh nghiêng dựa trên HoughLines."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    gray = cv2.bitwise_not(gray)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
    if lines is None:
        return image
    angles = [(theta - np.pi/2) * 180/np.pi for rho, theta in lines[:, 0]]
    median_angle = np.median(angles)
    if abs(median_angle) < 3 or abs(median_angle) > 15:
        return image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    return cv2.warpAffine(image, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)

def auto_rotate_image(image):
    """Xoay dọc nếu ảnh nằm ngang và deskew."""
    h, w = image.shape[:2]
    if w > h:
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return deskew_image(image)

def has_score_table(image, threshold_ratio=0.02):
    """Kiểm tra trang có bảng điểm dựa trên mật độ chữ."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 35, 15)
    black_pixels = np.sum(thresh > 0)
    total_pixels = thresh.shape[0] * thresh.shape[1]
    ratio = black_pixels / total_pixels
    return ratio > threshold_ratio

def remove_stamp(image):
    """Loại bỏ dấu đỏ bằng inpainting."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    return result

def preprocess_scorecard(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Không tìm thấy ảnh: {input_path}")

    # Xoay & deskew
    img = auto_rotate_image(img)

    # Kiểm tra có bảng điểm
    if not has_score_table(img):
        print("Trang không có bảng điểm, bỏ qua.")
        return

    # Loại bỏ dấu đỏ
    img = remove_stamp(img)

    # Giảm độ đậm chữ + làm nét
    img = normalize_text_thickness(img)
    img = sharpen_image(img)

    # Lưu ảnh chuẩn OCR
    cv2.imwrite(output_path, img)
    print(f"Ảnh đã xử lý được lưu tại: {output_path}")

if __name__ == "__main__":
    input_file = "data/034307009675_school_10_transcript_file.jpg"
    output_file = "bang_diem_processed.jpg"
    preprocess_scorecard(input_file, output_file)
