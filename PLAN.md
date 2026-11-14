# PLAN: SIMILITUDE — MVP 48 giờ cho đội 2 người

Nguồn: `DESIGN.md` (14/11/2026)  ·  Cổng 1: APPROVE 14/11/2026, lần chạy thứ 4 (xem Nhật ký)
Soạn: 14/11/2026 11:30 (UTC+7), Opus 5.5 (planner). Cập nhật 11:45: phân vai, tài khoản, quy tắc nhánh.

**Thành viên:** **A = Bảo** · **B = Linh**. Trong toàn bộ file, nhãn [A] là việc của Bảo, [B] là việc của Linh.

## Phạm vi

### Làm (MVP cho 2 người)
| Lens | Thiên thể | Pipeline | Chủ |
| :--- | :--- | :--- | :--- |
| L1 Touchdown & Traverse | Moon | Terrain | A |
| L2 Low-Sun Navigation | Moon | Terrain + thiên văn | A |
| M1 Aqueous Minerals | Mars | Spectral | B |
| X1 Ice under Dry Overburden | Mars (+ Moon ở dạng ledger) | Ice, **bản rút gọn bán định lượng** | B |

Kèm theo: fidelity engine (σ-dissimilarity, yếu tố giới hạn, cờ no-analog), validation harness (đối chứng dương, mồi nhử, phân bố null, ablation hai nhánh), Transfer Ledger, Attention Index, `candidates.geojson`, web tĩnh với Test Card, 7 slide, trang Project.

### Không làm (cắt sẵn vì đội 2 người, theo thứ tự cắt của DESIGN mục 5)
- Lens M2 (gió/bụi) và L3 (anorthosite/TIR).
- Embedding AlphaEarth và nhánh (b) của ablation. Ablation chỉ so (a) RGB/texture với (c) twin-formula.
- Chế độ Coverage/Gap, X1 bản đầy đủ, lưới toàn cầu 30 m, xử lý cube CRISM thô.
- **Tùy chọn, chỉ làm nếu dư giờ sau Code Freeze trừ 3 giờ:** Near-me, chỉ số tiếp cận (Oxford MAP + WDPA), so sánh cạnh nhau bằng WMTS Moon/Mars Trek (đường lùi: ảnh tĩnh).

### Nguyên tắc song song
1. **Chia theo lát dọc, không theo tầng.** A sở hữu trọn pipeline Terrain (mục tiêu Moon → dữ liệu Trái Đất → descriptor) và fidelity engine. B sở hữu trọn pipeline Spectral + Ice, discovery và phần trình bày. Hai người chỉ gặp nhau ở các file hợp đồng trong mục "Schema / giao diện".
2. **Khóa hợp đồng trước 13:45** (schema bảng, `lenses.yaml`, GeoJSON mẫu). Sau đó mỗi bên làm việc với dữ liệu giả của bên kia, không chờ nhau.
3. **Mỗi người chạy song song một agent** (Antigravity hoặc `claude-agy`) cho các hạng mục gắn nhãn `[agent]`: code thuần có test rõ ràng. Người giữ phần cần phán đoán khoa học và thao tác tài khoản (GEE, Earthdata).
4. **Việc chạy lâu (export GEE, tải EMIT) khởi động sớm nhất có thể** và chạy nền trong lúc làm việc khác hoặc ngủ.

### Quy tắc Git và nhánh
1. **Mỗi người code trên nhánh riêng, tạo ngay khi bắt đầu triển khai** (sau khi pull `main` có `PLAN.md` này):
   - Bảo: `git switch -c bao/terrain-engine`
   - Linh: `git switch -c linh/spectral-story`
   Agent của ai thì chạy trên nhánh của người đó.
2. **Trên nhánh cá nhân được commit tự do** và nên `git push -u origin <nhánh>` thường xuyên để có bản sao lưu. Commit không ghi danh AI (AGENTS.md quy tắc 6).
3. **`main` chỉ nhận merge qua Pull Request tại các mốc:** 13:45 (khóa hợp đồng), 22:00 (CP1), 03:00 (DF), 15:00 (CF). Trước mỗi lần merge: `make test && make lint` sạch và chạy `claude-prereview`; tại DF và CF chạy thêm `claude-gate-diff` (cổng 2) và chỉ merge khi SHIP.
4. **Sau mỗi lần merge vào `main`, người còn lại chạy `git merge main`** vào nhánh của mình ngay.
5. **Thứ tự của mốc khóa hợp đồng:** Bảo làm A0 trên nhánh mình, mở PR và merge vào `main` khoảng 13:15. Linh soạn các file cấu hình/schema của B0 trên nhánh mình ngay từ đầu, `git merge main` sau khi A0 vào `main`, viết `io.py` + test, rồi mở PR merge trước 13:45.
6. **Sở hữu file** (chỉ chủ sở hữu sửa; người kia cần đổi thì báo trước hoặc ghi vào Câu hỏi mở):

| Bảo (A) | Linh (B) | Dùng chung |
| :--- | :--- | :--- |
| `pyproject.toml`, `Makefile`, `README.md`, `LICENSE` | `config/*`, `schemas/*`, `ledger/*` | `PLAN.md`: mỗi người chỉ đánh dấu hạng mục của mình và ghi vào mục Nhật ký của mình |
| `descriptors/terrain.py`, `descriptors/astro.py` | `descriptors/spectral.py`, `descriptors/ice.py` | |
| `fidelity.py`, `validation.py`, `scripts/run_all.py` | `io.py`, `discovery.py` | |
| `scripts/targets/moon_*`, `scripts/gee/{tier1_terrain,chip_dem,tier2_lowsun}.py` | `scripts/targets/mica_*`, `scripts/emit/*`, `scripts/gee/tier_x1.py`, `scripts/attention/*` | |
| `docs/validation_report.md`, `docs/figures/*` | `web/*`, `.github/workflows/*`, slide, `docs/compliance.md` | |
| `config/seeds.yaml`, `config/exclusion_zones.yaml` | | |
| `tests/test_<module>.py` theo chủ của module | `tests/test_<module>.py` theo chủ của module | |
| `notebooks/bao_*.ipynb` | `notebooks/linh_*.ipynb` | |

Mọi thư viện cần dùng được khai báo hết trong A0. Linh cần thêm thư viện thì nhờ Bảo thêm vào `pyproject.toml`, tránh xung đột.

### Lịch song song (UTC+7)
| Khung giờ | Bảo (A) — Terrain + Engine | Linh (B) — Spectral + Ice + Story | Cổng |
| :--- | :--- | :--- | :--- |
| 11:45–12:45 | 0.2 tạo tài khoản; 0.1 tuân thủ (cùng Linh) | 0.2 tạo tài khoản; 0.1 tuân thủ (cùng Bảo) | **G0** quyết định SI + tài khoản dùng được |
| 12:45–13:45 | A0 khung repo, merge vào `main` ~13:15 | B0 hợp đồng dữ liệu + GeoJSON mẫu, merge trước 13:45 | Khóa hợp đồng 13:45 (dời 15 phút do cổng 1 chạy 3 lần) |
| 13:45–16:00 | A1 descriptor terrain `[agent]`; A2 khởi chạy export GEE tầng thô; A3 spike Moon (R4); A4 spike Earth (R5) | B1 descriptor phổ `[agent]`; B2 MICA; B3 spike EMIT (R2/R3); B4 web khung `[agent]` | **G1** 16:00 chốt lens |
| 16:00–22:00 | A5 fidelity engine `[agent]`; A6 chip DEM tầng mịn; A7 descriptor L2 | B5 ứng viên M1 + trích phổ EMIT; B6 X1 rút gọn; B7 Transfer Ledger; B8 Attention Index `[agent]` | Checkpoint 22:00 |
| 22:00–03:00 | A8 chấm điểm + validation | B9 discovery + xuất GeoJSON; B10 viết Test Card | **Data Freeze** 03:00 |
| 03:00–07:30 | Ngủ (agent chạy B11 trên dữ liệu thật) | Ngủ | — |
| 07:30–15:00 | A9 báo cáo validation + hình; A10 README + trích dẫn | B11 web hoàn thiện; B12 slide nháp | **Code Freeze** 15:00 |
| 15:00–21:00 | 5.1–5.3 cùng B | 5.1–5.3 cùng A | **Nộp** trước 21:00 |

Nếu một người buộc phải ngủ sớm hơn: ngủ ca 23:00–03:00, người kia ngủ 03:00–07:00, và export GEE / tải EMIT phải được khởi chạy trước ca ngủ.

## Schema / giao diện

### Cấu trúc repo
```
pyproject.toml  Makefile  LICENSE (Apache-2.0)  README.md
config/lenses.yaml  config/targets.yaml  config/controls.yaml
ledger/moon.yaml  ledger/mars.yaml
schemas/candidate.schema.json
src/similitude/
  descriptors/terrain.py   descriptors/spectral.py   descriptors/astro.py   descriptors/ice.py
  fidelity.py  validation.py  discovery.py  io.py
scripts/targets/  scripts/gee/  scripts/emit/  scripts/attention/
data/raw/ (gitignore)  data/derived/ (parquet nhỏ, commit được)
web/index.html  web/app.js  web/style.css  web/data/candidates.geojson  web/data/candidates.mock.geojson
docs/compliance.md  docs/validation_report.md  docs/figures/
tests/
```
Lệnh chuẩn: `make test` = `pytest -q`; `make lint` = `ruff check .`.

**Quy tắc nguồn duy nhất:** mọi công thức descriptor chỉ nằm trong `src/similitude/descriptors/`. Script phía Trái Đất và phía Moon/Mars chỉ được import, không tự viết lại công thức. Đây là cơ sở của khẳng định "same formula, both worlds"; cổng 2 sẽ kiểm tra điều này.

### Chữ ký hàm
```python
# descriptors/terrain.py
def aggregate_to_baseline(dem: np.ndarray, res_m: float, L_m: float) -> np.ndarray
def slope_stats(dem: np.ndarray, res_m: float) -> dict[str, float]
    # keys: slope_p50, slope_p90, frac_gt8, frac_gt15, frac_gt20 (độ, tỷ lệ 0–1)
def roughness_spectrum(dem, res_m, scales=(1, 2, 4, 8, 16)) -> dict[str, float]
    # keys: rms_s1..rms_s16 (độ lệch RMS sau khử xu hướng), hurst
def shadow_fraction(dem, res_m, sun_elev_deg=(2, 5, 7), n_az=16, max_dist_m=3000.0,
                    radius_m=None, exclude_border_m=None) -> dict[str, float]
    # keys: shadow_e2, shadow_e5, shadow_e7 (trung bình mọi phương vị)
    # thống kê chỉ trên vùng trong, bỏ viền rộng exclude_border_m (mặc định = max_dist_m)
def terrain_descriptors(dem, res_m, L_m, radius_m=None, footprint_m=None) -> dict[str, float]
    # gộp ba hàm trên ở baseline L; slope/roughness tính trên footprint trung tâm,
    # shadow dùng cả chip làm vùng đệm. L_m bắt buộc.

# descriptors/astro.py
def low_sun_hours(lat_deg, max_elev_deg=7.0, obliquity_deg=23.44) -> dict[str, float]
    # keys: lowsun_frac_time, lowsun_frac_daylight, lowsun_az_coverage (0–1), lowsun_hours_yr (chỉ Trái Đất)
    # cùng công thức cho Mặt Trăng: obliquity_deg=1.54

# descriptors/spectral.py
COMMON_WL_NM: np.ndarray   # 400–2490 nm, bước 10 nm, đã bỏ 1340–1460 và 1790–1960 nm
PARAM_TABLE: dict          # mỗi tham số: mốc gốc Viviano-Beck 2014 và mốc thay thế (nếu mốc gốc rơi vào dải bị che)
def resample(wl_nm: np.ndarray, refl: np.ndarray) -> np.ndarray       # về COMMON_WL_NM
def crism_params(refl: np.ndarray, subset: str = "swir") -> dict[str, float]  # "swir" (M1 mặc định) | "all"
def sam(a: np.ndarray, b: np.ndarray, window_nm=(2100, 2490)) -> float  # radian, sau khử continuum
    # bắt đầu từ 2100 nm để tránh dư CO2 ~1950–2080 nm trong phổ CRISM; band depth dùng trung bình
    # cửa sổ 3 kênh quanh mỗi mốc (kênh EMIT > 2450 nm có SNR thấp); áp dụng giống nhau hai phía

# descriptors/ice.py
def ice_config(maat_c, active_layer_m, aridity_p_pet, freeze_thaw_per_yr) -> dict[str, float]

# fidelity.py
@dataclass
class Metric: mean: np.ndarray; cov_inv: np.ndarray; scale: np.ndarray; mode: str  # "full" | "pca" | "diag"
def fit_population(X_pop: np.ndarray, min_scale: np.ndarray, mode: str = "auto") -> Metric
    # auto: full nếu n ≥ 5·K, ngược lại diag. Độ lệch chuẩn mỗi chiều = max(std quần thể, min_scale);
    # min_scale là dung sai vật lý khai báo trong lenses.yaml, chống Σ suy biến khi một descriptor gần hằng số
    # Σ = D·R·D với D = diag(max(std, min_scale)); R = ma trận tương quan, cột suy biến (std ≈ 0) có tương quan 0
def mahalanobis_d(E: np.ndarray, t: np.ndarray, m: Metric) -> np.ndarray    # khoảng cách d thô
def sigma_dissimilarity(E: np.ndarray, t: np.ndarray, m: Metric) -> np.ndarray
    # quy ước Mahony 2017, tính bằng đuôi phải để không tràn số: σ = chi(1).isf(chi(K).sf(d));
    # nếu sf underflow thì dùng logsf và trả giá trị chặn kèm cờ σ_capped (hiển thị "> X σ").
    # σ nhỏ = giống hơn. σ CHỈ để hiển thị: mọi xếp hạng, percentile, top-k, NMS dùng d thô
    # (cùng K thì đơn điệu với σ). percentile của một ô = tỷ lệ ô null có d LỚN HƠN ô đó (100 = tốt nhất)
def limiting_factor(E, t, m, names: list[str]) -> list[str]           # descriptor có độ lệch chuẩn hóa lớn nhất
def score_lens(earth: pd.DataFrame, targets: pd.DataFrame, lens: dict) -> pd.DataFrame

# validation.py
def control_percentiles(scores, controls) -> pd.DataFrame
def ablation(feature_sets: dict[str, pd.DataFrame], controls, k=(1, 5, 10)) -> pd.DataFrame  # recall@k, thứ hạng TB
def sensitivity(earth, targets, lens, perturbations) -> pd.DataFrame  # độ ổn định top-10 (Jaccard)
```

### Bảng dữ liệu (parquet trong `data/derived/`)
| Bảng | Cột bắt buộc |
| :--- | :--- |
| `targets_<lens>.parquet` | `target_id, body, lens_id, footprint_id, is_reference (bool), lat, lon, L_m, source,` + cột descriptor. Hàng `is_reference=False` là quần thể dùng để ước lượng Σ |
| `earth_<lens>.parquet` | `cell_id, lat, lon, footprint_km, lens_id, tier (1/2), L_m, source, qa_flag, sample_role (rank / null / control / decoy / seed), in_exclusion_buffer (bool),` + cột descriptor. Hàng `sample_role=null` là mẫu ngẫu nhiên phân tầng, **chỉ** dùng làm phân bố null |
| `fidelity.parquet` | `cell_id, lens_id, target_id, d, sigma, sigma_capped (bool), metric_mode, percentile (nullable: trống khi mẫu null < 30 ô), limiting_factor, no_analog (bool), feature_set`. L2 có thêm `d_shadow`, `sigma_shadow` (chỉ các descriptor `shadow_*`) để báo riêng phần địa hình khi phần thiên văn ra no-analog |
| `attention.parquet` | `name, query, n_pubs, source, date` |

`candidates.geojson`: theo DESIGN 2.4, bắt buộc có `evidence_status ∈ {engine-confirmed, engine-semiquant, literature-only, hypothesis}`. `engine-semiquant` dành cho X1 (so cấu hình, không phải σ đầy đủ). Được lên slide: `engine-confirmed` và `engine-semiquant`, nhãn hiển thị phải ghi rõ trạng thái. File `schemas/candidate.schema.json` là chuẩn kiểm tra; trong `lens_scores`, `percentile` cho phép `null`, và có thêm `d`, `sigma_capped`.

### Cấu hình
- `config/lenses.yaml`: theo DESIGN 2.4 (`id, body, footprint_km, baseline, descriptors, min_scale, gates, targets, ledger`). `min_scale` là dung sai vật lý theo từng descriptor (gợi ý: dốc 1°, tỷ lệ diện tích 0,05, `rms_s*` 10 % giá trị mục tiêu, `hurst` 0,05, `shadow_*` 0,05, `lowsun_*` 0,05, band depth 0,01). **Footprint L1 = L2 = 4 km** (đường kính vùng EVA bán kính 2 km), chip = footprint + vùng đệm 3 km mỗi phía (10 km); quy tắc này áp dụng giống nhau cho Trái Đất và Mặt Trăng.
- `config/targets.yaml`: tọa độ/ROI của mục tiêu. Moon: Connecting Ridge, vành Shackleton (L1/L2), PSR Shackleton (X1, chỉ ledger). Mars: Jezero rìa carbonate, Oxia Planum, Meridiani (M1); Arcadia Planitia (X1).
- `config/controls.yaml`: đối chứng dương (≥10 cặp, theo DESIGN 2.2(5) + NASA Analog Explorer) và mồi nhử (Wadi Rum, cát đỏ thạch anh nội địa Úc), mỗi mục ghi `lens_id, lat, lon, footprint_km, source, expected (high / uncertain / low)`. **Kỳ vọng được ghi trước khi có kết quả và khóa cùng hợp đồng lúc 13:45**; không được đổi danh sách đối chứng hay kỳ vọng sau khi đã xem kết quả. Gợi ý: Kilauea và trường dung nham California là analog biển mare nên với L1 (cao nguyên cực) ghi `uncertain`; Haughton/Devon ghi `high`.

## Hạng mục

Nhãn: **[A]** / **[B]** = chủ sở hữu; **[agent]** = giao được cho agent, người chủ duyệt; **Chờ** = phụ thuộc.

### Giai đoạn 0 — Tài khoản, tuân thủ và hợp đồng (11:45–13:45)
- [ ] 0.2. **[A+B] Tạo tài khoản — điều kiện chặn của A2, A3, A6, B3, B5, B6.** Mỗi người tự làm cho mình:
  - **NASA Earthdata Login:** đăng ký tại https://urs.earthdata.nasa.gov/users/new (cấp ngay); tạo file `~/.netrc` hoặc dùng `earthaccess.login(persist=True)`.
  - **Google Earth Engine:** tạo Google Cloud project, đăng ký Earth Engine loại phi thương mại (noncommercial / research) tại https://code.earthengine.google.com/register, bật Earth Engine API cho project đó; xác thực bằng `earthengine authenticate`. Ghi tên project vào biến môi trường `EE_PROJECT` (không commit vào repo).
  - Xong khi: chạy được `python -c "import earthaccess; earthaccess.login()"` và `python -c "import ee, os; ee.Initialize(project=os.environ['EE_PROJECT']); print(ee.Number(1).getInfo())"`.
  - Kiểm chứng: mỗi người ghi một dòng xác nhận vào Nhật ký của mình (không ghi mật khẩu, token, email).
  - **Nếu GEE chưa được duyệt trước 13:45:** Bảo lấy DEM Copernicus GLO-30 từ bucket công khai trên AWS (`s3://copernicus-dem-30m`, không cần tài khoản) cho A4/A6, thay tầng thô toàn cầu A2 bằng danh sách hạt giống `config/seeds.yaml`, lấy mẫu null 200 ô đất trơ bằng ESA WorldCover trên AWS (`s3://esa-worldcover`) + DEM AWS, và lấy Sentinel-2 cho ablation (a) qua Element84 STAC (hoặc bỏ nhánh này). Linh dùng `earthaccess` để tải EMIT trực tiếp, giới hạn ≤ 30 footprint. Ghi quyết định vào Câu hỏi mở.
- [ ] 0.1. **[A+B]** Đọc nguyên văn Project Submission Guide, FAQ phần SI, trang đề (tab Resources, 12 Considerations, giới hạn 7 slide / 30 s); hỏi Local Lead nếu điều khoản SI mơ hồ. Đội tự quyết phần ý tưởng nào giữ, sửa, bỏ và ghi lại cách đã dùng SI — File: `docs/compliance.md` — Xong khi: có quyết định G0 bằng văn bản (tiếp tục / điều chỉnh ý tưởng), danh sách tài nguyên chính thức, định dạng nộp đã xác nhận — Kiểm chứng: hai người cùng đọc và ký tên trong file.
- [x] A0. **[A]** Khung repo: `pyproject.toml` (Python ≥3.11; numpy, scipy, pandas, pyarrow, rasterio, xarray, netCDF4, pyyaml, jsonschema, earthaccess, earthengine-api, requests; dev: pytest, ruff), `Makefile`, `LICENSE` Apache-2.0, `.gitignore` có `data/raw/`, README khung, gói `src/similitude` rỗng — Xong khi: cài được bằng `pip install -e .[dev]`, PR đã merge vào `main` — Kiểm chứng: `make test` (0 test, không lỗi) và `make lint` sạch.
- [ ] B0. **[B]** Hợp đồng dữ liệu: `config/lenses.yaml`, `config/targets.yaml`, `config/controls.yaml`, `schemas/candidate.schema.json`, `web/data/candidates.mock.geojson` (3 feature giả đủ mọi trường, mỗi lens ít nhất một), `src/similitude/io.py` có `validate_candidates(path)` — Chờ: A0 (chỉ phần `io.py`; file cấu hình/schema soạn được ngay) — Xong khi: hai người đồng ý, PR đã merge vào `main`, không đổi schema sau 13:45 nếu không báo cả hai — Kiểm chứng: `pytest tests/test_schema.py` (file mẫu hợp lệ; thiếu `evidence_status` thì báo lỗi).

### Giai đoạn 1 — Thư viện và phép thử (13:45–16:00)
- [x] A1. **[A][agent]** `descriptors/terrain.py` + `descriptors/astro.py` theo chữ ký trên — File: `src/similitude/descriptors/{terrain,astro}.py`, `tests/test_terrain.py`, `tests/test_astro.py` — Xong khi: mọi test pass — Kiểm chứng: `pytest tests/test_terrain.py tests/test_astro.py`, gồm: mặt phẳng nghiêng 10° → `slope_p50` = 10 ± 0,1; mặt phẳng → `shadow_*` = 0 và `frac_gt8` = 0; mặt fBm tổng hợp 1024×1024, seed cố định, H = 0,7 → `hurst` = 0,7 ± 0,15; `aggregate_to_baseline` 5 m → 30 m giữ trung bình; vĩ độ 0° → `lowsun_frac_daylight` < vĩ độ 85°; Mặt Trăng (−89,5°, obliquity 1,54°) → `lowsun_frac_daylight` = 1.
- [x] A2. **[A]** Export GEE tầng thô toàn cầu ở 10 km cho các lens terrain, chia lô theo bbox lục địa, tính trên DEM 90 m (Copernicus GLO-30 qua `reduceResolution`, dốc bằng `ee.Terrain.slope`):
  - Mặt nạ đất trơ: MODIS NDVI, ESA WorldCover, loại nước/đô thị/canh tác. Thêm khô hạn và MODIS snow cho L2.
  - Descriptor thô mỗi ô: `slope_p50`, `frac_gt8`, `frac_gt20` ở 90 m. Mục tiêu Moon được tính **cùng cách** (A3 gộp về 90 m) để xếp hạng sơ bộ bằng σ đường chéo.
  - Vùng đệm quanh 4 điểm kinh điển và các điểm NASA Analog Explorer: **chỉ gắn cờ `in_exclusion_buffer`, không xóa ô**. Chỉ B9 mới lọc theo cờ này.
  - File: `scripts/gee/tier1_terrain.py`. **Khởi chạy trước 14:15**, cho chạy nền.
  - Xong khi: CSV ô ứng viên tải về `data/derived/tier1_terrain.csv`.
  - Kiểm chứng: số ô > 0; các đối chứng dương L1/L2 (vd Devon Island, Haughton) nằm trong mặt nạ và có mặt trong CSV (có cờ nếu nằm trong vùng đệm).
  - Đường lùi (R7): danh sách hạt giống ~150 footprint (hố va chạm, trường núi lửa Holocene, cao nguyên cực) trong `config/seeds.yaml`.
- [x] A3. **[A]** Spike R4 — mục tiêu Moon từ PGDA Product 78 (DEM 5 m, phép chiếu cực nam; đã tải về `data/raw/moon/pgda78/` cho Site01 Connecting Ridge, Site04 Shackleton rim, Site06, Site07, Site11, Site23):
  - Gộp DEM về L = 30 m. Lấy footprint 4 km + vùng đệm 3 km.
  - Mục tiêu (`is_reference=True`): tâm Site01 và Site04.
  - Quần thể Σ: lưới footprint 4 km không chồng lấn (chip 10 km được phép chồng nhau), chip nằm trọn trong site, lấy ở cả 6 site, ≥ 30 footprint; không đủ thì giảm bước lưới xuống 3 km và ghi chú. Ghi rõ quần thể là "địa hình các vùng ứng viên hạ cánh Artemis".
  - Tính thêm descriptor thô ở 90 m **trên cửa sổ 10 km** (bằng ô của A2) cho xếp hạng sơ bộ: `slope_p50_90m`, `frac_gt8_90m`, `frac_gt20_90m`, `relief_90m`. Ghi chú: tầng thô phía Trái Đất tính bằng `ee.Terrain.slope` trên GEE, nên chỉ dùng để lọc sơ bộ; mọi con số fidelity công bố đều tính bằng thư viện chung ở tầng mịn.
  - **Tải một chip ảnh LROC** (mosaic cực nam qua Moon Trek WMTS) cho mỗi mục tiêu, phục vụ ablation (a).
  - File: `scripts/targets/moon_terrain.py` → `data/derived/targets_L1.parquet`, `data/derived/targets_L1_coarse.parquet`, `data/raw/moon/lroc_chips/`.
  - Chờ: A1 (có thể viết script song song, chạy sau).
  - Xong khi: bảng đủ cột theo schema.
  - Kiểm chứng: trung vị dốc khác file `*_slp.tif` của PGDA (gộp cùng cách) ≤ 2°. Trượt → dùng thẳng sản phẩm dốc PGDA, ghi vào Câu hỏi mở. Không lấy được ảnh LROC trước G1 → bỏ ablation (a), ghi vào Nhật ký.
- [x] A4. **[A]** Spike R5 — tách biệt địa hình: chip DEM 10 km (footprint 4 km + đệm, chiếu về UTM cục bộ) cho 5 điểm Trái Đất (2 đối chứng dương L1 có `expected: high` + 3 ngẫu nhiên trên đất trơ), tính descriptor, tính σ thô (dạng đường chéo có `min_scale`) so với mục tiêu Connecting Ridge — File: `scripts/gee/chip_dem.py`, `scripts/spike_r5.py` — Chờ: A1, A3 — Xong khi: có bảng σ cho 5 điểm — Kiểm chứng: cả hai đối chứng dương có σ nhỏ hơn cả ba điểm ngẫu nhiên. Trượt → thêm `roughness_spectrum` hoặc thu footprint về 2 km, ghi kết quả vào Nhật ký.
- [ ] B1. **[B][agent]** `descriptors/spectral.py` theo chữ ký trên, tham số lấy theo Viviano-Beck 2014:
  - **Trước khi code**, soạn `PARAM_TABLE` ghi mốc gốc và mốc thay thế của từng tham số, rồi để Linh duyệt. Mốc thay thế dùng **giống nhau ở cả hai phía**. Chú ý: `D2300` (mốc 1815/1862 nm) và `OLINDEX` (mốc 1404/1417 nm) có mốc rơi vào dải bị che nên phải thay. `MIN2295_2480` cần lưới lên tới 2490 nm; `MIN2345_2537` vượt biên EMIT (2500 nm) nên thay mốc 2537 bằng 2490 hoặc bỏ, và ghi rõ.
  - `subset="swir"` (mặc định cho M1) chỉ gồm tham số trong 1000–2490 nm. Tham số VNIR chỉ dùng khi phổ mục tiêu có VNIR.
  - File: `src/similitude/descriptors/spectral.py`, `tests/test_spectral.py`.
  - Xong khi: test pass; `PARAM_TABLE` có đủ mốc gốc và mốc thay.
  - Kiểm chứng: `pytest tests/test_spectral.py`, gồm: phổ phẳng → mọi band depth ≈ 0; hấp thụ Gauss ở 2300 nm → `D2300` > 0,05 và `BD2210` ≈ 0; hấp thụ ở 2210 nm → ngược lại; **phổ carbonate tổng hợp có hai hấp thụ ở 2300 và 2500 nm → `MIN2295_2480` > 0, trong khi phổ chỉ có 2300 nm → `MIN2295_2480` ≈ 0**; `sam(a, a)` = 0.
- [ ] B2. **[B]** Nạp MICA: tải volume `mrocr_8001` (~3 MB) từ PDS Geosciences / crismtypespectra.rsl.wustl.edu.
  - **Trong 30 phút đầu, kiểm loại phổ.** MICA cung cấp phổ tỷ số (ratioed I/F) và phổ tử số (numerator, chưa chia). Ưu tiên phổ tử số khi so với phản xạ EMIT; ghi lại phổ nào chỉ có dải IR.
  - Cắt ≤ 2490 nm, `resample`, tính `crism_params(subset="swir")`.
  - **Tải một chip ảnh CTX** cho Jezero qua Mars Trek, phục vụ ablation (a).
  - File: `scripts/targets/mica_ingest.py` → `data/derived/mica.parquet`, `data/derived/targets_M1.parquet`, `data/raw/mars/ctx_chips/`.
  - Chờ: B1.
  - Xong khi: có vector mục tiêu cho các lớp carbonate (Jezero), Fe/Mg-smectite (Oxia/Mawrth), olivine, jarosite (Meridiani); toàn bộ phổ MICA dùng được làm quần thể Σ.
  - Kiểm chứng: phổ carbonate có `MIN2295_2480` > 0, phổ olivine có `OLINDEX` (bản đã thay mốc) cao nhất nhóm.
- [ ] B3. **[B]** Spike R2/R3 — CRISM trên EMIT: (i) **ngay đầu tiên** xác định EMIT L2A có trên GEE không và ID là gì (`NASA/EMIT/L2A_RFL` hay `NASA/EMIT/L2A/RFL`). Nếu không có trên GEE: dùng `earthaccess.open` để đọc lười, chỉ lấy cửa sổ footprint, và áp bảng GLT để có tọa độ, vì L2A chưa trực chiếu và mỗi granule khoảng 1,7 GB; (ii) tìm cảnh ít mây tại Lake Salda, một điểm peridotit Semail (Oman), Wadi Rum, Harrat Khaybar, Matanomadh; (iii) lấy phổ trung vị footprint (bỏ pixel mây/nước/thực vật), tính tham số — File: `scripts/emit/spike_r2.py`, `notebooks/linh_spike_r2.ipynb` — Chờ: B1, B2 — Xong khi: có bảng tham số + σ so với mục tiêu carbonate/olivine — Kiểm chứng (**tiêu chí G1 cho M1**): **đo thời gian đọc một footprint trước** rồi mới cam kết số footprint của B5; Lake Salda và Semail có σ nhỏ hơn Wadi Rum so với mục tiêu Jezero. Trượt → đường lùi theo thứ tự: sản phẩm EMIT L2B mineral (LP DAAC) → chỉ số SWIR Sentinel-2 + ASTER GED.
- [ ] B4. **[B][agent]** Web khung đọc `candidates.mock.geojson`: bản đồ MapLibre hoặc Leaflet, bộ chọn lens, marker tô màu theo σ, panel Test Card hiển thị đủ trường (fidelity theo lens, yếu tố giới hạn, quá trình, test here / cannot test, attention, evidence status, nguồn dữ liệu); không backend. Kèm **workflow GitHub Actions `.github/workflows/pages.yml`**: khi push lên `main`, copy `web/` cùng `docs/validation_report.md` và `docs/figures/` vào một thư mục build rồi deploy lên GitHub Pages (`actions/upload-pages-artifact` + `actions/deploy-pages`); repo Settings → Pages chọn nguồn "GitHub Actions" — File: `web/index.html`, `web/app.js`, `web/style.css`, `.github/workflows/pages.yml` — Chờ: B0 — Xong khi: mở bằng `python -m http.server -d web` thấy đủ 3 feature giả, đổi lens thì màu đổi; **deploy thử bằng file mock ở lần merge khóa hợp đồng hoặc lần merge kế tiếp** — Kiểm chứng: thử tay trên Chrome desktop và khung 375 px; console không lỗi; URL Pages mở được ở cửa sổ ẩn danh.
- [x] G1. **[A+B] 16:00 — cổng chốt lens** (đã quyết ~16:50 theo `docs/review_g1.md` mục 3; chi tiết thực thi ở Giai đoạn 2b) (15 phút): dựa trên A3, A4, B3 quyết định đường chính hay đường lùi cho từng lens; ghi vào Nhật ký. **Không thêm lens sau G1.** Quy tắc đã định sẵn: A3 hoặc A4 chưa xong lúc 16:00 thì **cắt L2 ngay**, không chờ CP1. Chưa có ảnh LROC/CTX thì bỏ ablation (a).

### Giai đoạn 2 — Xây dựng (16:00–22:00)
- [x] A5. **[A][agent]** `fidelity.py` theo chữ ký trên — File: `src/similitude/fidelity.py`, `tests/test_fidelity.py` — Xong khi: test pass — Kiểm chứng: `pytest tests/test_fidelity.py`, gồm: E = t → σ ≈ 0; σ tăng đơn điệu khi dịch xa dần; n < 5·K → tự chuyển `diag`; Σ suy biến không làm crash (PCA hoặc diag); **một cột quần thể là hằng số → `mahalanobis_d` hữu hạn và, trong ca chỉ lệch đúng cột đó, bằng độ lệch chia cho `min_scale`**; với K = 1 thì `sigma_dissimilarity` = `mahalanobis_d`; chế độ `full` với một cột hằng số không ra NaN; **d = 50, K = 14 → σ hữu hạn (không NaN/inf) và thứ hạng theo d được giữ nguyên trên một dãy d tăng dần 1…200**; `limiting_factor` trả đúng descriptor bị dịch trong ca thử; `no_analog` = True khi σ nhỏ nhất > 2.
- [x] A6. **[A]** Tầng mịn terrain: chip DEM Copernicus 30 m **trùng đúng ô 10 km của A2, footprint 4 km ở tâm ô, phần còn lại là vùng đệm** (chiếu về UTM cục bộ trước khi tính; GLO-30 là DSM, nên mặt nạ đất trơ giúp hạn chế sai lệch do cây và nhà) cho các nhóm:
  - `rank`: top 300 ô theo σ thô của A2.
  - `null`: **≥ 200 ô đất trơ chọn ngẫu nhiên phân tầng theo đới vĩ độ**, không phụ thuộc xếp hạng.
  - `control` / `decoy`: mọi đối chứng và mồi nhử L1/L2.
  - `seed`: các hạt giống.
  Tính descriptor bằng A1 — File: `scripts/gee/chip_dem.py` → `data/derived/earth_L1.parquet` — Chờ: A1, A2 — Xong khi: ≥ 90 % chip có `qa_flag` = ok — Kiểm chứng: đếm hàng; vẽ histogram `slope_p50` để soi giá trị bất thường; chip ven biển/vùng thiếu dữ liệu được đánh cờ, không bị âm thầm loại.
- [x] A7. **[A]** Descriptor L2 phía Trái Đất: `low_sun_hours` theo vĩ độ ô + tỷ lệ không tuyết trong các tháng Mặt Trời thấp (MODIS snow) + `shadow_fraction`; phía Moon: hằng số của mục tiêu đối chiếu bản đồ chiếu sáng PGDA — File: `scripts/gee/tier2_lowsun.py` → `data/derived/earth_L2.parquet`, `data/derived/targets_L2.parquet` — Chờ: A1, A6 — Xong khi: bảng đủ cột — Kiểm chứng: Devon Island và Peary Land xếp trên mọi ô vĩ độ < 60° theo `lowsun_frac_daylight`. **Kỳ vọng ghi trước:** để Mặt Trời đi trọn vòng chân trời ở độ cao 0–7° cần vĩ độ khoảng ≥ 83–86°, nơi gần như không có đất trơ, nên phần thiên văn của L2 rất có thể ra no-analog. Đó là kết quả hợp lệ ("Earth's best is X σ") và được báo cáo bằng số, không phải lỗi.
- [ ] B5. **[B]** Ứng viên M1 và trích phổ: tầng thô = đất trơ ∧ trong vùng phủ EMIT (±52°) ∧ chỉ số mafic ASTER GED + danh sách hạt giống (ophiolite, trường bazan, evaporite); tầng mịn = phổ trung vị EMIT cho ≤ 100 footprint gồm `rank`, `control`, `decoy` và **mẫu `null` ≥ 50 footprint đất trơ ngẫu nhiên, rút từ footprint granule EMIT thật (tra CMR), không rút trong cả dải ±52°** (EMIT ưu tiên vùng khô là nguồn bụi), ưu tiên rút gọn trên GEE; nếu phải dùng earthaccess (`open` lười + GLT) thì giới hạn ≤ 30 footprint ngoài mẫu null. **Sàn null: nếu mẫu null của một lens < 30 ô thì chỉ báo σ, không báo percentile.** Với null N ô, không được tuyên bố độ chính xác percentile mịn hơn 1/N (vd null 50 ô thì không viết "top 0,1%") — File: `scripts/emit/tier_m1.py` → `data/derived/earth_M1.parquet` — Chờ: B1, G1 — **Khởi chạy tải trước 18:00** — Xong khi: mọi đối chứng dương và mồi nhử M1 có phổ — Kiểm chứng: `qa_flag` ghi số pixel hợp lệ; footprint < 50 pixel hợp lệ bị đánh cờ.
- [ ] B6. **[B]** X1 rút gọn: phía Trái Đất tính MAAT, permafrost (Obu 2019 hoặc ESA CCI), P/PET, số chu kỳ đóng–tan từ MODIS LST ở 10 km; phía Mars mã hóa cấu hình từ SWIM cho Arcadia (băng < 1 m dưới lớp phủ khô); so sánh **cấu hình** (cờ + tỷ số); `evidence_status` tối đa là `engine-semiquant` — File: `src/similitude/descriptors/ice.py`, `scripts/gee/tier_x1.py` → `data/derived/earth_X1.parquet` — Chờ: G1 — Xong khi: có bảng xếp hạng X1 — Kiểm chứng: vùng Pamir/Changtang và các hoang mạc cực xếp trên vùng permafrost ẩm (vd đồng bằng Siberia). Nếu SWIM không tải được dạng raster, ghi Câu hỏi mở và dùng mô tả định tính từ ảnh PIA26046.
- [ ] B7. **[B]** Transfer Ledger: điền `ledger/moon.yaml`, `ledger/mars.yaml` theo bảng DESIGN 2.2(4); **mỗi con số kèm nguồn đã tra lại** (R10); số nào không tra được thì bỏ; liên kết gap kiến trúc NASA Moon to Mars đã xác nhận tên — Xong khi: không còn mục gắn [Nhớ] — Kiểm chứng: mỗi mục có trường `source` dạng URL hoặc DOI.
- [ ] B8. **[B][agent]** Attention Index: truy vấn OpenAlex theo DESIGN 2.2(6); tên dễ nhầm dùng thêm từ định danh (vd "Karakul" phải kèm "crater" hoặc "Tajikistan") — File: `scripts/attention/openalex.py` → `data/derived/attention.parquet` — Xong khi: có số cho mọi ứng viên và đối chứng — Kiểm chứng (R13): Atacama ≫ Harrat Khaybar; lưu nguyên văn chuỗi truy vấn và ngày tra.
- [ ] CP1. **[A+B] 22:00 — checkpoint** (10 phút): mọi bảng `earth_*` và `targets_*` có mặt; nếu một lens chưa đủ dữ liệu, cắt lens đó ngay (thứ tự cắt: X1 → L2). Mỗi người chạy `make test && make lint` + `claude-prereview` trên nhánh mình, mở PR, merge vào `main`; người còn lại `git merge main`. A8 cần dữ liệu của Linh nên phải merge xong trước khi bắt đầu.

### Giai đoạn 2b — Thực thi quyết định G1 (16:50–03:00), theo `docs/review_g1.md`
Ghi chú: tiến độ B0–B11 của Linh được theo dõi ở `progress.md` (Linh yêu cầu không sửa PLAN); trạng thái ô của các hạng mục B ở trên không phản ánh tiến độ thật.
Nguyên tắc chung cho cả giai đoạn: mọi quy tắc/ngưỡng mới phải được **commit trước** khi chạy toàn bộ dữ liệu (commit time là bằng chứng), và mọi thay đổi sau khi đã xem kết quả phải vào bảng "Deviations from pre-registration" của `docs/validation_report.md`.

- [x] G1a. **[A+B]** Gỡ nhãn analog nước sai: M1 chỉ tìm analog cho `analog_targets: [jezero_margin, nili_fossae_olivine]`; Oxia, Meridiani là `unobserved_targets` kèm lý do (`config/lenses.yaml`, `scripts/discovery/run_discovery.py`) — Kiểm chứng: Harrat Rahat/Khaybar/Pinacate không còn trong `web/data/candidates.geojson`; file qua `validate_candidates`; 122 test pass.
- [ ] A11. **[A]** Native rank: `score_lens` chấm thêm chính quần thể thiên thể đích, thêm cột `native_rank` (số footprint quần thể có d lớn hơn ô) và `n_native` (bỏ footprint trùng mục tiêu, d < 0,05) vào `fidelity.parquet` — File: `src/similitude/fidelity.py`, `tests/test_fidelity.py` — Xong khi: cột có mặt cho cả 4 lens — Kiểm chứng: test tổng hợp (ô trùng mục tiêu có native_rank = n_native; ô xa hơn mọi footprint có 0); L1: ba ô đứng đầu cho 53/53 như số thăm dò.
- [ ] A12. **[A]** Tập bền vững L1: một ô thuộc tập khi `native_rank ≥ n_native/2` dưới **cả ba** cấu hình (i) metric đường chéo 11 descriptor hiện tại, (ii) metric đầy đủ trên `[slope_p50, slope_p90, frac_gt20, rms_s1, rms_s16, hurst]`, (iii) baseline L = 90 m tính lại từ chip đã cache (cả Moon lẫn Trái Đất) — File: `scripts/l1_robust.py` → `data/derived/l1_robust_set.parquet` — Quy tắc commit trước khi chạy — Xong khi: có bảng + số ô mỗi cấu hình — Kiểm chứng: in giao/hợp của ba tập; nếu tập giao rỗng thì ghi đúng như vậy và dùng tập (i) kèm ghi chú độ nhạy (dự phòng mục 4.2 của review).
- [ ] A13. **[A]** Hồ sơ ô L1/L2 trong tập bền vững: tên (reverse-geocode như Linh, có cache), Attention (OpenAlex, cùng truy vấn B8), kiểm tra tuyết/băng (WorldCover lớp 70 trong footprint + ảnh Sentinel-2 trung vị mùa hè) → loại hoặc gắn cờ ô là mặt sông băng — File: `scripts/l1_profile.py` → cập nhật `earth_L1/L2.parquet` (cột `name`, `ice_frac`, `review_note`) — Xong khi: mọi ô trong tập bền vững có tên và `ice_frac` — Kiểm chứng: contact sheet `data/raw/review/l1_contact_sheet.png`, người duyệt chéo là Linh.
- [ ] A14. **[A]** Quy tắc đính chính tọa độ (áp chung, không chọn tay): nếu < 50 % footprint là đất hợp lệ (không nước WorldCover 80, có DEM) thì dời tâm tới tâm vùng đất hợp lệ liền khối gần nhất có ≥ 50 % — File: `src/similitude/io.py` hoặc `scripts/relocate.py` (hàm dùng chung, Linh áp cho Lake Salda) — Áp cho Karakul, Mistastin — Xong khi: báo **cả** kết quả gốc và kết quả sau đính chính trong báo cáo — Kiểm chứng: test với footprint giả lập nửa nước.
- [ ] A9b. **[A]** Báo cáo kiểm chứng bản 2: bảng phán quyết ba trạng thái (TRANSFERS / NO-ANALOG / UNOBSERVED) cho mỗi lens × biến; bảng bridge bias CRISM–EMIT (độ lệch hệ thống từng tham số, lấy từ số của Linh); bảng Deviations from pre-registration (tối thiểu 7 mục ở review 3.5); native rank thay "σ = 0" — File: `docs/validation_report.md` — Chờ: A11, A12, B13 (phần M1) — Xong khi: mọi con số dự định đưa lên slide 4–6 có dòng nguồn trong báo cáo.
- [ ] B13. **[B]** M1 so khớp theo pixel: tải pixel EMIT 60 m của footprint bằng `computePixels` (10–50 s/footprint), chạy `crism_params` của thư viện chung trên **từng pixel**, áp presence gate đã khai báo ở B14 → `data/derived/earth_M1_pixels.parquet` (`cell_id, target_id, n_valid_px, frac_matched, matched_area_km2, largest_patch_km2` + phân vị p50/p90/p99 của tham số chẩn đoán) — Thứ tự chạy: đối chứng + mồi nhử trước, rồi seed, rank, null — **Tiêu chí dừng 21:00:** Lake Salda (sau đính chính A14) và Semail có `matched_area_km2` > 0 với Jezero, Wadi Rum và Simpson ≈ 0. Đạt → M1 công bố theo matched area. Không đạt → M1 chỉ lên slide dạng "minh họa phương pháp trên 4 địa điểm + kết quả âm ở tỷ lệ footprint", không có hidden analog M1 — Kiểm chứng: in bảng 6 điểm đối chứng/mồi nhử; ghi kết quả vào `progress.md`.
- [ ] B14. **[B]** Khai báo trong `config/lenses.yaml` **trước** khi chạy B13 toàn bộ: họ tham số chẩn đoán cho từng mục tiêu lấy theo browse product Viviano-Beck 2014 (ghi nguồn); quy tắc ngưỡng chung "mỗi tham số chẩn đoán ≥ 50 % giá trị mục tiêu và ≥ sàn nhiễu = phân vị 95 của pixel null"; loại HCPINDEX, BD2250, MIN2250 khỏi fidelity (giữ trong bảng bridge bias); dùng bản MICA `ratioed` cho OLINDEX; trường `role` cho mỗi ứng viên (`aqueous` / `substrate-baseline` / `terrain`) — Xong khi: commit riêng trước commit chạy B13 — Kiểm chứng: `pytest tests/test_schema.py` vẫn pass; Harrat được gán `substrate-baseline`.
- [ ] B15. **[B]** X1 trình bày dạng danh sách điều kiện (permafrost; lớp phủ không tan tới mặt băng — số ngày đóng–tan bề mặt thấp là **điều kiện loại**; lớp phủ khô), sàn từng điều kiện lấy theo Beacon Valley + vật lý mục tiêu, ghi rõ "đặt sau khi xem dữ liệu"; chú thích ERA5-Land là tái phân tích lưới ~9 km, MODIS là LST trời quang — Xong khi: Test Card X1 hiển thị 3 điều kiện đạt/không đạt — Kiểm chứng: Beacon Valley đạt cả 3; ghi giả thuyết Pamir–Changtang "bị dữ liệu bác" trong báo cáo.
- [ ] B16. **[B]** Test Card ba trạng thái: mỗi lens score có `verdict ∈ {TRANSFERS, NO-ANALOG, UNOBSERVED}` + lý do (cập nhật `schemas/candidate.schema.json`); L2 tách hai dòng (hình học Mặt Trời: NO-ANALOG, tốt nhất 28 % so với 100 %; bóng đổ: σ_shadow); hiển thị native rank (L1/L2) và matched area (M1) — File: `schemas/`, `src/similitude/discovery.py`, `web/app.js` — Chờ: A11, B13 — Xong khi: Test Card mẫu trong review 3.4 hiển thị đúng trên web cục bộ — Kiểm chứng: `validate_candidates` pass; chụp màn hình desktop + 375 px.

**Không làm (review 4.1):** ablation ảnh LROC, descriptor trũng kín (đã thử, Mặt Trăng ≈ 0 ở 30 m), tỷ số hóa theo trung vị cảnh, thêm lens, mở rộng X1.
**Dự phòng (review 4.2):** Data Freeze 03:00 — tối thiểu phải có L1 tập bền vững + native rank, L2 con số no-analog, M1 4 địa điểm ở mức pixel, X1 Beacon Valley + phát biểu khan hiếm. Code Freeze 15:00 — nếu B16 chưa xong thì dùng bảng tĩnh trên slide 6, nhưng web bắt buộc đã gỡ nhãn Harrat (G1a, xong) và sửa hiển thị L2.

### Giai đoạn 3 — Tích hợp và Data Freeze (22:00–03:00)
- [x] A8. **[A]** Chấm điểm và validation: `score_lens` cho từng lens; `validation.py`: percentile đối chứng dương **tính trên mẫu `sample_role=null`** (không tính trên tập đã lọc), so với kỳ vọng ghi trước trong `controls.yaml`; điểm mồi nhử; ablation (a) RGB/texture (dựng lại kiểu NHSJS 2026 trên Sentinel-2 phía Trái Đất, LROC/CTX phía mục tiêu, **cả hai gộp về cùng độ phân giải 10 m trước khi tính**, kỳ vọng nhánh RGB ghi trước trong `controls.yaml` ở trường `expected_rgb`; bỏ nếu A3/B2 không có ảnh) với (c) twin-formula, **trình bày dạng nghiên cứu tình huống theo từng lens, không tuyên bố thống kê** vì mỗi lens chỉ có 2–3 cặp; độ nhạy (đổi L, bỏ từng descriptor, lắc ngưỡng mặt nạ) — File: `src/similitude/validation.py`, `tests/test_validation.py`, `scripts/run_all.py` → `data/derived/fidelity.parquet`, `data/derived/validation.parquet` — Chờ: A5, A6, A7, B5, B6 — Xong khi: `python scripts/run_all.py` chạy từ đầu đến cuối không lỗi — Kiểm chứng: `pytest tests/test_validation.py` (dữ liệu tổng hợp có ô cài sẵn phải đứng top); ghi **nguyên trạng** kết quả vào Nhật ký, kể cả khi kỳ vọng trong DESIGN không xảy ra.
- [ ] B9. **[B]** Discovery và xuất GeoJSON: lọc fidelity percentile cao (lens không có percentile thì dùng ngưỡng σ ≤ 1) ∧ attention thấp ∧ `in_exclusion_buffer = False` (bước duy nhất dùng cờ này để lọc); gộp ô kề nhau (non-max suppression theo khoảng cách ≥ footprint); gán `evidence_status`; điền `process_title`, `test_here`, `cannot_test` (từ ledger) — File: `src/similitude/discovery.py`, `tests/test_discovery.py` → `web/data/candidates.geojson` — Chờ: A8, B7, B8 — Xong khi: file qua `validate_candidates`; mỗi lens MVP có ≥ 1 ứng viên `engine-confirmed` (X1: `engine-semiquant`) hoặc lens đó được ghi là "no hidden analog found" — Kiểm chứng: `pytest tests/test_discovery.py` (hai ô cách nhau < footprint chỉ còn một).
- [ ] B10. **[B]** Đọc lại từng ứng viên top bằng ảnh Sentinel-2 / NASA Worldview để loại lỗi dữ liệu (mây sót, ruộng, mỏ lộ thiên); tiêu đề Test Card theo quá trình — Xong khi: ứng viên nghi vấn hạ xuống `hypothesis` kèm ghi chú — Kiểm chứng: hai người cùng duyệt danh sách cuối.
- [ ] DF. **[A+B] 03:00 — Data Freeze:** đóng băng `data/derived/` và `web/data/candidates.geojson`; chỉ ứng viên `engine-confirmed` hoặc `engine-semiquant` (ghi nhãn rõ) được lên slide. Mỗi người chạy `claude-prereview` rồi `claude-gate-diff` trên nhánh mình, merge vào `main` khi SHIP. **Nếu cổng 2 trả FIX:** không merge; ghi lỗi vào Câu hỏi mở; sửa và chạy lại cổng lúc 07:30. B11 vẫn tiếp tục trên nhánh của Linh. Trước khi ngủ, giao B11 cho agent chạy trên nhánh của Linh với dữ liệu thật.

### Giai đoạn 4 — Sản phẩm (07:30–15:00)
- [ ] A9. **[A]** `docs/validation_report.md` + hình trong `docs/figures/`: biểu đồ percentile đối chứng dương, so sánh mồi nhử (RGB vs twin-formula), recall@k của ablation, bản đồ σ cho mỗi lens — Chờ: A8 — Xong khi: mỗi khẳng định trong slide 3–5 đều trỏ được tới một hình hoặc bảng trong báo cáo — Kiểm chứng: B đọc chéo.
- [ ] A10. **[A]** README: mục đích, cách tái lập (`pip install -e .`, `python scripts/run_all.py`), danh sách đầy đủ dữ liệu NASA và đối tác kèm DOI, giới hạn đã biết (dải phổ bị che, EMIT ±52°, analog dưới pixel), khai báo SI, giấy phép — Xong khi: người ngoài clone về làm theo được — Kiểm chứng: clone vào thư mục tạm, chạy lại `make test`.
- [ ] B11. **[B][agent]** Web hoàn thiện trên `candidates.geojson` thật: hình hồ sơ lens (radar chart) trong Test Card, bảng Transfer Ledger, liên kết báo cáo validation, phần "Data & limits"; tùy chọn Near-me và nền Moon/Mars Trek nếu R12 ổn — Chờ: B9 — Xong khi: chạy đúng ở máy cục bộ (`python -m http.server -d web`) với dữ liệu thật — Kiểm chứng: thử trên máy tính và khung 375 px; không lỗi console. Bản trên Pages được kiểm ở CF và 5.2.
- [ ] B12. **[B]** Slide nháp 7 trang theo DESIGN 2.6 (hoặc kịch bản video 30 s nếu 0.1 chọn video), tiếng Anh, mọi con số lấy từ `validation_report.md` — Chờ: A9 (có thể dựng bố cục trước) — Xong khi: đủ 7 slide — Kiểm chứng: A đối chiếu từng con số với báo cáo.
- [ ] CF. **[A+B] 15:00 — Code Freeze:** `make test && make lint` sạch; `claude-prereview` → `claude-gate-diff` trên từng nhánh; merge PR vào `main` sau khi SHIP. `main` là bản nộp: repo công khai trỏ vào `main`, GitHub Pages build từ `main`.

### Giai đoạn 5 — Nộp bài (15:00–21:00)
- [ ] 5.1. **[A+B]** Hoàn thiện slide; điền trang Project bằng tiếng Anh (tóm tắt, dữ liệu NASA/đối tác, khai báo SI theo kết luận ở 0.1, tính nguyên bản) — Kiểm chứng: đọc chéo.
- [ ] 5.2. **[A+B]** Kiểm tra mọi link (slide, repo, web) ở cửa sổ ẩn danh; rà quy định ảnh/giọng người dưới 18 tuổi; kiểm tra tab Members — Kiểm chứng: checklist trong `docs/compliance.md` đánh dấu đủ.
- [ ] 5.3. **[A+B]** Nộp trước 21:00, chụp màn hình xác nhận — Kiểm chứng: trang Project hiển thị trạng thái đã nộp.

## Edge-cases
- **Hệ chiếu cực:** DEM Mặt Trăng ở polar stereographic; tính dốc trên lưới chiếu với kích thước pixel đúng, không dùng độ góc kinh/vĩ. Chip Trái Đất ở vĩ độ cao (Devon, Peary Land) phải chiếu về UTM hoặc polar stereographic cục bộ trước khi tính.
- **Chênh độ phân giải:** mọi so sánh dùng chung L; quên gộp về L là lỗi nghiêm trọng nhất của pipeline terrain. `terrain_descriptors` phải bắt buộc truyền `L_m`.
- **Lake Salda sát mặt nước:** mặt nạ nước/ẩm cho footprint đối chứng này phải chặt (vd NDWI, khoảng cách tới mép nước), nếu không phổ trung vị bị kéo về phía nước.
- **Vùng phủ EMIT:** đối chứng dương ngoài ±52° (Devon Island) không được dùng cho M1. Mồi nhử và đối chứng M1 phải nằm trong vùng phủ.
- **Pixel phổ hỏng:** mây, bóng mây, nước, thực vật dư (NDVI > ngưỡng), cát ẩm, mỏ lộ thiên. Phổ MICA có dải tới 3,9 µm: cắt ở 2,49 µm trước khi tính, không ngoại suy.
- **Thang phản xạ:** phổ MICA tỷ số (ratioed I/F) **không cùng loại** với phản xạ bề mặt EMIT; ưu tiên phổ tử số (numerator). Trong mọi trường hợp chỉ so **band depth và hình dạng** (tham số SWIR, SAM sau khử continuum), không so giá trị tuyệt đối, không dùng tham số VNIR nếu phổ mục tiêu không có VNIR.
- **Bóng bị cắt ở mép chip:** ở độ cao 2°, bóng dài khoảng 28 lần độ chênh cao. Mọi chip (Trái Đất và Mặt Trăng) dùng **cùng** quy tắc: footprint 4 km + đệm 3 km, chỉ thống kê trên footprint. Vật cản ở xa hơn 3 km bị bỏ qua ở cả hai phía; ghi vào báo cáo.
- **Lưới kinh/vĩ ở vĩ độ cao:** bước kinh độ của GLO-30 thay đổi khi lên trên 50°, nên phải chiếu lại trước khi tính dốc cục bộ.
- **Σ kém điều kiện:** quần thể ít mẫu, descriptor tương quan mạnh (vd `rms_s1` và `slope_p50`). `fit_population` phải tự lùi về `diag`, và ghi `mode` ra kết quả.
- **Quần thể M1:** chỉ ~30 phổ MICA, trải nhiều lớp khoáng; Σ khi đó đo "biến thiên giữa các lớp khoáng trên Sao Hỏa". Ghi rõ điều này trong báo cáo.
- **Ô trùng lặp:** nhiều ô kề nhau cùng điểm cao → non-max suppression trước khi đặt tên ứng viên.
- **Analog dưới pixel** (Kamil, hang băng): không đưa vào chấm; nếu nêu trong slide thì `evidence_status` = `literature-only`.
- **Trùng tên trong OpenAlex:** "Karakul" (giống cừu), "Lut", "Kamil". Dùng tên kèm định danh địa lý; lưu nguyên văn truy vấn.
- **Vùng nhạy cảm:** chỉ số tiếp cận và ghi chú an ninh chỉ là thông tin, không dùng để xếp hạng nếu chưa làm phần tùy chọn.
- **Hạn ngạch GEE:** export lớn có thể bị xếp hàng lâu; chia lô theo vùng, dùng `computePixels` cho chip nhỏ.

## Câu hỏi mở
- **[Cho Linh — đã sửa file của Linh, cần Linh xem lại] `src/similitude/discovery.py: passes_fidelity`:** trước đây chỉ xét percentile ≥ 90, nên khi mọi ô đều xa mục tiêu (no-analog) ô gần nhất vẫn đạt percentile 100 và bị gắn `engine-confirmed` (L2 σ≈14, M1 σ≈3). Đã thêm điều kiện σ ≤ 2 (ngưỡng no-analog của DESIGN 2.2(3)); L2 xét `sigma_shadow`. Test discovery vẫn pass. **Web card L2** đang hiện σ tổng ≈ 14 cạnh nhãn engine-confirmed — cần hiển thị cả σ_shadow và dòng "sun geometry: no Earth analog".
- **[Cho Linh] M1 chưa kiểm chứng được:** Lake Salda (`high`) chỉ ở percentile 11,6 so với Jezero; decoy Simpson Desert ở 73,9. Nghi vấn: phổ MICA ratioed vs numerator, nước/ẩm trong footprint Lake Salda, quần thể 29 phổ trải nhiều lớp khoáng, nhiễu kênh EMIT 2,25–2,5 µm. Chi tiết: `docs/validation_report.md` §4.
- **Tọa độ hạt giống/đối chứng rơi vào hồ:** Karakul (seed) và Mistastin (extra) có dốc 0° vì tâm chip nằm trên mặt hồ → kết quả của hai điểm này là lỗi dữ liệu, cần dời sang đất lộ trước khi dùng.
- **[Cho Linh, B3(i) đã có lời giải]** EMIT L2A trên GEE có ID **`NASA/EMIT/L2A/RFL`** (không phải `L2A_RFL` như ABOUT.md), ~249 nghìn cảnh, 08/2022–08/2026, 579 band — kiểm bằng tài khoản GEE của Bảo lúc 13:00. EMIT L2B mineral không có trên GEE. Không cần Earthdata cho đường chính của B3/B5.
- **Earthdata:** máy chủ đăng nhập `urs.earthdata.nasa.gov` không tới được từ mạng của Bảo (timeout IPv4); các máy chủ dữ liệu NASA khác vẫn tới được. Chỉ cần khi M1 phải lùi về EMIT L2B.
- **Máy Bảo không có `make`.** Dùng `.venv/bin/python -m pytest -q` và `.venv/bin/python -m ruff check .`, hoặc `sudo apt install make`.
- **Quota proxy (cập nhật 15:25):** Claude 4.6 (Opus và Sonnet) trên proxy Antigravity đã **cạn ở cả hai tài khoản, reset sau ~6–7 ngày** — coi như không còn trong hackathon. Việc `[agent]` còn lại chuyển sang **Antigravity IDE (Gemini 4 / Gemini 3.8 Flash)**; việc cần chính xác thì Opus 5.5 làm trực tiếp (quota gốc, dùng tiết kiệm). Cổng `claude-gate-diff` (Opus 5.5 gốc) vẫn dùng được; `claude-prereview` (Opus 4.6) KHÔNG còn dùng được → thay bằng tự chạy test/lint + đọc diff.
- **[Cho Linh] Bẫy CSV:** pandas đọc chuỗi `"null"` (giá trị `sample_role`) thành NaN. Đọc mọi CSV có cột `sample_role` bằng `keep_default_na=False`, hoặc dùng parquet.
- **Đề xuất cho G1, phần Bảo (Opus 5.5, 15:10; chờ Bảo + Linh chốt):**
  1. **Giữ L1.** R5 đạt mục đích gốc (descriptor tách được địa điểm, d 4–16). Báo Haughton như một kết quả âm có giải thích ("analog địa chất/EVA, không phải analog phân bố dốc của sống núi cực") — đây là bằng chứng engine không bị "tên tuổi" dẫn dắt. Giữ nguyên `expected: high` đã ghi trước cho Haughton trong báo cáo, không sửa hồi tố.
  2. **Mục tiêu L1 chính = Connecting Ridge.** Chip `shackleton_rim` (dốc trung vị 31°) giữ trong bảng nhưng đổi nhãn thành "Shackleton inner wall (Site04 centre)" và không dùng làm mục tiêu; không dời chip sau khi đã xem kết quả.
  3. **Giữ L2** nhưng trình bày tách: `sigma_shadow` (địa hình) là kết quả khám phá; phần thiên văn báo là no-analog có số (đúng kỳ vọng ghi trước ở A7).
  4. **Bỏ ablation (a) phía Moon** (chưa lấy được chip LROC); giữ ablation (a) cho M1 nếu Linh có chip CTX. Mồi nhử Wadi Rum vẫn chạy trên nhánh phổ.
- **G1 cần quyết:** (1) R5 trượt theo tiêu chí nhưng đạt mục đích tách biệt — giữ L1 và báo Haughton như một kết quả âm có giải thích, hay đổi cách đo? Không được đổi đối chứng/kỳ vọng hồi tố. (2) Mục tiêu L1 chính là Connecting Ridge; chip Shackleton nên dời sang gờ vành thật hay bỏ.
- Kết quả G0 về quy định SI (0.1): cần đội xác nhận trước khi triển khai.
- Nộp slide hay video 30 s? Điểm thi TP. HCM có thuyết trình trực tiếp không?
- Bảo đã đăng ký Earthdata và GEE lúc ~12:05 (chưa xác thực trên máy, chưa có tên project). Linh: chưa rõ. Nếu GEE chưa được duyệt trước 13:45, dùng đường lùi ghi ở 0.2.
- Kế hoạch giả định Bảo mạnh xử lý raster/Python, Linh mạnh dữ liệu phổ và trình bày. Nếu không đúng, đổi nguyên lát dọc giữa hai người, không đổi từng hạng mục.

## Nhật ký
- 2026-11-14 · Opus 5.5 · soạn PLAN.md từ DESIGN.md cho đội 2 người; cập nhật phân vai Bảo/Linh, tài khoản, quy tắc nhánh · test: chưa có code
- 2026-11-14 12:28 · `claude-gate-plan` (Opus 5.5, one-shot) · cổng 1 lần 4 = **APPROVE**, không blocker. Đã xử lý rủi ro hợp đồng mà cổng nêu: thêm cột `d`, `sigma_capped`, `metric_mode`, `percentile` nullable, ngưỡng σ ≤ 1 khi thiếu percentile, `d_shadow`/`sigma_shadow` cho L2; null M1 rút từ granule EMIT thật; đường lùi không GEE cho null và Sentinel-2; mặt nạ nước Lake Salda · test: chưa có code
- 2026-11-14 12:22 · Opus 5.5 · cổng 1 lần 3 = REVISE (1 blocker: σ tràn số khi d lớn); đã sửa theo đề xuất của cổng (sf/isf, xếp hạng bằng d thô, test d=50 K=14) + rủi ro: SAM từ 2100 nm, trung bình 3 kênh quanh mốc, lưới footprint A3, đo tốc độ EMIT trước, tên notebook; chờ cổng 1 lần 4 · test: chưa có code
- 2026-11-14 12:18 · Opus 5.5 · cổng 1 lần 2 = REVISE (2 blocker); đã sửa: tách `mahalanobis_d` và quy ước χ_K → χ_1, Σ = D·R·D; workflow Pages cho `web/`, B11 xong khi chạy cục bộ; footprint thô 10 km hai phía; sàn null 30 ô; ablation cùng độ phân giải; quy tắc khi cổng 2 FIX lúc 03:00; chủ sở hữu seeds/tests/notebooks; dời khóa hợp đồng sang 13:45 · test: chưa có code
- 2026-11-14 12:12 · Opus 5.5 · cổng 1 lần 1 = REVISE (7 blocker); đã sửa: lưới phổ 2490 nm + PARAM_TABLE, MICA numerator, mẫu null phân tầng, cờ vùng đệm thay vì xóa, min_scale chống Σ suy biến + kỳ vọng L2 no-analog, chip ảnh LROC/CTX cho ablation, trạng thái engine-semiquant cho X1; thêm footprint 4 km + đệm 3 km, kỳ vọng đối chứng ghi trước, quy tắc cắt L2 tại G1 · test: chưa có code

### Nhật ký — Bảo (A)
- 2026-11-14 16:50 · Opus 5.5 (planner) · Đưa quyết định G1 (`docs/review_g1.md`, Fable 5.2) vào PLAN: thêm Giai đoạn 2b (G1a, A11–A14, A9b, B13–B16). G1a xong: M1 chỉ tìm analog cho Jezero, Nili Fossae; Oxia, Meridiani = UNOBSERVED; Harrat Rahat/Khaybar/Pinacate ra khỏi candidates.geojson (đổi sau khi xem kết quả → mục Deviations) · test: 122 passed
- 2026-11-14 16:50 · Opus 5.5 · **A7, A8 xong; A9 bản nháp; đã hợp nhất nhánh Linh.** A7: `scripts/build_L2.py` (astro cùng công thức, obliquity 1,54° Moon / 23,44° Earth; bóng đổ dùng lại chip L1; snow_free_frac MODIS 2023 làm cột ngữ cảnh). Hợp nhất `origin/linh/spectral-story` (không xung đột). Đối chứng L1/L2 đối chiếu lại theo `controls.yaml` (hợp đồng 13:45) bằng `scripts/reconcile_controls.py`: thêm chip Meteor Crater (L1) và Sahara (L2, decoy); Mistastin, Wadi Rum (danh sách tạm) chuyển vai trò `extra`, không đánh giá. `fidelity.score_lens` đọc min_scale qua `io.min_scale_for` (hết default 1e-6 âm thầm). A8: `scripts/run_all.py` + `src/similitude/validation.py` chấm cả 4 lens bằng engine chung → `fidelity.parquet` (discovery của Linh tự dùng file này thay bộ chấm tạm). Kết quả: **L1** rank trung vị d 3,98 so với null 10,33; ô tốt nhất σ = 0 (Ellesmere bắc, NE Greenland, Changtang, Altiplano…); Haughton (high) trượt (pct 81,5). **L2** thiên văn no-analog đúng kỳ vọng (σ tốt nhất 13,9); riêng bóng đổ σ_shadow 0,49. **M1** Lake Salda (high) trượt (pct 11,6), Simpson decoy trượt, Wadi Rum decoy đạt; sau khi siết σ ≤ 2: Harrat Rahat σ 0,24, Harrat Khaybar σ 0,63 là ứng viên engine-confirmed. **X1** Beacon Valley đạt (pct 98,1), Axel Heiberg trượt. Độ nhạy L1: top-10 không ổn định (Jaccard trung vị 0,18) vì hàng chục ô cùng ở d ≈ 1 → báo tập ô σ≈0, không báo thứ hạng cố định. A9: `docs/validation_report.md` + 4 hình `docs/figures/validation_controls_*.png` (bản nháp; còn thiếu ablation (a), độ nhạy theo L). · test: 122 passed, ruff sạch
- 2026-11-14 16:00 · Opus 5.5 · **A6 xong:** `earth_L1.parquet` 512 hàng (300 rank, 200 null, 5 control, 1 decoy, 6 seed), **qa_flag ok 100 %**, chạy 29 phút, nguồn AWS GLO-30. Trung vị dốc: rank 12,8° (mục tiêu Connecting Ridge 12,4°) so với null 1,0° → tầng thô xếp hạng đúng hướng. **Ghi TRƯỚC khi chấm điểm:** (1) CTRL_Mistastin có dốc ≈ 0 vì tọa độ (55,88; −63,31) rơi vào mặt hồ trong hố → lỗi tọa độ, không phải kết quả; cần dời sang vành anorthosite lộ đá và ghi lý do trước A8. (2) DECOY_Wadi_Rum dốc trung vị 20° (khối sa thạch dựng đứng): mồi nhử này thiết kế cho lens khoáng vật M1; ở lens địa hình L1 nhiều khả năng trượt kỳ vọng `low` — sẽ báo nguyên trạng. (3) 3/5 ô rank đứng đầu nằm ở Altiplano–Atacama (đa số mang cờ vùng loại trừ) · test: 70 passed
- 2026-11-14 15:45 · claude-agy (Sonnet 4.6) viết, Opus 5.5 sửa/kiểm · **A5 xong:** `fidelity.py` (fit_population D·R·D + min_scale, mahalanobis_d, σ qua chi_K.sf → chi_1.isf, xếp hạng bằng d, percentile trên mẫu null với sàn 30, no_analog, d_shadow/sigma_shadow cho L2). Agent hết quota giữa chừng; Opus 5.5 sửa lỗi σ = NaN khi d lớn (scipy `logsf` → −inf từ d ≈ 40): thêm khai triển tiệm cận log Q(s,x), sai lệch < 0,05 % so với scipy ở d = 10–30; sửa E712 (so sánh Series với True/False) · test: 70 passed, ruff sạch
- 2026-11-14 15:45 · claude-agy viết, Opus 5.5 sửa · **A6 đang chạy:** `select_tier2.py` → 512 điểm (300 rank sau NMS 30 km, 200 null phân tầng theo đới vĩ 20°, 5 control, 1 decoy, 6 seed; 70 hàng mang cờ vùng loại trừ). Lỗi đã sửa: pandas đọc chuỗi `"null"` thành NaN → mọi chỗ đọc `tier2_L1_selection.csv` phải dùng `keep_default_na=False`. `build_earth_L1.py` khởi chạy 15:40 (~10 chip/phút, dự kiến xong ~16:30). controls.yaml của Linh chưa có → đang dùng danh sách đối chứng tạm theo PLAN (ghi trong cột `source`)
- 2026-11-14 14:30 · Opus 5.5 · **A2 xong:** 9 vùng export xong (w_asia lỗi lần đầu do ô thiếu DEM → lọc null trước `map`, chạy lại). **196.008 ô đất trơ 10 km** (Africa 122.696, W Asia 75.409, E Asia 29.948, Oceania 10.565, S America 7.299, N America 6.357, N Asia 3.555, Europe 1.732, Arctic 940). Gắn cờ vùng loại trừ 2.777 ô (Atacama 2.588, Iceland 156, Pilot Valley 23, Hawaii 10); không xóa ô nào. Haughton, Peary Land, Harrat Khaybar, Karakul đều có ô trong bảng. Không phủ Nam Cực (vốn thuộc vùng loại trừ). File commit: `data/derived/tier1_terrain.parquet` (5,4 MB, zstd); CSV 44 MB để trong `.gitignore`. Dốc tầng thô tính trên GEE nên chỉ dùng để xếp hạng sơ bộ (xem dòng đối chiếu chéo 13:03) · test: 39 passed
- 2026-11-14 13:13 · Opus 5.5 · Chip ảnh LROC (tùy chọn của A3): hết ngân sách 20 phút, **chưa lấy được**. Đã xác định lớp phù hợp trên Moon Trek: `LRO_NAC_Mosaic_1mpp_SP` (NAC 1 m/px, phủ ±136 km quanh cực nam, gồm các site PGDA), WMTS REST `https://trek.nasa.gov/tiles/Moon/SP/LRO_NAC_Mosaic_1mpp_SP/1.0.0/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png`, Style `default`, TileMatrixSet `default028mm`. Vướng mắc: lưới tile khai báo theo đơn vị giả kinh/vĩ (TopLeft −180, 90), chưa rõ cách ánh xạ từ tọa độ phép chiếu cực nam (m). Nếu G1 giữ ablation (a) phía Moon thì làm tiếp từ đây; nếu không thì bỏ.
- 2026-11-14 13:03 · Opus 5.5 (tự viết vì quota agent hết) · **A2 đang chạy:** `scripts/gee/tier1_terrain.py` — lưới 10 km EASE-Grid **EPSG:3410** (GEE không đọc được EPSG:6933), giai đoạn 1 lọc đất trơ ở 1 km (WorldCover 60+100 ≥ 0,5; 40+50+80 < 0,1; NDVI max 2023 < 0,25), giai đoạn 2 `reduceRegions` 90 m trên DEM GLO-30 đã gộp về 90 m. Thử vùng Devon: 149 ô, ô Haughton nằm trong mặt nạ (inert 1,0; NDVI 0,20), dốc trung vị 3,87°. Đối chiếu chéo cùng ô bằng thư viện chung (chip AWS, gộp 90 m): 3,29° / frac_gt8 0,155 so với GEE 3,87° / 0,187 — lệch ~15–20 % do ô lưới và kernel khác; chấp nhận cho tầng lọc thô, không dùng cho số công bố. 9 tác vụ `Export.table.toAsset` đã khởi chạy 13:02 (`--mode status` / `--mode collect`). `flag_exclusion.py` + `config/exclusion_zones.yaml` xong (chỉ gắn cờ) · test: 39 passed
- 2026-11-14 13:05 · claude-agy viết + Opus 5.5 chạy/kiểm · **A4 xong, R5 TRƯỢT theo tiêu chí PLAN** (d đường chéo tạm, min_scale như A4; so với Connecting Ridge): SP Crater/Black Point (expected uncertain) 4,32 · Sahara ngẫu nhiên 7,40 · Úc ngẫu nhiên 7,63 · Haughton/Devon (expected high) 10,56 · Gobi ngẫu nhiên 15,52. Không chỉnh gì sau khi xem kết quả. Diễn giải đưa ra G1: descriptor **tách được** địa điểm (d trải 4–16, mục đích gốc của R5 trong DESIGN đạt); thứ trượt là kỳ vọng của đối chứng — Haughton là analog địa chất/vận hành EVA nhưng địa hình rất phẳng (dốc trung vị 3° so với 12° của Connecting Ridge). n = 5, σ tạm, chưa phải kết luận thống kê. Kết quả: `data/derived/spike_r5.csv` · test: 38 passed
- 2026-11-14 13:00 · claude-agy viết + Opus 5.5 chạy/kiểm · **A3 xong:** 2 mục tiêu + 54 footprint quần thể (Site11 dùng bước 3 km) → `targets_L1.parquet`, `targets_L1_coarse.parquet`, chạy 69 s. **R4 đạt:** chênh trung vị dốc 5 m so với `*_slp.tif` ≤ 0,001° ở cả 6 site. Lưu ý: chip "shackleton_rim" ở tâm raster Site04 có dốc trung vị 31° (nhiều khả năng là sườn trong hố, không phải gờ vành) → đề xuất dùng Connecting Ridge làm mục tiêu L1 chính. Chip ảnh LROC chưa lấy (quota agent hết) → nếu chưa có trước G1 thì bỏ ablation (a) phía Moon · test: pass
- 2026-11-14 12:50 · Opus 5.5 · A1 xong (agent viết, Opus 5.5 sửa 2 lỗi: footprint chip không vuông, raise khi vùng trong rỗng thay vì âm thầm dùng cả chip; thêm 2 test hồi quy) · test: 19 passed, ruff sạch
- 2026-11-14 · Sonnet 4.6 (Antigravity) · A1 xong: terrain.py (aggregate_to_baseline, slope_stats, roughness_spectrum, shadow_fraction, terrain_descriptors), astro.py (low_sun_hours), conftest.py (make_fbm), test_terrain.py (11 test), test_astro.py (5 test) · pytest: 16 passed, ruff: sạch
- 2026-11-14 12:40 · claude-agy (Sonnet 4.6) + Opus 5.5 kiểm · A0 code xong trên `bao/terrain-engine`: `.venv/bin/python -m pytest` 1 passed, `ruff check` sạch, import rasterio/pyproj/earthaccess/ee OK. **Máy chưa cài `make`** (agent báo nhầm là `make` chạy được); tạm dùng lệnh trực tiếp. Chưa `[x]` vì chưa merge vào `main` · test: pass
- 2026-11-14 12:10 · Opus 5.5 · tải PGDA 78 (DEM 5 m + dốc) cho Site01, 04, 06, 07, 11, 23 vào `data/raw/moon/pgda78/` (~580 MB, không commit)
- 2026-11-14 · Sonnet 4.6 · A0 xong: pyproject.toml, Makefile, LICENSE, .gitignore, README.md, src/similitude/__init__.py, src/similitude/descriptors/__init__.py, tests/test_smoke.py, placeholder .gitkeep · pytest: 1 passed · ruff: All checks passed

### Nhật ký — Linh (B)
