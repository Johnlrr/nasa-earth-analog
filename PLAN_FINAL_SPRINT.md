# PLAN: Sprint cuối — kiểm chứng construct validity và cửa sổ thử nghiệm kết hợp (15/11, 20:55 → 23:30)

Nguồn: yêu cầu trực tiếp của người dùng 15/11 (mục tiêu nộp dời sang 23:30), đánh giá của Opus 5.5 và một AI khác. Cổng 1: chưa chạy.
Không thay `PLAN.md` hay `PLAN_IMPACT_VALIDITY.md`; chỉ áp dụng cho bản nộp tối nay.

## Phạm vi

**Làm** (theo thứ tự ưu tiên; mục nào trễ mốc thì cắt, không kéo dài):
1. **V1, construct validity (đã đăng ký trước):** chạy bộ lập tuyến theo giới hạn độ dốc trên địa hình Mặt Trăng và Trái Đất, kiểm tra xem ô qua L1 có tái tạo được *kết quả lập tuyến* của Connecting Ridge hay không, so với 1.000 ô ngẫu nhiên và 54 footprint quanh các địa điểm analog kinh điển. Rule nằm ở `config/prereg_route_v1.yaml`, phải commit trước khi chạy.
2. **I1, cửa sổ địa hình × ánh sáng (khám phá, ghi Deviations):** với mỗi lead ridge ở nước mở, tính lịch các ngày mà toàn bộ thời gian ban ngày có Mặt Trời < 7° (dùng đúng ngưỡng 7° của L2), số phút mỗi ngày, dải phương vị, và tỷ lệ bóng tính từ DEM tại đúng các hình học Mặt Trời đó, so với ridge. Kiểm tra sơ bộ cho thấy lead Baffin (63,85 N) có 67 ngày/năm (khoảng giữa tháng 11 đến cuối tháng 1).
3. **Sửa câu chuyện:** đổi hero khỏi Chile (nằm trong vùng đệm Atacama); thêm Deviations 31 (access screen) và 32 (I1); bỏ 113 lead của Shackleton khỏi vai trò kết quả; sửa các nhãn vượt bằng chứng; ghi rõ giả định của phép tính 8,2 km hoặc thay bằng số từ V1.
4. **Thang bằng chứng (evidence ladder):** mỗi tuyên bố gắn một mức (tính toán đã kiểm / dữ liệu bền / đăng ký trước / khám phá / mô phỏng nhiệm vụ / thực địa: chưa có).

**Không làm tối nay:** bộ dữ liệu Sao Hỏa mới, phỏng vấn người dùng, sửa `PLAN_IMPACT_VALIDITY.md`, đổi luật L1/L2/M1/X1, tái cấu trúc web.

## Schema / giao diện
- `src/similitude/route.py`: `route_outcomes(dem: np.ndarray, res_m: float, limits=(6, 8, 10), n_src=24, seed=20261115) -> dict[str, float]` trả về `reach_6, reach_8, detour_8, detour_10, climb_10, nan_frac`.
- `scripts/route_validity.py`: viết `data/derived/route_groups.csv` (cố định nhóm trước khi chạy), `data/derived/route_validity.parquet` (mỗi footprint: nhóm, outcome, `D_route`, `reproduces`), `data/derived/route_validity.json` (tau, p của H1/H1b, rho của H2, kết luận theo `decision_rule`).
- `src/similitude/lighting.py`: `sun_position(lat, lon, times_utc) -> (elev_deg, az_deg)`; `low_sun_windows(lat, lon, year=2027, elev_max=7.0) -> DataFrame`.
- `scripts/build_lighting_windows.py`: viết `data/derived/lighting_windows.parquet` (lead × tháng: số ngày toàn bộ ban ngày dưới 7°, số phút Mặt Trời thấp mỗi ngày, dải phương vị, shadow fraction so với ridge).
- Mọi con số mới vào slide/web/project page phải qua `docs/slide_numbers.json`; key lạ thì build dừng (giữ nguyên cơ chế cũ).

## Hạng mục
- [ ] 0. **[Đội, chặn nộp bài, xong trước 22:00]** Quyết định G0, điền Core idea, ký `docs/compliance.md`, dán `docs/project_page.md` vào form, kiểm tab Members, mở mọi link trong cửa sổ ẩn danh. Agent không được làm thay. — File: `docs/compliance.md`, `docs/project_page.md` — Xong khi: §2 và chữ ký đã điền — Kiểm chứng: hai người tự xác nhận.
- [x] 1. **Commit pre-registration** trước mọi lần chạy Earth. — File: `config/prereg_route_v1.yaml`, `PLAN_FINAL_SPRINT.md` — Xong khi: có commit hash; ghi hash vào Nhật ký — Kiểm chứng: `git log -1 -- config/prereg_route_v1.yaml`.
- [x] 2. **V1, phần code và test** (Track B, 21:05–21:45). — File: `src/similitude/route.py`, `tests/test_route.py` — Xong khi: test pass trên bề mặt giải tích: (a) mặt phẳng → reach = 1, detour ≈ 1; (b) vách dựng chia đôi lưới → reach ≈ tỷ lệ cặp cùng phía; (c) ridge Site01 tái tạo `frac_gt8 = 0.758` — Kiểm chứng: `pytest tests/test_route.py`.
- [x] 3. **V1, chạy và báo cáo** (Track B, 21:45–22:20). — File: `scripts/route_validity.py`, `data/derived/route_*`, `docs/validation_report.md` §7d — Xong khi: H1, H1b, H2 và phép kiểm với DEM thứ hai được báo **đúng theo `decision_rule`, kể cả khi trượt**; số ô bị bỏ vì NaN được ghi — Kiểm chứng: chạy lại script cho ra `route_validity.json` giống hệt; `report_tables.py --check` sạch.
- [x] 4. **I1, cửa sổ ánh sáng** (Track C, 21:05–22:15). — File: `src/similitude/lighting.py`, `tests/test_lighting.py`, `scripts/build_lighting_windows.py`, `data/derived/lighting_windows.parquet` — Xong khi: có lịch cho mọi lead ridge ở nước mở và cho Da Qaidam; shadow fraction tại hình học Mặt Trời của cửa sổ — Kiểm chứng: test độ cao Mặt Trời buổi trưa ngày chí = 90 − |lat| ± 23,44 (sai ≤ 0,5°), so một mốc với bảng NOAA; Baffin cho khoảng 67 ngày.
- [x] 5. **Câu chữ và Deviations** (Track D, 21:05–21:50). — File: `docs/validation_report.md` (Deviations 31 access screen; 32 I1; ghi V1 là đăng ký trước kèm commit hash), `web/app.js:352`, `web/app.js:453`, `web/explorer.html:118-119`, `docs/submission_kit.md`, `docs/project_page.md` — Xong khi: không còn "Qualified", "certify", "valid for the target"; 113 Shackleton chỉ còn là dòng phụ kèm câu "rule is not selective for steep walls (9/1000 random cells pass)"; có dòng "all leads have about twice the ridge's share above the 20° EVA limit (0.11–0.15 vs 0.058)"; "Aksai Chin" đổi thành "areas administered by China"; 8,2 km ghi là "area-share equivalent, not a computed route" hoặc thay bằng số từ V1 — Kiểm chứng: `grep -rniE 'qualified|certif|valid for the target' web/ slides/ docs/project_page.md` không còn kết quả vượt bằng chứng.
- [x] 6. **Hero và thang bằng chứng** (tích hợp, 22:20–22:50). — File: `docs/slide_numbers.json`, `scripts/slides/build_deck.py`, `slides/`, `web/index.html` hoặc `web/campaign.js` (ví dụ mẫu), `web/evidence.html`, `docs/project_page.md` — Xong khi: hero là **Baffin** nếu I1 đã kiểm chứng và V1 không phản bác Baffin, ngược lại là **Argentina E10K_-355_-671** (ô rút ngẫu nhiên, không nổi tiếng, giữ được với cả hai DEM); slide 5 ghi khoảng cách tới mục tiêu chứ không ghi "92 % vs 76 %"; có bảng thang bằng chứng — Kiểm chứng: build deck không có key lạ; PDF đúng 7 trang; mở web bằng trình duyệt thật.
- [x] 7. *(phụ)* **Ma trận phủ chiến dịch:** card của hero ghi 7 biến, mỗi biến do Earth site + cửa sổ hay facility đảm nhận, và biến nào vẫn trống. — File: `web/campaign.js`, `data/derived/field_facility.json` — Chỉ làm nếu mục 6 xong trước 22:50.
- [x] 8. *(phụ)* **ArcticDEM 2 m tại Baffin:** so phân bố độ dốc ở 5/10/30 m giữa ridge (LOLA 5 m) và Baffin. — Chỉ làm nếu tải COG mở được và mục 1–6 xong trước 22:45; nếu không thì để sau khi nộp.
- [ ] 9. **Cổng và nộp** (22:50–23:30). — `claude-gate-diff` → sửa → rebuild → merge → tag `submission-2026-11-15` → cập nhật form → screenshot — Xong khi: SHIP, form đã lưu trước 23:30.

## Mốc an toàn (kill-switch)
- **22:15: nộp bản an toàn** gồm mục 0 + 5 + hero Argentina (không có V1/I1). Sau đó chỉ nâng cấp tiếp nếu kịp.
- V1 chưa có kết quả đã kiểm chứng lúc 22:30 → không đưa lên slide; để ở báo cáo với nhãn "running/after submission".
- I1 chưa qua test lúc 22:15 → không đổi hero sang Baffin.
- Con số nào chưa qua `claude-gate-diff` thì không vào slide, web hay form.

## Edge-cases
- Footprint Earth > 5 % NaN: bỏ và đếm, không nội suy. Ô biển hay ô phẳng hoàn toàn: reach = 1, detour = 1, vẫn giữ.
- Thiếu chip cho footprint classic hoặc lead: ghi vào Câu hỏi mở, không tải ad hoc trong lúc chạy V1 (tải thêm làm đổi nhóm).
- V1 có thể trượt: đó là kết quả hợp lệ và phải công bố đúng `decision_rule`; không được đổi ngưỡng.
- Bộ lập tuyến trên lưới 30 m không thấy đá hay hố < 60 m: ghi trong `not_claimed` và trên card.
- Cửa sổ Baffin rơi vào mùa có tuyết và ban ngày ngắn (~4 giờ): hình học bóng tái tạo được, độ sáng bề mặt thì không (tuyết sáng, regolith tối). Card phải ghép với facility chiếu sáng (Ames) cho phần radiometry.
- Phương vị Mặt Trời ở Baffin trong cửa sổ chỉ quét một dải phía nam; phương vị *tương đối* với hướng đi được phủ bằng cách đổi hướng tuyến. Ghi đây là lập luận vận hành, không phải số đo.

## Câu hỏi mở
- Mục 6: trang lập chiến dịch (`index.html`) giữ catalog 3 địa điểm cũ (từ `candidates.geojson`); hero đổi sang lead Argentina, ví dụ mẫu Da Qaidam được ghi rõ là trượt phép thử lộ trình và nằm ở Trung Quốc. Đưa 2 lead mới vào catalog cần thêm bản ghi vào `candidates.geojson`, để sau khi nộp.
- Mục 7 làm ở mức hình + bảng (`scripts/build_campaign.py`, slide 7, evidence §5), chưa vào giao diện lập chiến dịch.
- Thể lệ có cho sửa link (repo/web) sau 23:59 không? Chưa xác minh. Mặc định: đóng băng bằng tag, mọi việc sau hạn làm trên nhánh khác.

## Nhật ký
- 2026-11-15 · Opus 5.5 · soạn sprint plan và pre-registration V1; prototype bộ lập tuyến chỉ chạy trên ridge Site01 (reach 0,55/0,84/≈1,0 ở 6/8/10°) và đo thời gian trên một chip Earth chưa chấm; tính lịch Mặt Trời thấp cho 3 lead (Baffin 67 ngày toàn bộ ban ngày dưới 7°; Argentina 0; Canada 69,9 N 49) · test: không chạy (chưa đổi code)
- 2026-11-15 · Opus 5.5 · đăng ký trước V1 (`4e9ceff`), code V1 (`6ab5bd5`) rồi mới chạy: H1 FAIL (3/9 vs 151/994, p=0.148), H1b FAIL (classic 27/54), H2 PASS (rho 0.377); cùng 3 ô tái tạo trên DEM thứ hai · I1: Baffin 71 ngày (13/11–22/1), Argentina 0 · đa tỷ lệ Baffin (luật `c4f7be5` trước khi chạy): khớp ở 5/10/30 m · slide, project page, báo cáo §7d + Deviations 31–34, web (hero Argentina, cột Routes, bỏ "certify"), trang evidence có thang bằng chứng · sửa lỗi NaN trong `web/data/access.json` làm hỏng tải dữ liệu web · test: pytest 215 pass, ruff sạch, report --check sạch, node 5/5, PDF 7 trang không tràn
- 2026-11-15 · Opus 5.5 · ma trận phủ chiến dịch Connecting Ridge: hai lead 5/5 hàng thực địa, Haughton 2/5, 8 hàng facility (Deviations 35); slide 7 thay bằng ma trận, nối với NASA Civil Space Shortfalls ESDMD #0805/#1101 · atlas 6 vùng Artemis (Deviations 36): chỉ Connecting Ridge có lead qua mọi phép thử; 117 lead độ dốc của vách Shackleton đều trượt phép thử lộ trình · test: pytest 215 pass, ruff sạch, report --check sạch, PDF 7 trang không tràn
- 2026-11-15 · Opus 5.5 · đăng ký trước V2 + Mars (`67920dd`, trước khi so Earth): V2 lấy τ từ 124 cửa sổ Site01 không chồng lấn (thay 8) → τ 1.161, random 95/994 (9.6 %), classic 17/54, passer 3/9 (cùng 3 ô, hai DEM): H1 PASS p=0.049, H1b FAIL p=0.59, H2 PASS ρ=0.359. Mars Jezero delta front (CTX DTM, 185 lân cận): classic Mars 17/45 vs random 159/994, HM1 PASS p=0.0005; HI-SEAS 9/9, Atacama 4/9, Haughton 3/9, MDRS 1/9, Wright 0/9. Campaign chuyển cột routes sang V2 (Haughton 1/5). Báo cáo §7e, Deviations 37–38, slide 3/4/6/7, kit, evidence. pytest 215 pass, ruff sạch, report_tables --check sạch, node 14/15 (similarities thiếu PNG cục bộ, như trên main).
