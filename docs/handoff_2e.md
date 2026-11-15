# Handoff — PLAN 2e (15/11 15:10), Fable 5.2

Người viết: Fable 5.2, theo ủy quyền toàn quyền của Bảo (bỏ cổng 1, mặc kệ Code Freeze).
Mục tiêu người dùng đặt: 45/50. Chấm thật hiện tại ≈ 38/50 (xem cuối file). File này để một
phiên khác tiếp tục được nếu phiên này hết quota giữa chừng.

## 1. Trạng thái repo

- `main` = `68504ad` (đã merge PR #7, PLAN 2d). Nhánh làm việc: `bao/terrain-engine`, HEAD
  `889a46b` (= main + 1 commit sửa chữ đã nằm trong PR #7).
- **Chưa commit** (chu kỳ 2e đang làm): `scripts/l1_regions.py`, `scripts/cross_dem.py`,
  `scripts/null_expand.py`, 5 bảng mới trong `scripts/report_tables.py`, mục §1 "Checks against
  known truth" và §7c + Deviations 28–29 trong `docs/validation_report.md`,
  `data/derived/{l1_regions.json,l1_regions.parquet,l1_lunar_control.parquet,l1_prevalence.parquet,nasa_slope_check.parquet,cross_dem.parquet}`.
- **Đang chạy nền:** `scripts/null_expand.py --n 800 --workers 32` (tải DEM Copernicus cho 800
  ô đất trống ngẫu nhiên mới; ~18 ô/phút; chip cache ở `data/raw/earth/chips/`, chạy lại không
  mất). Xong sẽ sinh `data/derived/earth_L1_null2.parquet` và `earth_L1_null2_L60.parquet`.
- Lỗi lint còn lại trong `scripts/report_tables.py`: F541 dòng ~445 (f-string không có biến),
  E501 dòng ~590.

## 2. Kết quả đã có của chu kỳ 2e (đều đọc từ bảng, hậu nghiệm)

| Kiểm tra | Kết quả | Ý nghĩa |
|---|---|---|
| Công thức độ dốc của ta so với raster độ dốc PGDA 78 của NASA (5 m, 6 vùng) | lệch tối đa 0,0009° và 0,004 điểm phần trăm | mã đúng; tỷ lệ > 8° gần như không đổi theo baseline 5 → 30 m (76,2 % → 75,8 % ở Connecting Ridge), tỷ lệ > 20° thì đổi (9,6 % → 5,7 %) |
| DEM thứ hai (NASADEM / ArcticDEM), cùng mã và quy tắc | 40/42 phán quyết giữ nguyên | **Da Qaidam vẫn đạt** (hạng 42/34/40 trên 49); **Peary Land trượt** (44/19/44; cần ≥ 24,5) → phán quyết L1 của Peary Land là sát ngưỡng, phải nói rõ |
| Leave-one-out trên Mặt Trăng (6 vùng) | cùng vùng 16/32, khác vùng 94/270; vách Shackleton 4/4 so với 13/45 | phép thử nhận ra **lớp địa hình**, không phải địa danh; tách rõ vách dốc khỏi sống núi |
| 6 vùng PGDA 78 (4 vùng mới dùng footprint medoid, thăm dò) | Da Qaidam đạt 3/6 vùng (Connecting Ridge, de Gerlache rim, peak near Shackleton); Nobile rim 1 và Malapert: 0 ô | mở rộng Relevance; không đưa vào `verdicts.parquet` |
| Độ phổ biến không thiên lệch (null 200) | Connecting Ridge 1/200, vách Shackleton 4/200, Fisher p = 0,37 | chưa đủ mạnh → đang mở rộng lên 1000 ô |
| JETT5 (NASA SVS 14583) | diễn tập Artemis III ở San Francisco Volcanic Field, 13–17/5/2024 | footprint SP Crater / Black Point là site kinh điển gần Connecting Ridge nhất (duy nhất qua 1 cấu hình), nhưng không bền vững |

## 2b. Cập nhật 15:30 (đã làm thêm sau khi viết file này)

- Mẫu null đã mở rộng xong: 1000 ô ngẫu nhiên → Connecting Ridge **1**, vách Shackleton **9**,
  Fisher p = 0,02; ngoại suy Connecting Ridge ≈ 196 ô (CI 5–1.090).
- `scripts/site_stability.py`: khối 3 × 3 footprint. Quanh 6 site kinh điển **0/54** đạt; quanh
  Da Qaidam và Peary Land mỗi nơi **1/9** đạt với cả hai DEM (Peary Land: footprint 4 km về phía
  nam, không phải ô gốc → là "manh mối", không phải kết quả).
- Hình mới `docs/figures/fig_region_matrix.png`; hiệu suất hành trình (≈ 10 km so với ≈ 86 km)
  đã vào bảng tiêu chí và slide 5; JETT5 đã vào `config/mission.yaml`.
- Mốc đã commit: `e4142fd`. Đang chạy: `cross_dem.py --n-wall 99` (toàn bộ ô vách).
- Slide 4 còn placeholder `@SAME@ of @NDEM@`: điền bằng khóa `cross_dem_same_verdict` /
  `cross_dem_n` sau khi cross-DEM xong.

## 2c. Cập nhật 15:50

- PR #8 (2e) đã mở; cổng 2 đang chạy (lời nhắc chuẩn). Commit: `e4142fd`, mốc 2 + merge main
  `0ba6d39`.
- Thêm `scripts/web_evidence.py` → `web/evidence.html` (trang "Evidence" sinh từ bảng), link
  trong `web/index.html`, workflow Pages chép thêm `test_protocols.md` và `field_facility.md`.
  **Chưa xem trên trình duyệt.**
- Còn chạy nền: `cross_dem.py --n-wall 99`. Xong thì chạy lại chuỗi ở mục 6, sửa hai số
  "40 of 42" trên slide 4 (dòng có `cross_dem_same_verdict = …`, test sẽ báo nếu lệch) rồi
  `scripts/web_evidence.py`.
- Mục 3 bên dưới: các bước 1–7 đã xong; còn bước 8 (cổng → sửa → merge).

## 3. Việc còn lại của chu kỳ 2e (theo thứ tự)

1. Chờ `null_expand.py` xong → `PYTHONPATH=src .venv/bin/python scripts/l1_regions.py` (sinh
   lại `l1_prevalence.parquet` với 1000 ô) → `scripts/report_tables.py`.
2. Sửa 2 lỗi lint; tên vùng viết đúng hoa/thường ("De Gerlache rim", "Peak near Shackleton").
3. Ghi điểm yếu Peary Land vào `config/sites.yaml` (note của site) → chạy lại
   `scripts/sites.py` (dùng cache Attention), `scripts/mission_value.py --no-attention`,
   `scripts/discovery/run_discovery.py`, `scripts/slides/slide_numbers.py`.
4. `config/mission.yaml`: thêm `analog_missions.jett5` (trích NASA SVS 14583).
5. `scripts/slides/slide_numbers.py`: khóa cho các số 2e (cross-DEM, 3/6 vùng, lunar control,
   prevalence 1000, sai khác với raster NASA). `docs/slides_draft.md`: slide 4 thêm 3 kiểm tra
   (raster NASA, DEM thứ hai, Mặt Trăng); slide 5 đổi trọng tâm sang **Da Qaidam** (đạt 3/6
   vùng, bền với 2 DEM); Peary Land ghi "sát ngưỡng, trượt với DEM thứ hai".
6. Test mới `tests/test_l1_regions.py`: tái lập đúng `l1_robust_set`; bảng commit = bản dựng
   lại; `cross_dem.parquet` có đủ ô then chốt; mọi khóa slide tồn tại.
7. PLAN: mục "Giai đoạn 2e" (A24–A27) + dòng Nhật ký có trạng thái test.
8. Commit (không ghi danh AI), push, mở PR, chạy cổng 2 với lời nhắc chuẩn (lời nhắc tự soạn
   từng bị bộ lọc API chặn nhầm — dùng đúng mẫu `claude-gate-diff`), sửa, merge.

## 4. Các hướng phân tích tiếp theo (chưa làm, xếp theo giá trị/chi phí)

**Validity**
- V1. Sau khi có 1000 ô null: độ phổ biến 6 vùng với CI hẹp; kiểm "sống núi hiếm hơn vách"
  bằng mẫu không thiên lệch; liệt kê ô null đạt (ứng viên không thiên lệch — chỉ báo cáo, không
  thành ứng viên theo quy tắc đã đăng ký).
- V2. Cross-DEM cho **toàn bộ** 99 ô vách + ô null đạt (hiện mới 30 ô mẫu); thêm ArcticDEM V4.
- V3. Độ nhạy ngưỡng: n/2 → n/3, 2n/3 (bảng `validation_sensitivity.parquet` đã có một phần).
- V4. Peary Land: thử ô lân cận (±4 km) với cả hai DEM để xem có ô nào bền vững.

**Impact**
- I1. Hiệu suất thử nghiệm: số km hành trình cần để gặp cùng lượng địa hình > 8° như 10 km ở
  Connecting Ridge (Da Qaidam ≈ 9,6 km; site kinh điển trung vị ≈ 86 km) — giả định hành trình
  ngẫu nhiên trong footprint, ghi rõ giả định.
- I2. Phiếu "kế hoạch chiến dịch" cho Da Qaidam: độ cao, mùa không tuyết, 3 vùng Artemis phục
  vụ, hệ thống cần thử, biến phải vào cơ sở mô phỏng. Đưa vào `docs/test_protocols.md` và web.
- I3. Web: thẻ site hiện giao thức + hình `fig_transfer_matrix.png` (file của Linh — báo qua PR).

**Creativity**
- C1. "Lớp địa hình, không phải địa danh": ma trận 6 vùng × site Trái Đất (hình).
- C2. "Quen cho Mars, hiếm trong ngữ cảnh Moon" (Da Qaidam 71 / 1) — đã có.

**Không ai làm thay được**
- Hai người đọc văn bản gốc về AI và ký `docs/compliance.md` (mục 0.1).
- Dàn trang slide (7 slide) từ `docs/slides_draft.md`; bật GitHub Pages; trang dự án.

## 5. Quy tắc phải giữ (đã bị cổng bắt lỗi nhiều lần)

- Không đổi ngưỡng, phán quyết hay `verdicts.parquet`; mọi phân tích mới là hậu nghiệm và có
  dòng trong bảng Deviations.
- Không viết: "meets the requirement", "credited towards TRL", "only 2 on Earth", "blind
  rediscovery" như bằng chứng, "false-positive rate" cho tỷ lệ null, "same place" (phải là
  "same island / plateau, different footprints").
- NASA ghi vùng 100 m / 2 km, không ghi baseline độ dốc → số của ta chỉ so Trái Đất với Mặt
  Trăng. Hai số đo dốc là kiểm tra nhất quán (engine chọn theo chính chúng).
- Mọi số trên slide có khóa trong `docs/slide_numbers.json` (test kiểm).
- Git: không dòng ghi danh AI; commit bằng danh tính người dùng.

## 6. Lệnh kiểm chứng

```bash
PYTHONPATH=src .venv/bin/python scripts/l1_regions.py
EE_PROJECT=similitude-ee PYTHONPATH=src .venv/bin/python scripts/cross_dem.py --n-wall 30
.venv/bin/python scripts/mission_value.py --no-attention
.venv/bin/python scripts/slides/slide_numbers.py
.venv/bin/python scripts/report_tables.py && .venv/bin/python scripts/report_tables.py --check
EE_PROJECT=x .venv/bin/python scripts/figures_report.py
.venv/bin/python -m pytest -q && .venv/bin/ruff check .
```

## 7. Chấm điểm thật (15/11 15:10)

| Tiêu chí | Điểm | Còn thiếu để lên 9 |
|---|---|---|
| Validity | ~8 | L1 không có đối chứng dương theo nghĩa chặt; M1 FAIL; Peary Land sát ngưỡng |
| Impact | ~7,5 | chưa có người dùng thật xác nhận; chưa có số hiệu suất (I1) |
| Creativity | ~8 | phát hiện "hidden" mỏng; cần hình 6 vùng × site |
| Relevance | ~8 | vế Mars chỉ có lens băng bán định lượng |
| Presentation | ~7 | slide mới là bản nháp chữ; web chưa có phần mới |

45/50 đòi hỏi 9 ở cả năm tiêu chí; với dữ liệu hiện có đó là mục tiêu chưa chắc đạt, và không
được đạt bằng cách thổi phồng khẳng định.
