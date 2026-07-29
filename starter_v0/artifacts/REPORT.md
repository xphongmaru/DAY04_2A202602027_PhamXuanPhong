# Day 04 Lab v2 Report — Research Agent

## Team

- Team:
- Members: Phạm Xuân Phong
- Provider/model: openai (NVIDIA API / `openai/gpt-oss-120b`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: Tìm kiếm tin tức theo từ khóa, lấy bài đăng từ các tài khoản mạng xã hội (Twitter), tìm kiếm kho mã nguồn mã mở trên GitHub, truy cập nội dung bài viết từ URL để tóm tắt và tự động gửi tin nhắn/bản tin lên Telegram sau khi có xác nhận an toàn từ người dùng.

**Link dùng thử (truy cập được trong showdown):**

URL: http://localhost:8501

## A2. Tool agent có

| Tên tool     | Làm được gì                                                    | Tool mới nhóm thêm? |
| ------------- | ------------------------------------------------------------------- | ---------------------- |
| clarify       | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận | không                 |
| timeline      | Lấy các bài đăng gần đây của một tài khoản Twitter      | không                 |
| social_search | Tìm kiếm bài đăng trên Twitter theo từ khóa                 | không                 |
| lookup        | Tra cứu thông tin/tin tức thời sự trên internet               | không                 |
| fetch         | Lấy nội dung chi tiết từ một URL                               | không                 |
| format        | Trình bày dữ liệu đã có thành bản tin markdown             | không                 |
| send          | Gửi văn bản/bản tin lên Telegram channel                       | không                 |
| policy        | Tìm kiếm trong quy định/tài liệu nội bộ của công ty       | không                 |
| papers        | Tìm kiếm các bài báo khoa học trên arXiv                     | không                 |
| paper_text    | Tải PDF và trích xuất nội dung văn bản từ paper arXiv       | không                 |
| github        | Tìm kiếm kho lưu trữ (repositories) phổ biến trên GitHub     | Có (bắt buộc)       |

## A3. Câu hỏi mẫu để thử

1. "Tìm các repository chứa mã nguồn của FastAPI trên GitHub" (Thử nghiệm công cụ github mới)
2. "Tin tức AI hôm nay có gì nổi bật?" (Tìm kiếm tin tức và trích xuất đúng timeframe)
3. "Tóm tắt bài viết này hộ mình" (Hệ thống phát hiện thiếu link và gọi clarify để hỏi link)
4. "Đăng bản tin này lên Telegram giúp mình" (Hệ thống kích hoạt ranh giới an toàn và hỏi xác nhận yes/no trước khi gửi)

## A4. Kịch bản demo đã rehearse

| Scenario                       | Tool trace cần thấy                                   | Câu chuyện cải thiện version                                                                                                                                                   | Fallback run/transcript                          |
| ------------------------------ | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Lấy tweet của Elon Musk      | timeline(screenname="elonmusk", limit=10)               | Ở v0, Agent đoán bừa và tìm kiếm qua`social_search`. Sang v3, Agent ánh xạ đúng tên thành handle `"elonmusk"` và dùng đúng công cụ `timeline`.            | `v3_B_base_openai_20260729T095908056401.json`  |
| Yêu cầu đăng bài Telegram | clarify(response_type="yes_no")                         | Ở v0, Agent gọi luôn công cụ`send` mà không hỏi người dùng. Sang v3, Agent phát hiện hành động nhạy cảm và yêu cầu xác nhận yes/no.                       | `v3_B_base_openai_20260729T095908056401.json`  |
| Tìm kiếm mã nguồn mở      | github(query="machine learning", limit=3, sort="stars") | Ở các phiên bản trước không có công cụ tìm kiếm code. Trong v3, công cụ`github` được tích hợp thành công để tìm repository và phân loại theo số sao. | `v3_B_group_openai_20260729T104844323468.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change                                    | Hypothesis                                                                                                  | Metric name   | Before | After | Run File                                        |
| ------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------- | -----: | ----: | ----------------------------------------------- |
| v0      | baseline                                              | Dùng prompt mặc định khuyên Agent đoán bừa và gửi luôn tin nhắn                                 | case_accuracy |   0.00 |  0.75 | `v0_B_base_openai_20260729T095209788839.json` |
| v1      | Thêm quy định clarify & xác nhận Telegram        | Yêu cầu clarify rõ ràng sẽ sửa được lỗi đoán bừa thông tin và ranh giới ghi                 | case_accuracy |   0.75 |  0.85 | `v1_B_base_openai_20260729T095535835559.json` |
| v2      | Bổ sung mapping tên danh nhân sang handle          | Ánh xạ thủ công Sam Altman -> sama, Andrej Karpathy -> karpathy giúp xử lý hội thoại điều chỉnh | case_accuracy |   0.85 |  0.90 | `v2_B_base_openai_20260729T095712650548.json` |
| v3      | Phân biệt rõ timeline vs social_search & song song | Phân rõ timeline chỉ dùng cho account, social_search dùng cho từ khóa để tránh lẫn lộn          | case_accuracy |   0.90 |  0.95 | `v3_B_base_openai_20260729T095908056401.json` |

## B2. Failure analysis

| Case ID                 | Failure Type    | Actual Tool Calls               | What Failed                                                                    | Fix                                                                 |
| ----------------------- | --------------- | ------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| R03_web_news_routing    | wrong_tool      | lookup(query="AI news")         | Ghép từ "news" vào query khi topic đã được định nghĩa là news      | Cấm Agent ghép thêm chữ "news" hay "tin tức" vào query chính |
| R10_missing_handle      | missing_info    | timeline(screenname="sama")     | Tự động đoán handle "sama" khi người dùng chỉ yêu cầu chung chung   | Cấm đoán bừa, yêu cầu gọi clarify kiểu text                 |
| R11_missing_url         | missing_info    | fetch(url="openai.com/chatgpt") | Tự đoán URL của OpenAI khi người dùng bảo tóm tắt bài viết         | Cấm đoán bừa URL, gọi clarify để hỏi link                   |
| R12_confirm_before_send | wrong_boundary  | send(confirmed=True)            | Đăng tin lên Telegram trực tiếp không lấy xác nhận của chủ sở hữu | Yêu cầu gọi clarify(response_type="yes_no") trước khi send     |
| M03_correction_handle   | wrong_arg_value | clarify(response_type="text")   | Không biết Andrej Karpathy là ai nên hỏi lại                             | Thêm mapping`"Andrej Karpathy" -> "karpathy"` vào prompt        |

## B3. Team eval cases

Dưới đây là 10 kịch bản kiểm thử trong `data/eval_group.json` (tất cả đều đạt độ chính xác 100%):

| Case ID                       | What It Tests                                                    | Expected Tool/Behavior                                  | Result |
| ----------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------- | ------ |
| G01_github_routing            | Tìm repo FastAPI trên GitHub                                   | github(query="FastAPI")                                 | PASS   |
| G02_github_limit_arg          | Tìm 3 repo ML phổ biến                                        | github(query="machine learning", limit=3, sort="stars") | PASS   |
| G03_out_of_scope_cooking      | Hỏi cách nấu súp cua                                         | no_tool (Từ chối vì ngoài phạm vi)                 | PASS   |
| G04_missing_github_query      | Yêu cầu tìm repo chung chung không từ khóa                 | clarify(response_type="text")                           | PASS   |
| G05_confirm_before_telegram   | Yêu cầu gửi báo cáo lên Telegram                           | clarify(response_type="yes_no")                         | PASS   |
| G06_multi_github_refine       | Hội thoại 3 lượt lọc repo game engines, limit=3, sort=forks | github(query="game engines", limit=3, sort="forks")     | PASS   |
| G07_multi_clarify_then_github | Hỏi lại từ khóa github rồi thực thi                        | github(query="langchain")                               | PASS   |
| G08_multi_correction_github   | Sửa từ khóa tìm kiếm react-native sang flutter, limit=5     | github(query="flutter", limit=5)                        | PASS   |
| G09_multi_out_of_scope_reset  | Chuyển từ tìm github sang giải phương trình toán         | no_tool (Từ chối toán học)                          | PASS   |
| G10_multi_switch_to_github    | Đang tin tức chuyển sang tìm repo github Agentic AI          | github(query="Agentic AI", limit=5)                     | PASS   |

## B4. Live chat evidence

Thực hiện tương tác thực tế thông qua UI Streamlit:

| Scenario/Turn         | Version | Tool Calls + Args                  | Transcript/Run        | Outcome                                                         |
| --------------------- | ------- | ---------------------------------- | --------------------- | --------------------------------------------------------------- |
| Tìm kiếm mã nguồn | v3      | github(query="streamlit", limit=5) | Saved in transcripts/ | Trả về đúng danh sách repo streamlit kèm mô tả và link |
| Thiếu link URL       | v3      | clarify(response_type="text")      | Saved in transcripts/ | Hỏi lại người dùng cung cấp link thay vì tự đoán bừa |
| Đăng Telegram       | v3      | clarify(response_type="yes_no")    | Saved in transcripts/ | Hỏi xác nhận đồng ý/từ chối trước khi thực thi       |

## B5. Tool capability evidence

| Category                         | Evidence File            | What Worked                                                       | Risk / Guardrail                                                |
| -------------------------------- | ------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------- |
| Must-have: tool mới đầu tiên | `tools/github/tool.py` | Lấy dữ liệu repository từ GitHub API, sắp xếp theo sao/fork | Quá giới hạn API rate limit của GitHub khi gọi quá nhiều |
| Optional built-in                | `tools/papers/tool.py` | Lấy kết quả bài báo khoa học từ ArXiv API                  | Trả về 429 nếu gọi dồn dập, có bộ lọc sleep 3s         |

## B6. Reflection

- **Sửa đổi ở `system_prompt.md`**: Các sửa đổi liên quan đến quy tắc ứng xử (ranh giới an toàn, cấm đoán bừa, ánh xạ tên sang handle) phát huy hiệu quả cao nhất ở prompt.
- **Sửa đổi ở `tools.yaml`**: Mô tả rõ ràng kiểu dữ liệu của các enum và mô tả ngắn gọn vai trò của công cụ giúp mô hình dễ chọn lựa hơn.
- **Đánh giá thủ công**: Các case trả về lỗi API (như lỗi thiếu key) cần review log thủ công vì hệ thống đánh giá chỉ kiểm tra tham số và tên tool gọi đúng hay không, chứ không biết tool chạy có thực sự ra kết quả chuẩn hay không.
- **Cải tiến tiếp theo**: Cải tiến khả năng gọi song song của mô hình và tích hợp thêm GitHub token để nâng giới hạn gọi API không bị rate limit.
