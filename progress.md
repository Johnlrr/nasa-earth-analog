# PROGRESS — Linh (B)

Nhật ký tiến độ phần việc của Linh (B). Theo yêu cầu của Linh: **không sửa `PLAN.md` / `DESIGN.md`**. Mọi tiến độ, sai khác so với PLAN và việc cần quyết đều ghi ở đây.
Nhánh: `linh/spectral-story` (từ 16:28 đồng bộ với `main` @ `541f0fe` sau khi Bảo hợp nhất A5–A9 + B0–B11). Môi trường: conda `similitude` (Python 3.12).

## Cần Linh / đội quyết (chưa chặn việc)
- [x] ~~Commit / push~~: đã commit + push 8 commit B0–B12 lúc 14:00; Bảo đã hợp nhất vào `main`.
- [ ] **0.1 / G0 (quy định SI):** cần người đọc Submission Guide và quyết. Bản nháp `docs/compliance.md` sẽ có sẵn checklist.
- [ ] File `.dodsrc` ở gốc repo do `earthaccess` tạo (chỉ chứa đường dẫn netrc/cookie). Chưa xoá, không commit. Nên thêm vào `.gitignore` (file của Bảo).
- [ ] **G1 — mục tiêu `shackleton_rim`:** Bảo đề xuất không dùng chip này làm mục tiêu (dốc trung vị 31°, có lẽ là thành trong hố). Hiện **4/5 ứng viên L2** khớp tốt nhất với `shackleton_rim`. Nếu G1 chấp nhận đề xuất, cần lọc mục tiêu này trong `fidelity.parquet` (A8) hoặc trong discovery rồi chạy lại.
- [ ] **OpenAlex hết ngân sách miễn phí trong ngày** cho IP này (không có API key; reset 00:00 UTC = 07:00 giờ VN). Ô L1/L2 mới chưa có Attention (hiển thị "unknown", vẫn được giữ theo thiết kế). Sáng mai chạy lại `python scripts/discovery/run_discovery.py`; hoặc đặt biến môi trường `OPENALEX_API_KEY` (khoá cá nhân, không commit) để chạy ngay.
- [ ] **Báo Bảo:** mặt nạ đất trơ tầng 1 để lọt băng/tuyết (sông băng Nunavut, South Patagonian Ice Field) → nên loại WorldCover lớp 70 (snow/ice) trong A2/A6.

## Việc còn lại của B (phụ thuộc người / Bảo)
- **G1 (16:00):** quyết M1 đường chính hay lùi (xem B3), giữ hay cắt X1, và mục tiêu `shackleton_rim` (trên).
- **B10:** Bảo duyệt chéo `config/review_b10.yaml` + `data/raw/review/contact_sheet.png`, `contact_sheet_L1L2.png`.
- **B12:** chốt số theo `docs/validation_report.md` (A9); dựng slide thật từ `docs/slides_draft.md`.
- **0.1 / 5.x:** đọc nguyên văn, quyết G0, ký `docs/compliance.md`, điền trang Project, nộp.
- Workflow Pages (`.github/workflows/pages.yml`) cần bật Settings → Pages → "GitHub Actions" và merge vào `main` để deploy.

## Sai khác so với PLAN (ghi lại, không sửa PLAN)
- `lens_id` dùng dạng ngắn `L1, L2, M1, X1` (khớp `targets_L1.parquet` của Bảo), không dùng `M1_aqueous` như ví dụ DESIGN 2.4.
- Hạt giống của B (M1/X1) đặt ở `config/seeds_m1.yaml`, `config/seeds_x1.yaml` vì `config/seeds.yaml` thuộc Bảo.
- Tên tham số phổ giữ tên ngắn của PLAN (`OLINDEX`, `D2300`, `MIN2295_2480`…); tên gốc Viviano-Beck (`OLINDEX3`…) và mốc thay ghi trong `PARAM_TABLE`.

## Giai đoạn 2b (sau G1, theo `docs/review_g1.md` + PLAN 2b)
| Hạng mục | Trạng thái | Commit |
| :--- | :--- | :--- |
| Gộp nhánh Bảo (G1a) | ✓ Harrat/Pinacate đã gỡ khỏi web | `88bfef6` |
| B14a đăng ký trước quy tắc pixel M1 | ✓ commit riêng 17:20, trước mọi pixel | `66f9da7` |
| B13 giai đoạn null | ✓ 69 footprint null, ~490 nghìn pixel | `1e8ae67` |
| B14b sàn nhiễu | ✓ commit riêng 17:29, trước đối chứng: D2300 0,110 · MIN2295_2480 0,040 · OLINDEX 0,273 | `4e007f2` |
| B13 đối chứng/mồi nhử | ✓ chạy 20:21 sau A14 · **tiêu chí dừng: FAIL** (xem dưới) | (commit này) |
| B13 hạt giống / rank | ✓ chạy cho đủ hồ sơ, **không công bố** (tiêu chí dừng trượt) | (commit này) |

**B13 — tiêu chí dừng 21:00 (đăng ký ở B14a, sàn nhiễu B14b), mục tiêu Jezero, đạt = mảng khớp lớn nhất ≥ 0,1 km²:** `data/derived/m1_stop_rule.json`
| Điểm | Mảng lớn nhất (km²) | Kỳ vọng | Kết quả |
| :--- | ---: | :--- | :--- |
| Lake Salda (toạ độ A14, dời 2,65 km) | 0,052 (tổng khớp 0,19) | đạt | **trượt** — chỉ khớp vụn dọc bờ |
| Lake Salda (toạ độ gốc, 141 pixel) | 0 | — | trượt |
| Semail Wadi Tayin A / B / Ibra | 3,19 / 19,25 / 0,35 | đạt | đạt |
| Wadi Rum (mồi nhử) | 0 | bị bác | đạt |
| Simpson (mồi nhử) | 0 | bị bác | đạt |
| Harrat Khaybar / Rahat | 0 / 0,003 | — | xác nhận "khớp rỗng" |
**Phán quyết: FAIL** → theo quy tắc PLAN 2b: M1 lên slide dạng "minh hoạ phương pháp trên 4 địa điểm + kết quả âm ở tỷ lệ footprint", **không công bố hidden analog M1**. Không chỉnh ngưỡng sau khi xem kết quả. Ghi chú để báo cáo: sàn D2300 (0,110) > mục tiêu (0,080) làm phép thử rất bảo thủ; Salda tổng khớp 0,19 km² nhưng phân mảnh. Hạt giống/rank (ghi lại, không công bố): rank_001 khớp 100 % pixel (25 km²) — đáng ngờ, cần soi ảnh nếu dùng; New Idria, Troodos ít pixel hợp lệ (thực vật).
| B15 X1 danh sách 3 điều kiện | ✓ | `677777a` |
| B16 phần "Attention rỗng ≠ hidden" | ✓ | `4ce40cf` |
| Hợp đồng A15 cho M1/X1 | ✓ `verdict_variables`, `unobserved: [{variable, reason, facility}]` trong `lenses.yaml`; cờ `m1_controls_pass` (= False) trong `m1_stop_rule.json` và cột của `earth_M1_pixels.parquet`; trường `variable`/`facility` cho mọi mục `ledger/*.yaml` (nội dung không đổi). **Bảo:** định dạng `verdict_variables` cho L1/L2 nên theo cùng khóa (`test, targets, source, rule`) | `8de6700` |
| B16 phần đọc | ✓ schema thêm `verdicts[]`, `analog_role` (**thêm giá trị `ice-configuration` cho X1**, ngoài 3 giá trị PLAN), native rank, matched area; discovery **chỉ đọc** `verdicts.parquet` (không có bảng → không sinh verdict); web: khối ba trạng thái + native rank + matched area (Lake Salda hiển thị footprint A14, kèm số gốc). Kiểm bằng file verdicts giả + ảnh chụp `data/raw/review/web_verdicts_card.png` | (commit này) |
| B16 còn lại | ✓ (20:55) sau A15: ứng viên = ô có verdict **TRANSFERS cấp ô** trong `verdicts.parquet` (không còn chọn theo σ khi có bảng); card hiển thị đúng mục tiêu của verdict; dòng TRANSFERS tổng hợp cấp lens ("N ô đạt") **không** hiện như phán quyết của từng điểm, chỉ giữ dòng vật lý dùng chung và NO-ANALOG/UNOBSERVED của đúng mục tiêu. Kết quả: X1 hidden = Mackenzie King Island (att 1), Peary Land (att 2), `engine-semiquant`; L1/L2: 5 ô mỗi lens đạt nhưng **Attention chưa biết** (OpenAlex hết ngân sách) → chưa gọi là hidden; M1: không (tiêu chí dừng). Ảnh: `data/raw/review/b16_card_desktop.png`, `b16_card_375.png` (375 px không tràn ngang). Test 155 passed | (commit này) |
| Báo Bảo về A15 | (1) X1 `rank_0056` (qa `vegetated`) có TRANSFERS — nên lọc `qa_flag`; discovery đã chặn qua cổng qa. (2) Biến M1 trong verdicts là `aqueous_mineral`, khác khóa `verdict_variables` đã khai báo; dòng UNOBSERVED dùng chuỗi thay vì khóa `unobserved[].variable` | — |
| Không push `main` nữa | Linh yêu cầu merge vào `main` một lần (20:20, `ca70f94` → `d444de3`); các commit sau chỉ lên `linh/spectral-story` | — |

**B13 null:** thư viện phổ được vector hoá (`resample` nhóm theo mẫu kênh hợp lệ, `crism_params_stack`) — **cho kết quả trùng tuyệt đối** với cách tính từng phổ trên 154 phổ thật (31 MICA + 123 EMIT; sai khác lớn nhất 0); thêm test. Tải pixel bằng `computePixels` ~6 s/footprint. Sàn D2300 (0,110) cao hơn chính giá trị mục tiêu Jezero (0,080) → ngưỡng pixel Jezero thực tế là D2300 ≥ 0,110 và MIN2295_2480 ≥ 0,040 (bảo thủ, đúng rủi ro PLAN đã ghi: caliche/sét trong null hoang mạc).

**B15 X1:** 3 điều kiện (MAAT ≤ −1 °C; đóng–tan ≤ 20 ngày/năm; khô hạn ≤ 0,5 theo ranh giới bán khô hạn UNEP), **ngưỡng đặt sau khi xem dữ liệu, đã ghi trong `lenses.yaml`**. Kiểm chứng độc lập **ĐẠT**: hai mồi nhử permafrost ẩm đã đăng ký trước (Yakutsk, Tây Siberia) trượt ≥ 1 điều kiện. Beacon Valley đạt 3/3; Axel Heiberg đạt 3/3. **Pamir–Changtang: 0/6 hạt giống đạt** (160–230 ngày đóng–tan/năm) → giả thuyết DESIGN bị dữ liệu bác. Thêm bộ lọc băng hà (WorldCover lớp 70, cùng ngưỡng A13 của Bảo: > 0,2 loại): 4 ô "đạt" thực ra nằm trên chỏm băng Greenland → loại. Còn **7 ô** đạt cả 3 và không phải băng hà (Bắc Cực Canada, Peary Land; 2 ô > 82,75°N ngoài vùng phủ WorldCover = "không đánh giá được băng").

## Nhật ký
- 2026-11-14 16:55 · **Sau khi hợp nhất với engine của Bảo (A5–A8):**
  - Duyệt thay đổi của Bảo trong `discovery.passes_fidelity` (thêm σ ≤ 2; L2 xét `sigma_shadow`): **đồng ý**, đúng DESIGN 2.2(3). Thêm test cho nhánh này.
  - Sửa lỗi: đối chứng L1/L2 **không được xuất** vì bảng của Bảo dùng ID `CTRL_<id>`/`SEED_<Tên>` còn discovery chỉ nhận `ctl_`. Giờ nhận cả hai quy ước (`ID_PREFIXES`, `control_cell_ids`); hạt giống của Bảo lấy tên từ cột `name`.
  - Ô L1/L2 (`E10K_…`) giờ có tên (reverse-geocode) và được tra Attention.
  - L2 xếp hạng/NMS/chọn mục tiêu theo `d_shadow` (`score_column`); ghi chú L2 tách "Sun geometry: no Earth analog" và σ_shadow.
  - `metadata.lenses[*].n_null` lấy từ bảng `earth` (trước là `null`); thêm `ranking`, `best_sigma_ranked`.
  - Test Card mất radar khi dùng `fidelity.parquet` (không có z) → z tính lại bằng chính `fidelity.fit_population` + `_min_scale` của Bảo (`engine_z`), không viết công thức mới.
  - `openalex.py`: dừng sớm khi hết ngân sách, hỗ trợ `OPENALEX_API_KEY`; discovery không còn treo/hỏng khi OpenAlex lỗi.
  - Web: L2 dùng σ_shadow cho màu, thứ tự danh sách, tooltip; card có khung hai phần (bóng đổ = ứng viên; hình học Mặt Trời = no-analog có số). Kiểm bằng ảnh chụp headless (`data/raw/review/web_l2_card.png`).
  - **B10 cho 10 ô L1/L2:** hạ 4 ô xuống `hypothesis` (băng/tuyết: L1 Nunavut, L2 Gêrzê, L2 Nunavut, L2 Lago Argentino); giữ 6, ghi chú L1 Tamarugal về địa lý vẫn là bắc Atacama (ngoài vòng 350 km).
  - Kết quả: 28 feature. Hidden đang `engine-confirmed`: M1 Harrat Rahat (σ 0,24), Harrat Khaybar (0,63), Pinacate (2,00); L1 Greenland, Gêrzê, Tamarugal, ven biển Lima (σ ≈ 0); L2 Hajar/Oman (σ_shadow 0,65), Bandar Abbas (0,67). X1: không có ứng viên (σ tốt nhất 2,07 > 2).
  - test: 126 passed, ruff sạch, `node --check` OK, `validate_candidates` = 28.
- 2026-11-14 12:56 · 0.2 phần Linh: Earthdata `earthaccess.login()` OK; GEE `ee.Initialize(project=$EE_PROJECT)` OK, scope đầy đủ (export được). `EE_PROJECT=nasa-hackthon-kl`.
- 2026-11-14 13:05 · **B0 xong (chờ commit/PR):** `config/lenses.yaml`, `config/targets.yaml`, `config/controls.yaml` (18 mục, kỳ vọng ghi trước, có `expected_rgb`), `schemas/candidate.schema.json`, `web/data/candidates.mock.geojson` (3 feature, phủ L1/L2/M1/X1), `src/similitude/io.py` (`validate_candidates`, `check_candidates`, `write_candidates`, `load_*`, `min_scale_for`), `tests/test_schema.py` · test: 15 passed, ruff sạch. DOI trong targets/controls đã kiểm qua Crossref.
- 2026-11-14 13:10 · **B1 xong:** `src/similitude/descriptors/spectral.py` (`COMMON_WL_NM` 400–2490 nm bỏ 1340–1460, 1790–1960; `PARAM_TABLE` 24 tham số, mốc gốc VB14 + mốc thay; `resample`, `crism_params(subset)`, `sam`), `tests/test_spectral.py` · test 13 passed.
- 2026-11-14 13:15 · **B2 xong:** `scripts/targets/mica_ingest.py` → `mica.parquet`, `mica_spectra.parquet`, `targets_M1.parquet` (4 mục tiêu + 29 phổ khoáng quần thể, bản numerator). Kiểm chứng PLAN: MG_CARBONATE `MIN2295_2480` = 0,056 > 0 ✓; `OLINDEX` cao nhất = FE_OLIVINE ✓ (bản ratioed: MG_OLIVINE cao nhất, FE_OLIVINE hạng 2). Ánh xạ mục tiêu → MICA: jezero_margin→MG_CARBONATE, oxia_planum→FE_SMECTITE, meridiani→JAROSITE, nili_fossae_olivine→FE_OLIVINE. Chip CTX 10 m/px (5 km) cho 4 mục tiêu: `scripts/targets/mica_ctx_chips.py` → `data/raw/mars/ctx_chips/` (Jezero 10 % pixel trống).
- 2026-11-14 13:20 · **B3 spike (R2/R3):** EMIT L2A trên GEE `NASA/EMIT/L2A/RFL`, 2–6 s/footprint 5 km (→ B5 ~100 footprint ≈ 7 phút, không cần earthaccess). **Lỗi tìm thấy và đã sửa:** cảnh EMIT mới điền −0,01 vào kênh hơi nước (không phải NaN) → `resample` giờ chỉ nhận phản xạ > 0. Hệ quả cho tham số (áp dụng cả hai phía): `BD1750` loại khỏi M1 (vùng fill bắt đầu ~1765 nm, mất vai phải); `D2300` mốc 1780→1700 nm; `BD2100` mốc 1970→1990 nm (1970 còn dư hơi nước). Kết quả (d đường chéo tạm, quần thể MICA, so Jezero; σ tạm tràn số nên xếp theo d):
  | site | n pixel | d Jezero | d Oxia | d Meridiani | SAM Jezero |
  | :--- | ---: | ---: | ---: | ---: | ---: |
  | semail_a | 7551 | **7,21** | 7,27 | 9,79 | 0,022 |
  | harrat_khaybar | 7647 | 8,08 | **4,11** | 5,82 | 0,020 |
  | semail_b | 7627 | 10,08 | 10,82 | 14,22 | 0,064 |
  | semail_c | 7556 | 10,78 | 9,73 | 12,74 | 0,072 |
  | matanomadh | 2562 | 15,09 | 11,73 | 12,81 | 0,064 |
  | wadi_rum (mồi nhử) | 7980 | 17,36 | 15,48 | 17,07 | 0,049 |
  | lake_salda (đối chứng) | **142** | 19,73 | 18,35 | 21,68 | 0,038 |
  **Tiêu chí G1/M1: TRƯỢT một nửa** — Semail < Wadi Rum ✓, nhưng Lake Salda > Wadi Rum ✗. Diễn giải (chưa phải kết luận): footprint Salda 5 km chủ yếu là mặt hồ; mặt nạ nước/ẩm chặt chỉ để lại 142 pixel bờ ẩm, phổ sụt mạnh về SWIR (r1300 0,34 → r2490 0,04) giống đất ướt hơn là hydromagnesit khô. Theo PLAN **không dời toạ độ đối chứng sau khi xem kết quả**. Thêm: mọi điểm Trái Đất đều > 4σ so với quần thể MICA (lệch hệ thống numerator I/F Sao Hoả vs phản xạ bề mặt) → dự kiến cờ no-analog nhiều; báo bằng số.
  **Cần G1 (16:00) quyết:** (a) giữ đường chính (EMIT + tham số CRISM), báo Salda là kết quả âm có giải thích — **đề xuất của mình**, vì tham số vẫn tách Semail/Harrat khỏi mồi nhử; hoặc (b) lùi về EMIT L2B mineral (Linh tải được bằng earthaccess). Trong lúc chờ, B5 chạy theo (a).
- 2026-11-14 13:30 · **B5 xong (theo đường chính, chờ G1):** `scripts/emit/tier_m1.py` + `scripts/emit/emit_gee.py` → `earth_M1.parquet`, `earth_M1_spectra.parquet`, `earth_M1_cells.csv`. 123 footprint 5 km: control 4, decoy 2, seed 27 (`config/seeds_m1.yaml`; 2 low_valid), rank 20 (ASTER GED Ninomiya MI = e12/e13 cao nhất trên đất trơ WorldCover=60, |lat|≤52, cách nhau ≥100 km; đã kiểm hướng: Semail 0,996, Harrat 0,990 > Wadi Rum 0,909, Simpson 0,854), **null 70 (69 ok)** rút ngẫu nhiên trong footprint cảnh EMIT thật theo ngày ngẫu nhiên. Mọi footprint đối chứng/mồi nhử có phổ ✓; `qa_flag` = low_valid khi < 50 pixel. Sai khác PLAN: tổng 123 > 100 footprint (do thêm hạt giống; GEE nhanh nên không cần cắt).
- 2026-11-14 13:30 · **B6 xong (bán định lượng):** `src/similitude/descriptors/ice.py` (`ice_config`, `aridity_index` có sàn PET 500 mm, `stefan_active_layer`), `tests/test_ice.py` (9 passed), `config/seeds_x1.yaml`, `scripts/gee/tier_x1.py` → `earth_X1.parquet` (416 điểm 10 km: control 2, decoy 2, seed 12, rank 144, null 256 — null ok 54 ≥ 30), `targets_X1.parquet` (Arcadia + 5 điểm Sao Hoả mã hoá từ văn liệu có DOI). **Sai khác PLAN/DESIGN:** MAAT lấy từ ERA5-Land nhiệt độ đất 28–100 cm (2014–2023) thay vì MODIS LST (LST trời quang lệch ấm 2–18 °C ở cao nguyên: Pamir +2,2, Puna +17,7); P/PET dùng sàn PET 500 mm/năm vì P/PET thường hỏng ở hoang mạc cực (Peary Land ra 14,9 = "ẩm"); permafrost: dùng MAAT thay cho Obu 2019/ESA CCI (không có sẵn trên GEE); bề dày tầng hoạt động = Stefan 0,03·√TDD. Quan sát sớm: cao nguyên Tây Tạng/Pamir có **160–230 chu kỳ đóng–tan ngày/năm** (MODIS) so với 8–13 ở hoang mạc cực (Peary, Devon, Axel Heiberg) — giả thuyết DESIGN "Pamir/Changtang tốt nhất" có thể không đứng; để engine quyết.
- 2026-11-14 13:35 · Đồng bộ cờ vùng loại trừ với `config/exclusion_zones.yaml` của Bảo (bản sao trong `discovery.DEFAULT_EXCLUSION_ZONES` cho tới khi merge); gắn lại cờ cho `earth_M1` (4 ô) và `earth_X1` (2 ô).
- 2026-11-14 13:38 · **B8 xong:** `scripts/attention/openalex.py` → `attention.parquet` (truy vấn `"<nơi>" AND (analog OR analogue) AND (Mars OR Moon OR lunar OR planetary)` trên tiêu đề+tóm tắt OpenAlex, lưu nguyên văn truy vấn + ngày). **R13 ✓:** Atacama 223 ≫ Harrat Khaybar 0. Có bảng OVERRIDES cho tên dễ nhầm (Karakul + crater/Pamir…) và REGION_ALIASES cho tên hành chính từ reverse-geocode (vd "Afar Region" → "Afar OR Danakil" = 23 bài → **Afar bị loại khỏi hidden**, đúng tinh thần "hidden").
- 2026-11-14 13:40 · **B9 xong (dữ liệu tạm, chỉ M1 + X1):** `src/similitude/discovery.py` (cờ vùng loại trừ theo đúng 3 kiểu của Bảo, `gate_mask`, `best_target`, `nms`, `select_hidden`, `evidence_status`, `cannot_test` từ ledger, `lens_score`), `tests/test_discovery.py` (11 passed, gồm NMS "hai ô < footprint chỉ còn một"), `scripts/discovery/run_discovery.py` → `web/data/candidates.geojson` (14 feature, qua `validate_candidates`). **Chấm điểm tạm** bằng `scripts/provisional/score_b.py` (theo đúng quy ước fidelity của PLAN, chế độ diag; tự thay bằng `fidelity.parquet` của A8 khi có). Ngưỡng: percentile ≥ 90 (σ ≤ 1 nếu không có percentile), Attention ≤ 10, NMS theo footprint. Cổng mới cho X1 `permafrost_min: 0.5` (**thêm sau khi xem kết quả tạm** — sa mạc nóng không có băng lọt top 5–12 do quần thể Sao Hoả có điểm không băng; ghi rõ trong `lenses.yaml`). Tên ô rank: reverse-geocode Nominatim (chỉ gửi toạ độ, có cache).
  Kết quả tạm (σ đường chéo; σ chỉ để hiển thị, xếp theo d):
  | lens | ứng viên | mục tiêu | σ | percentile | attention | trạng thái |
  | :--- | :--- | :--- | ---: | ---: | ---: | :--- |
  | M1 | Harrat Rahat (SA) | Oxia Planum | 0,24 | 100 | 0 | engine-confirmed |
  | M1 | Harrat Khaybar (SA) | Oxia Planum | 0,63 | 100 | 0 | engine-confirmed |
  | M1 | Pinacate (MX) | Oxia Planum | 2,00 | 98,5 | 1 | engine-confirmed |
  | M1 | Ardakan playa, Yazd (IR) | — | 3,15 | 97 | 0 | engine-confirmed |
  | M1 | Matruh (EG) | — | 3,09 | 97 | 9 | **hypothesis** (B10) |
  | X1 | Đảo Mackenzie King (CA) | Arcadia | 2,44 | 98,1 | 1 | engine-semiquant |
  Đối chứng/mồi nhử: Rio Tinto (expected uncertain) pct 98,5 vs Meridiani ✓; Beacon Valley (expected high) X1 hạng 4/125 ✓; Axel Heiberg (high) pct 46 ✗; Lake Salda (high) pct 12 ✗; Wadi Rum (decoy, low) pct 22 ✓; **Simpson (decoy, low) pct 76–91** ✗ (mồi nhử cát đỏ vẫn khá gần Meridiani/Oxia). Jezero: tốt nhất Semail σ 4,1 → cờ **no-analog** cho mục tiêu carbonate (báo bằng số). Diễn giải: phổ numerator I/F của MICA mang nhiều nền bazan/bụi → khớp tốt nhất là các harrat bazan khô, không phải khoáng biến đổi do nước — cần nói thẳng trên slide.
- 2026-11-14 13:42 · **B10 (một người duyệt):** ảnh Sentinel-2 (median 2023) cho 6 ứng viên → `data/raw/review/contact_sheet.png`; quyết định ghi ở `config/review_b10.yaml` (áp tự động khi chạy discovery): Matruh hạ xuống `hypothesis` (sát biển + ô ruộng); Harrat Rahat giữ, ghi chú có thị trấn trong footprint; X1 ảnh không kết luận được. **Còn thiếu: Bảo duyệt chéo** (PLAN: hai người cùng duyệt).
- 2026-11-14 13:50 · **Nháp 0.1:** `docs/compliance.md` (bảng quy định cần đối chiếu nguyên văn, mục quyết định G0 để trống, nhật ký dùng SI, danh sách dữ liệu NASA/đối tác, checklist 5.2, chỗ ký). **Chưa xong 0.1** — cần hai người đọc nguyên văn và ký.
- 2026-11-14 13:52 · **Nháp B12:** `docs/slides_draft.md` — 7 slide tiếng Anh theo DESIGN 2.6 + kịch bản video 30 s; số M1/X1 gắn nhãn ⟨prov⟩, chỗ L1/L2 và ablation để ⟨TBD-A⟩. Chờ A9 (`validation_report.md`) để chốt số.
- 2026-11-14 13:55 · **B4 + B11 xong (chạy cục bộ):** `web/index.html`, `web/app.js`, `web/style.css`, `.github/workflows/pages.yml`. Leaflet + nền NASA GIBS Blue Marble; chọn lens (đọc `lenses.json`, mặc định lens đầu có dữ liệu); banner "Provisional scores"; trạng thái rỗng cho L1/L2 ("No engine results for this lens yet"); marker theo vai trò (hidden/control/decoy) và màu σ; Test Card có radar SVG (s = exp(−|z|/2)), yếu tố giới hạn, bảng descriptor, Test here, Cannot test, Transfer Ledger theo `applies_to` có link nguồn và gap NASA, mục "Data & limits". Kiểm chứng: chụp màn hình Chrome headless desktop 1366 px + Test Card Harrat Rahat (`data/raw/review/web_desktop.png`, `web_card_crop.png`) không lỗi JS; trong iframe 375 px scrollWidth = clientWidth (không tràn ngang). Sửa CSS bảng bị ngắt chữ. Chưa deploy Pages (cần merge `main` + bật Pages).
- 2026-11-14 13:45 · Xuất `web/data/lenses.json`, `web/data/ledger.json` (`scripts/discovery/export_web_data.py`) cho web.
- 2026-11-14 13:05 · **B7 xong:** `ledger/moon.yaml`, `ledger/mars.yaml`, mỗi mục có `source`. Sửa so với DESIGN: g Sao Hỏa 3,73 (không phải 3,71); T trung bình Sao Hỏa 214 K; áp suất Sao Hỏa 0,636 kPa; PSR "well below 100 K" (Paige 2010), không dùng "<110 K". Bỏ: "bụi tích điện" (nguồn NASA nói lực tĩnh điện yếu hơn van der Waals), số ánh sáng tán xạ. Gap NASA 2024 đã xác nhận: 0301, 0801, 0805, 1101, 0603, 0307 (Moon); 0802, 1102, 0307 (Mars).
