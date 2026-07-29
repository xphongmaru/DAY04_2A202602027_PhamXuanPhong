# Tool: github

Tìm kiếm kho lưu trữ (repositories) trên GitHub để tìm mã nguồn hoặc dự án liên quan đến từ khóa.

## Arguments

* `query` (string, required): Từ khóa tìm kiếm (ví dụ: "machine learning", "fastapi").
* `limit` (integer, optional, default: 5): Số lượng kết quả tối đa cần lấy (tối đa 10).
* `sort` (string, optional, enum: [stars, forks, updated], default: "stars"): Sắp xếp theo số sao, số fork hoặc thời gian cập nhật.

## Response

Trả về danh sách các repository kèm theo mô tả, số stars, số forks, ngôn ngữ lập trình chính và URL liên kết.
