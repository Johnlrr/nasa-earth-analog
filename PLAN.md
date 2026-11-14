# PLAN: SIMILITUDE — MVP 48 giờ cho đội 2 người

Nguồn: `DESIGN.md` (14/11/2026)  ·  Cổng 1: chưa chạy
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
2. **Khóa hợp đồng trước 13:30** (schema bảng, `lenses.yaml`, GeoJSON mẫu). Sau đó mỗi bên làm việc với dữ liệu giả của bên kia, không chờ nhau.
3. **Mỗi người chạy song song một agent** (Antigravity hoặc `claude-agy`) cho các hạng mục gắn nhãn `[agent]`: code thuần có test rõ ràng. Người giữ phần cần phán đoán khoa học và thao tác tài khoản (GEE, Earthdata).
4. **Việc chạy lâu (export GEE, tải EMIT) khởi động sớm nhất có thể** và chạy nền trong lúc làm việc khác hoặc ngủ.

### Quy tắc Git và nhánh
1. **Mỗi người code trên nhánh riêng, tạo ngay khi bắt đầu triển khai** (sau khi pull `main` có `PLAN.md` này):
   - Bảo: `git switch -c bao/terrain-engine`
   - Linh: `git switch -c linh/spectral-story`
   Agent của ai thì chạy trên nhánh của người đó.
2. **Trên nhánh cá nhân được commit tự do** và nên `git push -u origin <nhánh>` thường xuyên để có bản sao lưu. Commit không ghi danh AI (AGENTS.md quy tắc 6).
3. **`main` chỉ nhận merge qua Pull Request tại các mốc:** 13:30 (khóa hợp đồng), 22:00 (CP1), 03:00 (DF), 15:00 (CF). Trước mỗi lần merge: `make test && make lint` sạch và chạy `claude-prereview`; tại DF và CF chạy thêm `claude-gate-diff` (cổng 2) và chỉ merge khi SHIP.
4. **Sau mỗi lần merge vào `main`, người còn lại chạy `git merge main`** vào nhánh của mình ngay.
5. **Thứ tự của mốc khóa hợp đồng:** Bảo làm A0 trên nhánh mình, mở PR và merge vào `main` khoảng 13:00. Linh soạn các file cấu hình/schema của B0 trên nhánh mình ngay từ đầu, `git merge main` sau khi A0 vào `main`, viết `io.py` + test, rồi mở PR merge trước 13:30.
6. **Sở hữu file** (chỉ chủ sở hữu sửa; người kia cần đổi thì báo trước hoặc ghi vào Câu hỏi mở):

| Bảo (A) | Linh (B) | Dùng chung |
| :--- | :--- | :--- |
| `pyproject.toml`, `Makefile`, `README.md`, `LICENSE` | `config/*`, `schemas/*`, `ledger/*` | `PLAN.md`: mỗi người chỉ đánh dấu hạng mục của mình và ghi vào mục Nhật ký của mình |
| `descriptors/terrain.py`, `descriptors/astro.py` | `descriptors/spectral.py`, `descriptors/ice.py` | |
| `fidelity.py`, `validation.py`, `scripts/run_all.py` | `io.py`, `discovery.py` | |
| `scripts/targets/moon_*`, `scripts/gee/{tier1_terrain,chip_dem,tier2_lowsun}.py` | `scripts/targets/mica_*`, `scripts/emit/*`, `scripts/gee/tier_x1.py`, `scripts/attention/*` | |
| `docs/validation_report.md`, `docs/figures/*` | `web/*`, slide, `docs/compliance.md` | |

Mọi thư viện cần dùng được khai báo hết trong A0. Linh cần thêm thư viện thì nhờ Bảo thêm vào `pyproject.toml`, tránh xung đột.

### Lịch song song (UTC+7)
| Khung giờ | Bảo (A) — Terrain + Engine | Linh (B) — Spectral + Ice + Story | Cổng |
| :--- | :--- | :--- | :--- |
| 11:45–12:30 | 0.2 tạo tài khoản; 0.1 tuân thủ (cùng Linh) | 0.2 tạo tài khoản; 0.1 tuân thủ (cùng Bảo) | **G0** quyết định SI + tài khoản dùng được |
| 12:30–13:30 | A0 khung repo, merge vào `main` ~13:00 | B0 hợp đồng dữ liệu + GeoJSON mẫu, merge trước 13:30 | Khóa hợp đồng 13:30 |
| 13:30–16:00 | A1 descriptor terrain `[agent]`; A2 khởi chạy export GEE tầng thô; A3 spike Moon (R4); A4 spike Earth (R5) | B1 descriptor phổ `[agent]`; B2 MICA; B3 spike EMIT (R2/R3); B4 web khung `[agent]` | **G1** 16:00 chốt lens |
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
def shadow_fraction(dem, res_m, sun_elev_deg=(2, 5, 7), n_az=16) -> dict[str, float]
    # keys: shadow_e2, shadow_e5, shadow_e7 (trung bình mọi phương vị)
def terrain_descriptors(dem, res_m, L_m) -> dict[str, float]   # gộp ba hàm trên ở baseline L

# descriptors/astro.py
def low_sun_hours(lat_deg: float, max_elev_deg: float = 7.0) -> dict[str, float]
    # keys: lowsun_hours_yr, lowsun_az_coverage (0–1)

# descriptors/spectral.py
COMMON_WL_NM: np.ndarray   # 400–2450 nm, bước 10 nm, đã bỏ 1340–1460 và 1790–1960 nm
def resample(wl_nm: np.ndarray, refl: np.ndarray) -> np.ndarray       # về COMMON_WL_NM
def crism_params(refl: np.ndarray) -> dict[str, float]               # tập con Viviano-Beck 2014, DESIGN 2.2(2)
def sam(a: np.ndarray, b: np.ndarray, window_nm=(2000, 2450)) -> float  # radian, sau khử continuum

# descriptors/ice.py
def ice_config(maat_c, active_layer_m, aridity_p_pet, freeze_thaw_per_yr) -> dict[str, float]

# fidelity.py
@dataclass
class Metric: mean: np.ndarray; cov_inv: np.ndarray; scale: np.ndarray; mode: str  # "full" | "pca" | "diag"
def fit_population(X_pop: np.ndarray, mode: str = "auto") -> Metric   # auto: full nếu n ≥ 5·K, ngược lại diag
def sigma_dissimilarity(E: np.ndarray, t: np.ndarray, m: Metric) -> np.ndarray  # d Mahalanobis → σ qua phân bố χ_K
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
| `earth_<lens>.parquet` | `cell_id, lat, lon, footprint_km, lens_id, tier (1/2), L_m, source, qa_flag,` + cột descriptor |
| `fidelity.parquet` | `cell_id, lens_id, target_id, sigma, percentile, limiting_factor, no_analog (bool), feature_set` |
| `attention.parquet` | `name, query, n_pubs, source, date` |

`candidates.geojson`: theo DESIGN 2.4, bắt buộc có `evidence_status ∈ {engine-confirmed, literature-only, hypothesis}`. File `schemas/candidate.schema.json` là chuẩn kiểm tra.

### Cấu hình
- `config/lenses.yaml`: theo DESIGN 2.4 (`id, body, footprint_km, baseline, descriptors, gates, targets, ledger`).
- `config/targets.yaml`: tọa độ/ROI của mục tiêu. Moon: Connecting Ridge, vành Shackleton (L1/L2), PSR Shackleton (X1, chỉ ledger). Mars: Jezero rìa carbonate, Oxia Planum, Meridiani (M1); Arcadia Planitia (X1).
- `config/controls.yaml`: đối chứng dương (≥10 cặp, theo DESIGN 2.2(5) + NASA Analog Explorer) và mồi nhử (Wadi Rum, cát đỏ thạch anh nội địa Úc), mỗi mục ghi `lens_id, lat, lon, footprint_km, source`.

## Hạng mục

Nhãn: **[A]** / **[B]** = chủ sở hữu; **[agent]** = giao được cho agent, người chủ duyệt; **Chờ** = phụ thuộc.

### Giai đoạn 0 — Tài khoản, tuân thủ và hợp đồng (11:45–13:30)
- [ ] 0.2. **[A+B] Tạo tài khoản — điều kiện chặn của A2, A3, A6, B3, B5, B6.** Mỗi người tự làm cho mình:
  - **NASA Earthdata Login:** đăng ký tại https://urs.earthdata.nasa.gov/users/new (cấp ngay); tạo file `~/.netrc` hoặc dùng `earthaccess.login(persist=True)`.
  - **Google Earth Engine:** tạo Google Cloud project, đăng ký Earth Engine loại phi thương mại (noncommercial / research) tại https://code.earthengine.google.com/register, bật Earth Engine API cho project đó; xác thực bằng `earthengine authenticate`. Ghi tên project vào biến môi trường `EE_PROJECT` (không commit vào repo).
  - Xong khi: chạy được `python -c "import earthaccess; earthaccess.login()"` và `python -c "import ee, os; ee.Initialize(project=os.environ['EE_PROJECT']); print(ee.Number(1).getInfo())"`.
  - Kiểm chứng: mỗi người ghi một dòng xác nhận vào Nhật ký của mình (không ghi mật khẩu, token, email).
  - **Nếu GEE chưa được duyệt trước 13:30:** Bảo lấy DEM Copernicus GLO-30 từ bucket công khai trên AWS (`s3://copernicus-dem-30m`, không cần tài khoản) cho A4/A6, và thay tầng thô toàn cầu A2 bằng danh sách hạt giống `config/seeds.yaml`. Linh dùng `earthaccess` để tải EMIT trực tiếp, giới hạn ≤ 30 footprint. Ghi quyết định vào Câu hỏi mở.
- [ ] 0.1. **[A+B]** Đọc nguyên văn Project Submission Guide, FAQ phần SI, trang đề (tab Resources, 12 Considerations, giới hạn 7 slide / 30 s); hỏi Local Lead nếu điều khoản SI mơ hồ. Đội tự quyết phần ý tưởng nào giữ, sửa, bỏ và ghi lại cách đã dùng SI — File: `docs/compliance.md` — Xong khi: có quyết định G0 bằng văn bản (tiếp tục / điều chỉnh ý tưởng), danh sách tài nguyên chính thức, định dạng nộp đã xác nhận — Kiểm chứng: hai người cùng đọc và ký tên trong file.
- [ ] A0. **[A]** Khung repo: `pyproject.toml` (Python ≥3.11; numpy, scipy, pandas, pyarrow, rasterio, xarray, netCDF4, pyyaml, jsonschema, earthaccess, earthengine-api, requests; dev: pytest, ruff), `Makefile`, `LICENSE` Apache-2.0, `.gitignore` có `data/raw/`, README khung, gói `src/similitude` rỗng — Xong khi: cài được bằng `pip install -e .[dev]`, PR đã merge vào `main` — Kiểm chứng: `make test` (0 test, không lỗi) và `make lint` sạch.
- [ ] B0. **[B]** Hợp đồng dữ liệu: `config/lenses.yaml`, `config/targets.yaml`, `config/controls.yaml`, `schemas/candidate.schema.json`, `web/data/candidates.mock.geojson` (3 feature giả đủ mọi trường, mỗi lens ít nhất một), `src/similitude/io.py` có `validate_candidates(path)` — Chờ: A0 (chỉ phần `io.py`; file cấu hình/schema soạn được ngay) — Xong khi: hai người đồng ý, PR đã merge vào `main`, không đổi schema sau 13:30 nếu không báo cả hai — Kiểm chứng: `pytest tests/test_schema.py` (file mẫu hợp lệ; thiếu `evidence_status` thì báo lỗi).

### Giai đoạn 1 — Thư viện và phép thử (13:30–16:00)
- [ ] A1. **[A][agent]** `descriptors/terrain.py` + `descriptors/astro.py` theo chữ ký trên — File: `src/similitude/descriptors/{terrain,astro}.py`, `tests/test_terrain.py`, `tests/test_astro.py` — Xong khi: mọi test pass — Kiểm chứng: `pytest tests/test_terrain.py tests/test_astro.py`, gồm: mặt phẳng nghiêng 10° → `slope_p50` = 10 ± 0,1; mặt phẳng → `shadow_*` = 0 và `frac_gt8` = 0; mặt fBm tổng hợp với H = 0,7 → `hurst` = 0,7 ± 0,1; `aggregate_to_baseline` 5 m → 30 m giữ trung bình; vĩ độ 0° → `lowsun_hours_yr` < vĩ độ 85°.
- [ ] A2. **[A]** Export GEE tầng thô toàn cầu ở 10 km cho các lens terrain: mặt nạ đất trơ (MODIS NDVI, ESA WorldCover, loại nước/đô thị/canh tác), khô hạn, độ dốc thô Copernicus GLO-30, MODIS snow cho L2; loại vùng đệm quanh 4 điểm kinh điển và các điểm NASA Analog Explorer — File: `scripts/gee/tier1_terrain.py` — **Khởi chạy trước 14:00**, cho chạy nền — Xong khi: CSV ô ứng viên tải về `data/derived/tier1_terrain.csv` — Kiểm chứng: số ô > 0; các đối chứng dương L1/L2 (vd Devon Island, Haughton) nằm trong mặt nạ; không ô nào trong vùng đệm loại trừ. Đường lùi (R7): danh sách hạt giống ~150 footprint (hố va chạm, trường núi lửa Holocene, cao nguyên cực) trong `config/seeds.yaml`.
- [ ] A3. **[A]** Spike R4 — mục tiêu Moon: tải tile PGDA Product 78 / LOLA cực quanh Connecting Ridge và vành Shackleton; tính `terrain_descriptors` ở L = 30 m cho 2 mục tiêu và ≥ 40 footprint ngẫu nhiên trong 6° quanh cực (quần thể Σ) — File: `scripts/targets/moon_terrain.py` → `data/derived/targets_L1.parquet` — Chờ: A1 (có thể viết script song song, chạy sau) — Xong khi: bảng đủ cột theo schema — Kiểm chứng: trung vị dốc khác bản đồ dốc có sẵn của PGDA ≤ 2°. Trượt → dùng thẳng sản phẩm dốc/chiếu sáng PGDA, ghi vào Câu hỏi mở.
- [ ] A4. **[A]** Spike R5 — tách biệt địa hình: chip DEM 10 km cho 5 điểm Trái Đất (2 đối chứng dương L1 + 3 ngẫu nhiên trên đất trơ), tính descriptor, tính σ thô (dạng đường chéo) so với mục tiêu Connecting Ridge — File: `scripts/gee/chip_dem.py`, `notebooks/spike_r5.ipynb` — Chờ: A1, A3 — Xong khi: có bảng σ cho 5 điểm — Kiểm chứng: cả hai đối chứng dương có σ nhỏ hơn cả ba điểm ngẫu nhiên. Trượt → thêm `roughness_spectrum` hoặc thu footprint về 2 km, ghi kết quả vào Nhật ký.
- [ ] B1. **[B][agent]** `descriptors/spectral.py` theo chữ ký trên, tham số lấy theo Viviano-Beck 2014, rút gọn **giống nhau ở cả hai phía** với tham số chạm dải bị che — File: `src/similitude/descriptors/spectral.py`, `tests/test_spectral.py` — Xong khi: test pass; docstring mỗi tham số ghi bước sóng gốc và bước sóng đã thay — Kiểm chứng: `pytest tests/test_spectral.py`, gồm: phổ phẳng → mọi band depth ≈ 0; phổ có hấp thụ Gauss ở 2300 nm → `D2300` > 0,05 và `BD2210` ≈ 0; hấp thụ ở 2210 nm → ngược lại; `sam(a, a)` = 0.
- [ ] B2. **[B]** Nạp MICA: tải volume `mrocr_8001` (~3 MB) từ PDS Geosciences / crismtypespectra.rsl.wustl.edu, đọc các phổ chuẩn, cắt ≤ 2450 nm, `resample`, tính `crism_params` — File: `scripts/targets/mica_ingest.py` → `data/derived/mica.parquet`, `data/derived/targets_M1.parquet` — Chờ: B1 — Xong khi: có vector mục tiêu cho các lớp carbonate (Jezero), Fe/Mg-smectite (Oxia/Mawrth), olivine, jarosite (Meridiani); toàn bộ ~30 phổ MICA làm quần thể Σ — Kiểm chứng: phổ carbonate có `MIN2295_2480` > 0, phổ olivine có `OLINDEX` cao nhất nhóm.
- [ ] B3. **[B]** Spike R2/R3 — CRISM trên EMIT: (i) xác định ID tập EMIT trên GEE (`NASA/EMIT/L2A_RFL` hay `NASA/EMIT/L2A/RFL`); (ii) tìm cảnh ít mây tại Lake Salda, một điểm peridotit Semail (Oman), Wadi Rum, Harrat Khaybar, Matanomadh; (iii) lấy phổ trung vị footprint (bỏ pixel mây/nước/thực vật), tính tham số — File: `scripts/emit/spike_r2.py`, `notebooks/spike_r2.ipynb` — Chờ: B1, B2 — Xong khi: có bảng tham số + σ so với mục tiêu carbonate/olivine — Kiểm chứng (**tiêu chí G1 cho M1**): Lake Salda và Semail có σ nhỏ hơn Wadi Rum so với mục tiêu Jezero. Trượt → đường lùi theo thứ tự: sản phẩm EMIT L2B mineral (LP DAAC) → chỉ số SWIR Sentinel-2 + ASTER GED.
- [ ] B4. **[B][agent]** Web khung đọc `candidates.mock.geojson`: bản đồ MapLibre hoặc Leaflet, bộ chọn lens, marker tô màu theo σ, panel Test Card hiển thị đủ trường (fidelity theo lens, yếu tố giới hạn, quá trình, test here / cannot test, attention, evidence status, nguồn dữ liệu); không backend — File: `web/index.html`, `web/app.js`, `web/style.css` — Chờ: B0 — Xong khi: mở bằng `python -m http.server -d web` thấy đủ 3 feature giả, đổi lens thì màu đổi — Kiểm chứng: thử tay trên Chrome desktop và khung 375 px; console không lỗi.
- [ ] G1. **[A+B] 16:00 — cổng chốt lens** (15 phút): dựa trên A3, A4, B3 quyết định đường chính hay đường lùi cho từng lens; ghi vào Nhật ký. **Không thêm lens sau G1.**

### Giai đoạn 2 — Xây dựng (16:00–22:00)
- [ ] A5. **[A][agent]** `fidelity.py` theo chữ ký trên — File: `src/similitude/fidelity.py`, `tests/test_fidelity.py` — Xong khi: test pass — Kiểm chứng: `pytest tests/test_fidelity.py`, gồm: E = t → σ ≈ 0; σ tăng đơn điệu khi dịch xa dần; n < 5·K → tự chuyển `diag`; Σ suy biến không làm crash (PCA hoặc diag); `limiting_factor` trả đúng descriptor bị dịch trong ca thử; `no_analog` = True khi σ nhỏ nhất > 2.
- [ ] A6. **[A]** Tầng mịn terrain: chip DEM Copernicus 30 m cho top ~300 ô của A2 + mọi đối chứng/mồi nhử L1/L2 + hạt giống; tính descriptor bằng A1 — File: `scripts/gee/chip_dem.py` → `data/derived/earth_L1.parquet` — Chờ: A1, A2 — Xong khi: ≥ 90 % chip có `qa_flag` = ok — Kiểm chứng: đếm hàng; vẽ histogram `slope_p50` để soi giá trị bất thường; chip ven biển/vùng thiếu dữ liệu được đánh cờ, không bị âm thầm loại.
- [ ] A7. **[A]** Descriptor L2 phía Trái Đất: `low_sun_hours` theo vĩ độ ô + tỷ lệ không tuyết trong các tháng Mặt Trời thấp (MODIS snow) + `shadow_fraction`; phía Moon: hằng số của mục tiêu đối chiếu bản đồ chiếu sáng PGDA — File: `scripts/gee/tier2_lowsun.py` → `data/derived/earth_L2.parquet`, `data/derived/targets_L2.parquet` — Chờ: A1, A6 — Xong khi: bảng đủ cột — Kiểm chứng: Devon Island và Peary Land xếp trên mọi ô vĩ độ < 60° theo `lowsun_hours_yr`.
- [ ] B5. **[B]** Ứng viên M1 và trích phổ: tầng thô = đất trơ ∧ trong vùng phủ EMIT (±52°) ∧ chỉ số mafic ASTER GED + danh sách hạt giống (ophiolite, trường bazan, evaporite); tầng mịn = phổ trung vị EMIT cho ≤ 100 footprint, ưu tiên rút gọn trên GEE; nếu phải tải bằng earthaccess thì giới hạn ≤ 30 footprint — File: `scripts/emit/tier_m1.py` → `data/derived/earth_M1.parquet` — Chờ: B1, G1 — **Khởi chạy tải trước 18:00** — Xong khi: mọi đối chứng dương và mồi nhử M1 có phổ — Kiểm chứng: `qa_flag` ghi số pixel hợp lệ; footprint < 50 pixel hợp lệ bị đánh cờ.
- [ ] B6. **[B]** X1 rút gọn: phía Trái Đất tính MAAT, permafrost (Obu 2019 hoặc ESA CCI), P/PET, số chu kỳ đóng–tan từ MODIS LST ở 10 km; phía Mars mã hóa cấu hình từ SWIM cho Arcadia (băng < 1 m dưới lớp phủ khô); so sánh **cấu hình** (cờ + tỷ số), ghi rõ `evidence_status` tối đa là bán định lượng — File: `src/similitude/descriptors/ice.py`, `scripts/gee/tier_x1.py` → `data/derived/earth_X1.parquet` — Chờ: G1 — Xong khi: có bảng xếp hạng X1 — Kiểm chứng: vùng Pamir/Changtang và các hoang mạc cực xếp trên vùng permafrost ẩm (vd đồng bằng Siberia). Nếu SWIM không tải được dạng raster, ghi Câu hỏi mở và dùng mô tả định tính từ ảnh PIA26046.
- [ ] B7. **[B]** Transfer Ledger: điền `ledger/moon.yaml`, `ledger/mars.yaml` theo bảng DESIGN 2.2(4); **mỗi con số kèm nguồn đã tra lại** (R10); số nào không tra được thì bỏ; liên kết gap kiến trúc NASA Moon to Mars đã xác nhận tên — Xong khi: không còn mục gắn [Nhớ] — Kiểm chứng: mỗi mục có trường `source` dạng URL hoặc DOI.
- [ ] B8. **[B][agent]** Attention Index: truy vấn OpenAlex theo DESIGN 2.2(6); tên dễ nhầm dùng thêm từ định danh (vd "Karakul" phải kèm "crater" hoặc "Tajikistan") — File: `scripts/attention/openalex.py` → `data/derived/attention.parquet` — Xong khi: có số cho mọi ứng viên và đối chứng — Kiểm chứng (R13): Atacama ≫ Harrat Khaybar; lưu nguyên văn chuỗi truy vấn và ngày tra.
- [ ] CP1. **[A+B] 22:00 — checkpoint** (10 phút): mọi bảng `earth_*` và `targets_*` có mặt; nếu một lens chưa đủ dữ liệu, cắt lens đó ngay (thứ tự cắt: X1 → L2). Mỗi người chạy `make test && make lint` + `claude-prereview` trên nhánh mình, mở PR, merge vào `main`; người còn lại `git merge main`. A8 cần dữ liệu của Linh nên phải merge xong trước khi bắt đầu.

### Giai đoạn 3 — Tích hợp và Data Freeze (22:00–03:00)
- [ ] A8. **[A]** Chấm điểm và validation: `score_lens` cho từng lens; `validation.py`: percentile đối chứng dương trên phân bố null của toàn bộ ô, điểm mồi nhử, ablation (a) RGB/texture (dựng lại kiểu NHSJS 2026 trên ảnh Sentinel-2) với (c) twin-formula, độ nhạy (đổi L, bỏ từng descriptor, lắc ngưỡng mặt nạ) — File: `src/similitude/validation.py`, `tests/test_validation.py`, `scripts/run_all.py` → `data/derived/fidelity.parquet`, `data/derived/validation.parquet` — Chờ: A5, A6, A7, B5, B6 — Xong khi: `python scripts/run_all.py` chạy từ đầu đến cuối không lỗi — Kiểm chứng: `pytest tests/test_validation.py` (dữ liệu tổng hợp có ô cài sẵn phải đứng top); ghi **nguyên trạng** kết quả vào Nhật ký, kể cả khi kỳ vọng trong DESIGN không xảy ra.
- [ ] B9. **[B]** Discovery và xuất GeoJSON: lọc fidelity percentile cao ∧ attention thấp ∧ ngoài vùng đệm loại trừ; gộp ô kề nhau (non-max suppression theo khoảng cách ≥ footprint); gán `evidence_status`; điền `process_title`, `test_here`, `cannot_test` (từ ledger) — File: `src/similitude/discovery.py`, `tests/test_discovery.py` → `web/data/candidates.geojson` — Chờ: A8, B7, B8 — Xong khi: file qua `validate_candidates`; mỗi lens MVP có ≥ 1 ứng viên `engine-confirmed` hoặc lens đó được ghi là "no hidden analog found" — Kiểm chứng: `pytest tests/test_discovery.py` (hai ô cách nhau < footprint chỉ còn một).
- [ ] B10. **[B]** Đọc lại từng ứng viên top bằng ảnh Sentinel-2 / NASA Worldview để loại lỗi dữ liệu (mây sót, ruộng, mỏ lộ thiên); tiêu đề Test Card theo quá trình — Xong khi: ứng viên nghi vấn hạ xuống `hypothesis` kèm ghi chú — Kiểm chứng: hai người cùng duyệt danh sách cuối.
- [ ] DF. **[A+B] 03:00 — Data Freeze:** đóng băng `data/derived/` và `web/data/candidates.geojson`; ứng viên không phải `engine-confirmed` không lên slide. Mỗi người chạy `claude-prereview` rồi `claude-gate-diff` trên nhánh mình, merge vào `main` khi SHIP. Trước khi ngủ, giao B11 cho agent chạy trên nhánh của Linh với dữ liệu thật.

### Giai đoạn 4 — Sản phẩm (07:30–15:00)
- [ ] A9. **[A]** `docs/validation_report.md` + hình trong `docs/figures/`: biểu đồ percentile đối chứng dương, so sánh mồi nhử (RGB vs twin-formula), recall@k của ablation, bản đồ σ cho mỗi lens — Chờ: A8 — Xong khi: mỗi khẳng định trong slide 3–5 đều trỏ được tới một hình hoặc bảng trong báo cáo — Kiểm chứng: B đọc chéo.
- [ ] A10. **[A]** README: mục đích, cách tái lập (`pip install -e .`, `python scripts/run_all.py`), danh sách đầy đủ dữ liệu NASA và đối tác kèm DOI, giới hạn đã biết (dải phổ bị che, EMIT ±52°, analog dưới pixel), khai báo SI, giấy phép — Xong khi: người ngoài clone về làm theo được — Kiểm chứng: clone vào thư mục tạm, chạy lại `make test`.
- [ ] B11. **[B][agent]** Web hoàn thiện trên `candidates.geojson` thật: hình hồ sơ lens (radar chart) trong Test Card, bảng Transfer Ledger, liên kết báo cáo validation, phần "Data & limits"; tùy chọn Near-me và nền Moon/Mars Trek nếu R12 ổn — Chờ: B9 — Xong khi: triển khai lên GitHub Pages — Kiểm chứng: mở URL ở cửa sổ ẩn danh trên máy tính và điện thoại; không lỗi console.
- [ ] B12. **[B]** Slide nháp 7 trang theo DESIGN 2.6 (hoặc kịch bản video 30 s nếu 0.1 chọn video), tiếng Anh, mọi con số lấy từ `validation_report.md` — Chờ: A9 (có thể dựng bố cục trước) — Xong khi: đủ 7 slide — Kiểm chứng: A đối chiếu từng con số với báo cáo.
- [ ] CF. **[A+B] 15:00 — Code Freeze:** `make test && make lint` sạch; `claude-prereview` → `claude-gate-diff` trên từng nhánh; merge PR vào `main` sau khi SHIP. `main` là bản nộp: repo công khai trỏ vào `main`, GitHub Pages build từ `main`.

### Giai đoạn 5 — Nộp bài (15:00–21:00)
- [ ] 5.1. **[A+B]** Hoàn thiện slide; điền trang Project bằng tiếng Anh (tóm tắt, dữ liệu NASA/đối tác, khai báo SI theo kết luận ở 0.1, tính nguyên bản) — Kiểm chứng: đọc chéo.
- [ ] 5.2. **[A+B]** Kiểm tra mọi link (slide, repo, web) ở cửa sổ ẩn danh; rà quy định ảnh/giọng người dưới 18 tuổi; kiểm tra tab Members — Kiểm chứng: checklist trong `docs/compliance.md` đánh dấu đủ.
- [ ] 5.3. **[A+B]** Nộp trước 21:00, chụp màn hình xác nhận — Kiểm chứng: trang Project hiển thị trạng thái đã nộp.

## Edge-cases
- **Hệ chiếu cực:** DEM Mặt Trăng ở polar stereographic; tính dốc trên lưới chiếu với kích thước pixel đúng, không dùng độ góc kinh/vĩ. Chip Trái Đất ở vĩ độ cao (Devon, Peary Land) phải chiếu về UTM hoặc polar stereographic cục bộ trước khi tính.
- **Chênh độ phân giải:** mọi so sánh dùng chung L; quên gộp về L là lỗi nghiêm trọng nhất của pipeline terrain. `terrain_descriptors` phải bắt buộc truyền `L_m`.
- **Vùng phủ EMIT:** đối chứng dương ngoài ±52° (Devon Island) không được dùng cho M1. Mồi nhử và đối chứng M1 phải nằm trong vùng phủ.
- **Pixel phổ hỏng:** mây, bóng mây, nước, thực vật dư (NDVI > ngưỡng), cát ẩm, mỏ lộ thiên. Phổ MICA có dải tới 3,9 µm: cắt ở 2,45 µm trước khi tính, không ngoại suy.
- **Thang phản xạ:** MICA là I/F đã hiệu chỉnh, EMIT là phản xạ bề mặt. So **band depth và hình dạng** (tham số, SAM sau khử continuum), không so giá trị tuyệt đối.
- **Σ kém điều kiện:** quần thể ít mẫu, descriptor tương quan mạnh (vd `rms_s1` và `slope_p50`). `fit_population` phải tự lùi về `diag`, và ghi `mode` ra kết quả.
- **Quần thể M1:** chỉ ~30 phổ MICA, trải nhiều lớp khoáng; Σ khi đó đo "biến thiên giữa các lớp khoáng trên Sao Hỏa". Ghi rõ điều này trong báo cáo.
- **Ô trùng lặp:** nhiều ô kề nhau cùng điểm cao → non-max suppression trước khi đặt tên ứng viên.
- **Analog dưới pixel** (Kamil, hang băng): không đưa vào chấm; nếu nêu trong slide thì `evidence_status` = `literature-only`.
- **Trùng tên trong OpenAlex:** "Karakul" (giống cừu), "Lut", "Kamil". Dùng tên kèm định danh địa lý; lưu nguyên văn truy vấn.
- **Vùng nhạy cảm:** chỉ số tiếp cận và ghi chú an ninh chỉ là thông tin, không dùng để xếp hạng nếu chưa làm phần tùy chọn.
- **Hạn ngạch GEE:** export lớn có thể bị xếp hàng lâu; chia lô theo vùng, dùng `computePixels` cho chip nhỏ.

## Câu hỏi mở
- Kết quả G0 về quy định SI (0.1): cần đội xác nhận trước khi triển khai.
- Nộp slide hay video 30 s? Điểm thi TP. HCM có thuyết trình trực tiếp không?
- Tài khoản Earthdata và GEE (0.2) của cả hai chưa có tại 11:45. Nếu GEE chưa được duyệt trước 13:30, dùng đường lùi ghi ở 0.2.
- Kế hoạch giả định Bảo mạnh xử lý raster/Python, Linh mạnh dữ liệu phổ và trình bày. Nếu không đúng, đổi nguyên lát dọc giữa hai người, không đổi từng hạng mục.

## Nhật ký
- 2026-11-14 · Opus 5.5 · soạn PLAN.md từ DESIGN.md cho đội 2 người; cập nhật phân vai Bảo/Linh, tài khoản, quy tắc nhánh · test: chưa có code

### Nhật ký — Bảo (A)

### Nhật ký — Linh (B)
