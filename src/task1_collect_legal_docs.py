"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
MIN_DOCUMENTS = 3
MIN_SIZE_BYTES = 1024

# Chủ đề: du lịch văn hóa ẩm thực Hà Nội. "url" = link tải trực tiếp PDF/DOCX;
# để None với file đã tải thủ công (trang nguồn chặn bot hoặc chỉ có landing page).
SOURCES = {
    "Hanoi_Culture_of_Cuisine_as_Factor_Attracting_Tourists_to_Vietnam.pdf": {
        "citation": "Nguyen Hoang Tien, Conference 'Values of Cuisine Culture in "
        "Tourist Activities', Tien Giang University, 21/05/2018",
        "url": None,
    },
    "MOT_SO_YEU_TO_ANH_HUONG_DEN_PHAT_TRIEN_DU_LICH_AM_.pdf": {
        "citation": "Tạp chí KH&CN Trường ĐH Hùng Vương, Tập 36 Số 3 (2024), "
        "DOI 10.59775/1859-3968.214",
        "url": None,
    },
    "am_thuc_ha_noi.pdf": {
        "citation": "Lã Tiến Dũng, 'Nghiên cứu phát triển du lịch ẩm thực tại "
        "Hà Nội', Tạp chí Công Thương",
        "url": None,
    },
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def _is_valid_document(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > MIN_SIZE_BYTES


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    import requests

    for filename, source in SOURCES.items():
        target = DATA_DIR / filename
        if _is_valid_document(target):
            print(f"Present: {filename} ({source['citation']})")
            continue
        if not source["url"]:
            print(f"Missing: {filename} — tải thủ công từ: {source['citation']}")
            continue
        response = requests.get(source["url"], timeout=30)
        response.raise_for_status()
        # Chặn trường hợp server trả trang HTML (login/WAF) thay vì file thật.
        if not response.content.startswith((b"%PDF", b"PK")):
            print(f"Skip: {filename} — response is not a PDF/DOCX")
            continue
        target.write_bytes(response.content)
        print(f"Downloaded: {filename}")

    documents = [
        path for path in DATA_DIR.iterdir()
        if path.suffix.lower() in {".pdf", ".doc", ".docx"} and _is_valid_document(path)
    ]
    if len(documents) < MIN_DOCUMENTS:
        raise RuntimeError(
            f"Cần ≥{MIN_DOCUMENTS} tài liệu PDF/DOCX >1KB, hiện có {len(documents)}"
        )
    print(f"OK: {len(documents)} documents in {DATA_DIR}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
