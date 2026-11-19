# Nhiệm vụ 1.6 (D): Bộ chẩn đoán baseline M1 và hàm tìm nút gốc

Thư mục này gồm đủ 3 phần: **môi trường** (script cài đặt), **giao diện** (ứng dụng Streamlit) và **sản phẩm** theo nhiệm vụ (`diagnosis/` + `tests/test_diagnosis.py`). Dữ liệu là đồ thị thật của nhóm: 70 khái niệm, 119 cạnh `REQUIRES`.

## 1. Cài môi trường (làm 1 lần)

Mở thư mục này trong VS Code, mở Terminal (`` Ctrl + ` ``) rồi gõ:

**Windows**
```powershell
.\setup_env.ps1
```
Nếu báo *"running scripts is disabled"*: chạy `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` rồi chạy lại.

**macOS / Linux**
```bash
bash setup_env.sh
```

Script sẽ tạo `.venv`, cài thư viện trong `requirements.txt`, rồi tự in bảng kiểm tra nhiệm vụ. Kết quả đúng là `Ket qua: 13/13 yeu cau dat.`

## 2. Mở giao diện

```powershell
.\run_app.ps1          # macOS/Linux: bash run_app.sh
```

Trình duyệt sẽ mở `http://localhost:8501`. Muốn tắt thì bấm `Ctrl + C` trong Terminal.

| Khu vực | Làm được gì |
| --- | --- |
| Thanh bên: **Đồ thị tiên quyết** | Lấy đồ thị từ `data/`, tải file lên, hoặc đọc thẳng từ Neo4j của nhóm (`bolt://localhost:7687`) |
| Thanh bên: **Tham số M1** | Ngưỡng vững, prior a₀/b₀, chế độ `direct`/`ancestors`, chia đều trọng số |
| **1. Bài làm**: Kịch bản mẫu | Chọn sinh viên mẫu, hoặc tự thêm lỗ hổng gốc |
| **1. Bài làm**: Nhập tay | Sửa số câu và số câu đúng của từng khái niệm (số câu = 0 nghĩa là không có trong đề) |
| **1. Bài làm**: Tải file CSV | Q-matrix + bài làm thật (khi C có dữ liệu), hoặc file mẫu |
| **2. Kết luận** | Một dòng kết luận: sinh viên vững hay chưa vững, lỗ hổng gốc nào cần học trước; 4 ô số liệu |
| **3. Đồ thị tiên quyết** | Vẽ bằng SVG (mặc định) hoặc Graphviz; tô đỏ/vàng/xanh/xám, đường đỏ là dấu vết bằng chứng; tải hình SVG |
| **4. Chi tiết**: Công thức và cách tính | Công thức M1 và bảng từng khái niệm: số câu, số đúng, α, β, phép tính, so với ngưỡng, kết luận |
| **4. Chi tiết**: Lỗ hổng gốc / Tải kết quả | Câu sai, tiên quyết đã vững, đường đi; tải JSON, CSV, báo cáo văn bản |

## 3. Chạy test

```powershell
.\run_tests.ps1        # macOS/Linux: bash run_tests.sh
```

Kết quả đúng: `58 passed, 1 skipped`. Test bị bỏ qua là test so khớp với `scripts/init_db.py` của B; nó chỉ chạy khi thư mục này nằm trong repo nhóm.

## 4. Đối chiếu yêu cầu nhiệm vụ 1.6

| Yêu cầu | Ở đâu | Kiểm tra |
| --- | --- | --- |
| B1. Giao diện `diagnose(responses, Q, G) -> {mastery, weak, roots, evidence}` | `diagnosis/api.py` | `check_task.py` mục Bước 1 |
| B1. `evidence` của mỗi nút gốc: câu sai liên quan + đường đi trên đồ thị | `diagnosis/api.py` (khóa `wrong_items`, `paths`, `explains`) | Bước 1 |
| B2. M1: trung bình hậu nghiệm Beta-Binomial, "yếu" khi dưới ngưỡng | `diagnosis/m1.py` | Bước 2 |
| B3. Outer fringe: chưa vững mà mọi tiên quyết đều vững | `diagnosis/roots.py` (`find_roots`, `rank_roots`) | Bước 3 |
| B4. Unit test đồ thị đồ chơi 10 nút, 5 ca dựng tay | `tests/conftest.py`, `tests/test_diagnosis.py` | Bước 4: **5/5** |
| Không nhúng cứng ngưỡng 0,6 | `M1Params(threshold=...)`, thanh trượt trên giao diện | Mục "Không nên" |
| Sản phẩm: `diagnosis/` + `tests/test_diagnosis.py` | Có | Mục "Sản phẩm" |

**Ngoài yêu cầu, có sẵn cho các bước sau:**
- **Đọc đồ thị của nhóm** (`diagnosis/io.py`): từ CSV, từ `init_db.py` hoặc từ Neo4j. Các hàm tự đảo chiều `REQUIRES`.
- **Đọc Q-matrix và bài làm từ CSV** (`load_q_csv`, `load_responses_csv`): dùng ngay khi có dữ liệu ở nhiệm vụ 2.3 và 3.5.
- **`diagnose_batch`**: chẩn đoán nhiều sinh viên cùng lúc, cho `run_sim.py` ở nhiệm vụ 2.5.
- **`p_mastered`** trong `details`: điểm số để vẽ ROC chọn ngưỡng ở GĐ3.

## 5. Cấu trúc thư mục

```
D_nhiem_vu_1.6/
├── diagnosis/             SẢN PHẨM CHÍNH
│   ├── api.py             diagnose(), diagnose_batch()
│   ├── m1.py              M1Params, Beta-Binomial
│   ├── roots.py           find_roots (outer fringe), rank_roots, explained_by
│   ├── qmatrix.py         chuẩn hóa Q, kiểm tra DAG, graph_from_requires
│   ├── io.py              đọc concepts/edges/Q/bài làm từ CSV, init_db.py, Neo4j
│   ├── report.py          báo cáo văn bản tiếng Việt
│   ├── verdict.py         kết luận tổng cho một sinh viên
│   └── viz.py             vẽ đồ thị (SVG, DOT), bảng tính từng bước, JSON
├── tests/
│   ├── conftest.py        đồ thị đồ chơi 10 nút
│   ├── test_diagnosis.py  5 ca dựng tay + các bẫy dễ mắc   (sản phẩm theo nhiệm vụ)
│   ├── test_real_graph.py chạy trên đồ thị thật 70 khái niệm
│   ├── test_io_viz.py     đọc CSV, vẽ đồ thị
│   └── test_app_smoke.py  chạy thử giao diện bằng Streamlit giả lập
├── app/d_app.py           GIAO DIỆN Streamlit
├── scripts/
│   ├── check_task.py      bảng kiểm tra 13 yêu cầu nhiệm vụ 1.6
│   ├── demo_diagnosis.py  demo trong Terminal
│   ├── export_edges.py    xuất cạnh từ init_db.py của B ra data/edges_v0.csv
│   └── make_demo_data.py  sinh dữ liệu mẫu
├── data/
│   ├── concepts_v0.csv    bản sao từ B (70 khái niệm)
│   ├── edges_v0.csv       119 cạnh REQUIRES
│   └── samples/           Q_demo.csv, responses_demo.csv (dữ liệu GIẢ)
├── requirements.txt
├── setup_env.ps1 / .sh    cài môi trường
├── run_app.ps1 / .sh      mở giao diện
└── run_tests.ps1 / .sh    chạy test + bảng kiểm tra
```

## 6. Ghép vào repo nhóm

Chép `diagnosis/`, `tests/`, `app/`, `scripts/check_task.py`, `scripts/demo_diagnosis.py`, `scripts/export_edges.py`, `scripts/make_demo_data.py`, `data/edges_v0.csv`, `data/samples/` vào thư mục gốc của repo.

**Không chép** `data/concepts_v0.csv` (repo đã có bản của B). Thêm `scipy`, `pytest`, `streamlit` vào `requirements.txt` của nhóm.

Khi B sửa cạnh trong `init_db.py`, chạy lại `python scripts/export_edges.py`.

## 7. Lưu ý

- **Q-matrix trong kịch bản mẫu và `data/samples/` là giả** (mỗi khái niệm 2 câu). Q thật là sản phẩm của C ở nhiệm vụ 2.3.
- **`mastery` = trung bình hậu nghiệm**, theo bước 2 của nhiệm vụ. Bước 1 lại gọi `mastery` là "xác suất đã vững", và đại lượng đó nằm ở `details[...]["p_mastered"]`. Nhóm nên chốt một cách gọi và ghi vào báo cáo.
- **Phiên bản trong `requirements.txt` chưa được cài thử** trên máy làm sản phẩm (máy không có mạng). Nếu `pip install` báo lỗi phiên bản với Python của bạn, bỏ phần `==...` của thư viện báo lỗi rồi cài lại, sau đó ghim lại bằng `pip freeze`.
