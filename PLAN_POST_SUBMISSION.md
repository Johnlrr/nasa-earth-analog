# PLAN: SIMILITUDE sau khi nộp — kiểm chứng thật, phủ Artemis III, căn cứ Mars

Nguồn: yêu cầu trực tiếp của Bảo (15/11/2026, sau khi nộp)  ·  Cổng 1: chưa chạy

## Bối cảnh (recap cho phiên mới)
- Bản nộp Space Apps 2026 bị đóng băng ở tag `submission-2026-11-15` / nhánh `main` (Pages deploy từ `main`).
  **Không merge `post-submission` vào `main` và không sửa Pages cho tới khi chấm xong.**
- Mọi việc sau hạn làm trên nhánh `post-submission`, worktree `../nasa-earth-analog-post`. `data/raw` là symlink
  sang repo chính. Trong worktree chạy Python với `PYTHONPATH=src` (gói `similitude` cài editable trỏ về repo chính).
- Đã có khi nộp: L1 (độ dốc 30 m, ba cấu hình), V1 FAIL / V2 PASS (p = 0.049; Bonferroni 0.098), lens Mars
  Jezero HM1 PASS (p = 0.0005), lead Argentina và Baffin (71 ngày Mặt Trời thấp), ma trận chiến dịch 5/5 vs classic 1/5,
  atlas 6 vùng PGDA (chỉ Connecting Ridge có lead qua mọi test). Báo cáo `docs/validation_report.md` §7d–7e, Deviations ≤ 38.
- Đã làm sau hạn (commit `8798764`, `dabc895`, `ae2bbff`), báo cáo §7f và Deviations 39–41:
  - R1 FAIL: detour của planner không dự báo detour thật của Perseverance (ρ = −0.35, 20 leg 1 km); R2 FAIL (độ gồ ghề so với tốc độ lái).
  - **R1b PASS: độ dốc 30 m từ quỹ đạo so với độ nghiêng rover đo tại 708 waypoint, ρ = 0.80 (0.91 theo site).**
  - Lens Mars chạy lại với ô vuông (lưới CTX equirectangular rộng khoảng 5 % theo x): HM1 vẫn PASS (p = 0.0004).
  - `docs/pitch_3min.md` (pitch 3 phút), `docs/outreach_draft.md` (thư xin phản hồi; người trong đội tự gửi).

## Phạm vi
Làm: (A) phủ 9 vùng ứng viên Artemis III bằng campaign card và tối ưu phủ tập; (B) lens Mars cho căn cứ người (địa hình + băng);
(C) đóng gói cho vòng chấm sau. Không làm: sửa bản đã nộp; claim năng lực rover cho route outcome (R1 đã FAIL).

## Schema / giao diện
- `data/derived/artemis3_regions.json`: `{region, source, lat, lon, pgda_sites: [...], dem: "PGDA78 SiteXX" | "LOLA 20 m"}`
- `scripts/campaign_cover.py`: `cover(region) -> {sites: [...], facilities: [...], rows_covered, rows_total, windows}`
  bằng tham lam phủ tập (greedy set cover) trên bảng site × hàng thử nghiệm; tiêu chí phụ khi hoà: ít nước đóng hơn, cửa sổ dài hơn.
- `data/derived/mars_base_lens.json`: cùng khung với `mars_m1.json`, thêm `ice` (X1) cho mỗi ô.

## Hạng mục
- [x] A1. **Toạ độ 9 vùng Artemis III** (Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton,
  Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain) lấy từ tài liệu NASA có trích dẫn (thông cáo 10/2024 hoặc NTRS),
  **không đoán**. — File: `data/derived/artemis3_regions.json`, `docs/validation_report.md` (bảng nguồn) — Xong khi: 9 vùng có
  lat/lon và link nguồn — Kiểm chứng: mỗi toạ độ rơi vào DEM LOLA của vùng; đối chiếu tên site PGDA 78.
- [x] A2. **DEM cho mỗi vùng**: ưu tiên PGDA 78 5 m (tải thêm Site khác ngoài 01/04/06/07/11/23 nếu phủ vùng), nếu không có thì
  LOLA 20 m south-pole DEM của PGDA. — File: `scripts/fetch_artemis3_dem.py` — Xong khi: mỗi vùng có cửa sổ ≥ 12 km không NaN —
  Kiểm chứng: slope code khớp slope raster NASA ≤ 0.01° như đã làm cho Site01.
- [x] A3. **Đăng ký trước** `config/prereg_artemis3.yaml` **trước khi so Earth**: tham chiếu mỗi vùng = medoid của các cửa sổ 4 km
  trong vùng (như `l1_regions.py`); τ route theo luật V2 (cửa sổ không chồng lấn, tâm ≥ 4 km); test = L1 robust + V2 route trên
  hai DEM; mẫu Earth = 1,000 ô null + leads của access screen. Commit + push trước khi chạy.
- [x] A4. **Chạy** `scripts/artemis3_atlas.py` (dựa trên `scripts/artemis_atlas.py`, thay τ V1 bằng V2) — Xong khi: bảng vùng × (leads,
  slope hai DEM, route hai DEM, qua mọi test, cửa sổ Mặt Trời thấp) — Kiểm chứng: Connecting Ridge (nếu nằm trong một vùng) tái
  tạo đúng số §7e.
- [x] A5. **Tối ưu phủ chiến dịch** `scripts/campaign_cover.py` cho mỗi vùng: hàng thực địa (slope, routes, low Sun, shadow, slope 5 m
  nếu có ArcticDEM) + hàng facility từ ledger; xuất campaign card (JSON + PNG như `fig_campaign_coverage.png`) — Kiểm chứng: với
  Connecting Ridge cho lại 5/5 bằng Argentina + Baffin; unit test greedy trên ma trận nhỏ.
- [ ] A6. **Trang `web/artemis3.html`** (chỉ trên nhánh này): chọn vùng → card → lịch. Theo UI của Linh (skill UI của Linh).
- [x] B1. **Đăng ký trước** `config/prereg_mars_base.yaml`: mục tiêu = 2–3 vùng băng nông ứng viên đổ bộ người (Arcadia Planitia,
  Deuteronilus Mensae theo SWIM; toạ độ có trích dẫn), DEM = HiRISE DTM (PDS/UA) nếu có ở đó, nếu không thì CTX DTM; match =
  địa hình (slope + route, như M1, ô vuông) VÀ X1 băng PASS; null = 1,000 ô; classic = Haughton, Svalbard (nếu có chip), Wright Valley.
- [x] B2. **Chạy** `scripts/mars_base_lens.py` — Xong khi: tỷ lệ khớp null, classic, danh sách ô nước mở — Kiểm chứng: null prevalence
  phải thấp hơn lens Jezero (16 %); nếu không thì ghi rõ "lens không chọn lọc".
- [x] B3. **R1b cho băng?** Không: chưa có ground truth băng ở Mars; ghi vào Giới hạn.
- [ ] C1. Báo cáo §7g (Artemis III) và §7h (Mars base), Deviations 42+, slide pitch riêng `slides/pitch/` (không đụng `slides/deck.html` đã nộp).
- [ ] C2. Chạy pytest, ruff, `report_tables.py --check`, node test; ghi Nhật ký. Mở PR `post-submission` → **không merge** tới khi chấm xong.

## Edge-cases
- Vùng Artemis III không có DEM 5 m: dùng 20 m, ghi rõ; slope 20 m→30 m vẫn đúng baseline.
- Medoid nằm trong vùng tối vĩnh cửu (PSR): DEM vẫn có; chỉ L2 (ánh sáng) cần lưu ý.
- HiRISE DTM nhỏ (khoảng 5 × 20 km): không đủ 185 cửa sổ 4 km; dùng lưới 1 km và ghi n thực tế; nếu < 30 cửa sổ thì dùng CTX.
- Pages: mọi trang mới chỉ ở nhánh; không push lên `main`.

## Kết quả ngắn (15/11 đêm)
- A1: NASA không công bố toạ độ tâm 9 vùng; chạy 5 vùng có DEM PGDA 78 cùng tên (Haworth, Malapert Massif, Nobile Rim 1/2, Mons Mouton Plateau = Leibnitz β). 4 vùng còn lại ghi lý do trong `config/prereg_artemis3.yaml`.
- A2: slope ta vs slope NASA lệch trung vị ≤ 0.02°. A3 đăng ký `1e18662`; sanity Site01 τ = 1.1608 = V2.
- A4: mọi vùng có site Earth ở nước mở (1–23), null 0.2–3 %, classic 0/54 ở cả 5 vùng (so sánh classic > null FAIL, p = 1). A5: Haworth, Nobile Rim 1 phủ 2/2 (Canada, Mặt Trời thấp 46/36 ngày); 3 vùng còn lại 1/2.
- B: Arcadia (HiRISE, đăng ký `30f201d`): exploratory (2 lân cận); địa hình khớp 14/994, classic 0/45 (HB1 FAIL), không ô nào vừa khớp địa hình vừa có băng (X1) → cần 2 site (đồng bằng khô + sa mạc cực).
- Shortfalls: `docs/shortfalls_map.md` theo danh sách NASA 2026 (1.05, 1.06, 3.02, 3.03, 16.01, 8.06, 8.07).
- Chưa làm: A6 (trang web), C1 phần slide pitch.

## Câu hỏi mở
- Có công bố toạ độ chính thức cho tâm 9 vùng Artemis III không, hay chỉ có bản đồ? (A1 phải trả lời trước A3.)
- Vòng chấm địa phương có pitch trực tiếp không? Nếu có, dùng `docs/pitch_3min.md`; kết quả sau hạn phải nói rõ là sau hạn.

## Nhật ký
- 2026-11-15 · Opus 5.5 · R1/R2 FAIL, R1b PASS (ρ 0.80), M1 ô vuông giữ PASS; pitch + outreach draft; plan này · test: pytest 218 pass, ruff sạch, report --check sạch.
- 2026-11-15 23:27 · Opus 5.5 · A1–A5 (5/9 vùng Artemis III có DEM PGDA cùng tên; đăng ký `1e18662`; null 0.2–3 %, classic 0/54 mọi vùng, site nước mở 1–23/vùng; Haworth và Nobile Rim 1 phủ 2/2 nhờ Canada), B (Arcadia HiRISE, `30f201d`: exploratory, 14/994, classic 0/45, 0 ô có cả địa hình và băng), map NASA 2026 Shortfalls, báo cáo §7g/§7h, Deviations 42–44.
