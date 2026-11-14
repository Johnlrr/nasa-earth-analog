# DESIGN: SIMILITUDE — tìm "bãi thử" trên Trái Đất cho Moon Base và Sao Hỏa bằng đồng dạng vật lý theo nhiệm vụ

> Soạn: 14/11/2026 ~11:30 (UTC+7), Fable 5.2 (Solution Architect). Đầu vào: `ABOUT.md` + prompt của người dùng (không có `BRIEF.md`).
> Quy ước độ tin cậy: **[Đã kiểm]** = tra được nguồn trong phiên này; **[Nhớ]** = từ kiến thức nền, chưa tra lại; **[Giả thuyết]** = suy luận, phải để dữ liệu xác nhận.
> Tên "SIMILITUDE" là tên làm việc, đội tự đặt lại.
> **Cập nhật G1 (14/11 ~16:45):** xem `docs/review_g1.md`. Bản review thay thế tài liệu này ở các điểm: M1 so khớp theo pixel thay cho trung vị footprint; phán quyết ba trạng thái (TRANSFERS / NO-ANALOG / UNOBSERVED); native rank và matched area; các kỳ vọng đã bị dữ liệu bác (Lake Salda ở tỷ lệ 5 km, Haughton cho L1, Pamir–Changtang cho X1).

---

## 1. Vấn đề & ràng buộc đã xác nhận

### 1.1. Bài toán cốt lõi (phân tích từ gốc)

NASA không dùng analog để "ngắm cho giống". Analog là **đồ gá thử nghiệm (test fixture)**: nơi một thiết bị, quy trình hay giả thuyết khoa học được thử trong "môi trường liên quan" trước khi bay. Trong quy trình kỹ thuật hệ thống của NASA, TRL 5–6 đòi hỏi kiểm chứng trong *relevant environment* [Nhớ: NPR 7123.1]; analog thực địa là một dạng môi trường đó. Từ đây suy ra ba hệ quả mà phần lớn đội thi bỏ qua:

1. **Độ tương đồng luôn tương đối theo nhiệm vụ.** Một nơi có thể là analog tuyệt vời cho thử radar tìm băng nhưng vô dụng cho thử bánh xe. Hỏi "nơi nào giống Sao Hỏa" là hỏi sai; câu đúng là "phép thử X cho kết quả chuyển giao được ở đâu". Khái niệm này đã có tên trong văn liệu: *functional analogue* (Foucher và cs. 2021, Planetary & Space Science 197:105162) [Đã kiểm] — nhưng mới ở mức khung khái niệm, chưa ai hiện thực hóa thành công cụ tính toán toàn cầu trên dữ liệu NASA (theo những gì tra được).
2. **Giá trị của analog nằm ở biến số mà phép thử nhạy cảm, không nằm ở ngoại hình.** Kỹ sư hầm gió không hỏi mô hình có giống máy bay không; họ hỏi các số không thứ nguyên có khớp không (luật đồng dạng, Buckingham π). Đây là khung lý thuyết sẵn có để so sánh hai thế giới khác trọng lực và khí quyển.
3. **Phần không tái tạo được cũng là sản phẩm.** Người lập kế hoạch thử nghiệm cần biết chính xác phần nào phải chuyển sang buồng chân không, bay parabol hay hệ treo giảm trọng lực. "Delta-Limit" trong ABOUT.md phải là **con số tính ra**, không phải đoạn văn tuyên bố.

### 1.2. Ràng buộc cứng

| Ràng buộc | Giá trị | Trạng thái |
| :--- | :--- | :--- |
| Thời gian | 09:00 14/11 → 23:59 15/11/2026 (giờ địa phương Team Owner). Lúc soạn tài liệu này đã trôi ~2,5 giờ. Mục tiêu nộp 21:00 15/11. | Theo ABOUT.md |
| Nộp bài | 1 link công khai: ≤7 slides (gồm bìa) hoặc video ≤30 s; tiếng Anh; mọi link mở được ở cửa sổ ẩn danh | Theo tóm tắt địa phương trong ABOUT.md; **chưa đọc được toàn văn Submission Guide** |
| Dữ liệu | Bắt buộc dùng và giải trình dữ liệu NASA / Space Agency Partner | Theo ABOUT.md |
| SI/AI | Phải khai báo cách dùng. Bản tóm tắt Purwokerto ghi **không dùng SI để nghĩ ra ý tưởng cốt lõi** | **Rủi ro tuân thủ trực tiếp với chính tài liệu này — xem R0 ở mục 4** |
| Giấy phép | Mã nguồn mở OSI (mặc định Apache 2.0) | Theo ABOUT.md |
| Nhân lực | 4–5 người | Theo prompt |
| Phủ đề | Cả Moon Base (số nhiều: "Permanent Moon Base Locations") lẫn Sao Hỏa | Tên đề |

**Không truy cập được trang đề chính thức trong phiên này** (trang render bằng JS, lỗi chứng chỉ). Tab Resources, 12 Potential Considerations nguyên văn và Judging Guide chỉ biết qua ABOUT.md. Đội phải đối chiếu trực tiếp trước khi chốt.

Bối cảnh Moon Base 2026 [Đã kiểm, qua báo chí và tiêu đề tài liệu NASA, chưa đọc được toàn văn PDF 10 MB]: NASA công bố *Moon Base Architecture User's Guide* (04/2026); căn cứ ở vùng Cực Nam, mục tiêu được nêu là **vành Shackleton và Connecting Ridge**; Phase I đến 2029 với hơn 20 lần hạ cánh robot; hai thách thức môi trường được chính tài liệu nhấn mạnh là **chiếu sáng và địa hình**. Điều này định hướng trực tiếp lựa chọn lens Mặt Trăng bên dưới.

### 1.3. Ràng buộc mềm: giám khảo và đối thủ

**Những gì đã tồn tại và khoảng trống của chúng:**

| Nguồn | Đã làm gì | Khoảng trống khai thác được |
| :--- | :--- | :--- |
| NASA Analog Explorer [Đã kiểm] | ~7–8 cặp kể chuyện: lava caves California–Moon, Kilauea–Moon, Pilot Valley Utah–Mars, Atacama–Mars, Iceland–Mars, California–Mars, Lake Salda–Mars, Alaska–Enceladus | Định tính, không có thước đo, không truy vấn được, không có lý do "vì sao không phải nơi khác" |
| Danh mục Preston và cs. (ESA CAFE, 2012–2013) và tổng quan 33 điểm (Int. J. Astrobiology 2013) [Đã kiểm] | Danh mục điểm analog đầy đủ nhất | Chính các tác giả nêu: **chưa có cơ sở dữ liệu mở toàn cầu, chưa có tiêu chí đánh giá rõ ràng** |
| USGS TARGET + Terrestrial Analogs Survey (OMB 1028-0140, gia hạn 2026) [Đã kiểm] | Khảo sát nhu cầu cộng đồng về điểm analog, kho dữ liệu, bộ mẫu | Bằng chứng rằng nhu cầu là thật và đang được cơ quan liên bang hỏi ý kiến ngay năm nay; chưa có công cụ tìm kiếm định lượng |
| Foucher và cs. 2021 [Đã kiểm] | Định nghĩa functional analogue, phân loại theo công dụng | Chưa có hiện thực tính toán |
| Xếp hạng bằng texture ảnh (NHSJS 2026) [Đã kiểm] | So 10 điểm Trái Đất với Moon/Mars bằng độ sáng và độ nhám ảnh | Xếp **Devon Island — nơi NASA đặt Haughton-Mars Project — kém nhất**, "Nevada Desert" tốt nhất. Đây là minh chứng định lượng có sẵn cho bẫy thị giác, dùng được ở slide 2 |
| Metric learning ảnh Earth–Mars ở Qaidam (arXiv 2501.08584) [Đã kiểm] | CNN học độ tương đồng ảnh để chọn điểm trong một vùng analog | Vẫn là tương đồng ảnh, phạm vi một vùng |
| Dự án Space Apps 2023–2025 về analog | **Không tra được** dự án analog nào (trang cũ không lập chỉ mục tốt). Theo trí nhớ, các năm đó không có đề riêng về analog | Không dựa được vào tiền lệ; coi như sân trống nhưng cũng không có mẫu để học |

**Dự đoán phân bố đối thủ [Giả thuyết]:** ~50% liệt kê địa danh nổi tiếng + bản đồ đánh dấu; ~30% chatbot/LLM hoặc "AI similarity" trên ảnh RGB; ~15% chồng lớp GEE với điểm trọng số tự gán; <5% có so sánh vật lý chéo hành tinh thật. Vậy vùng khác biệt là: (a) cùng một công thức chạy trên dữ liệu của cả hai thế giới, (b) kiểm chứng có đối chứng âm, (c) phần không tái tạo được có số, (d) đầu ra là phiếu thử nghiệm chứ không phải điểm trên bản đồ.

---

## 2. Phương án chọn

### 2.1. Tên và Innovation Hook

**SIMILITUDE — the proving-ground finder.**

> *"Wind-tunnel engineers never ask whether the model looks like the aircraft. They ask whether the dimensionless numbers match. We apply the same law to planets: one formula, run on NASA data from both worlds, per mission task — and we report exactly which test results will transfer and which never can."*

Ba khẳng định mà cả bài thi phải chứng minh bằng số:

1. **Same formula, both worlds.** Mọi chỉ số được tính bằng cùng một công thức, cùng một baseline không gian, trên dữ liệu Trái Đất và dữ liệu Moon/Mars. Không có chỗ cho so ảnh.
2. **Fidelity is per mission task.** Không có điểm tổng. Mỗi địa điểm có hồ sơ theo từng *lens nhiệm vụ*.
3. **The gap is a deliverable.** Với mỗi lens, hệ thống xuất danh sách đại lượng không tái tạo được kèm tỷ số, và đánh dấu mục tiêu "no-analog" khi không nơi nào trên Trái Đất đủ gần.

### 2.2. Cơ chế hoạt động

```
 [A] TARGET PROFILER            [B] EARTH PROFILER
 Moon/Mars footprints           Lưới ứng viên Trái Đất (GEE)
 (LOLA/PGDA, MOLA/HRSC,         (Copernicus DEM, EMIT, MODIS,
  MICA/CRISM, SWIM, Diviner)     ASTER GED, khí hậu, permafrost)
          \                         /
           v                       v
        [C] TWIN-FORMULA DESCRIPTORS  (cùng công thức, cùng baseline L)
                      |
        [D] FIDELITY ENGINE  (σ-dissimilarity theo lens + yếu tố giới hạn)
                      |
        [E] VALIDATION HARNESS  (đối chứng dương, mồi nhử, phân bố null, ablation)
                      |
        [F] DISCOVERY FILTER  (loại vùng kinh điển, Attention Index, khả năng tiếp cận)
                      |
        [G] ANALOG TEST CARD + TRANSFER LEDGER  → GeoJSON tĩnh → Web app
```

#### (1) Mission Lens — đơn vị tổ chức của toàn hệ thống

Mỗi lens = một nhiệm vụ thử nghiệm cụ thể + footprint vận hành (quyết định tỷ lệ không gian, giải lỗi "nhầm tỷ lệ") + bộ descriptor + sổ chuyển giao.

| Lens | Thiên thể | Câu hỏi thử nghiệm | Footprint | Mục tiêu tham chiếu (khóa sớm) | Pipeline | Ưu tiên |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **L1 Touchdown & Traverse** | Moon | Nơi nào có phân bố dốc/nhám như bãi đáp và hành lang LTV ở Cực Nam? | 2 km (EVA) và 10 km (LTV) | Connecting Ridge / vành Shackleton; Mons Mouton | Terrain | MVP |
| **L2 Low-Sun Navigation** | Moon | Nơi nào cho bóng đổ dài, Mặt Trời sát chân trời trên nền đất trơ để thử cảm biến dẫn đường? | 10 km | Như L1 | Terrain + thiên văn | MVP (rẻ, ăn theo L1) |
| **M1 Aqueous Minerals & Biosignature** | Mars | Nơi nào đang có cùng tổ hợp khoáng biến đổi do nước? | 5 km | Jezero (olivine–carbonate); Oxia Planum / Mawrth (Fe/Mg-smectite; Oxia là bãi đáp Rosalind Franklin của ESA); tùy chọn Meridiani (sulfate/jarosite) | Spectral | **MVP, trung tâm sáng tạo** |
| **X1 Ice under Dry Overburden** | Mars + Moon | Nơi nào có băng nông dưới lớp phủ khô để thử khoan 1 m, GPR, neutron? | 10 km | Arcadia Planitia (SWIM); PSR Shackleton/Faustini | Ice | MVP nếu qua cổng G1, nếu không thì bản rút gọn |
| M2 Aeolian & Dust | Mars | Nơi nào gió đang tạc yardang/megaripple, nâng bụi? | 20 km | Medusae Fossae; Gale | Process | Stretch |
| L3 Highland Feedstock | Moon | Nơi nào có anorthosite lộ trần cho ISRU cao nguyên? | 5 km | Regolith feldspathic Cực Nam | TIR | Stretch |

Ba pipeline (Terrain, Spectral, Ice) phục vụ bốn lens MVP, phủ cả hai thiên thể. Đây là điểm kiểm soát phạm vi quan trọng nhất của bản thiết kế.

#### (2) Twin-formula descriptors — sửa hai lỗi kỹ thuật trong khung ABOUT.md

**Lỗi 1 cần sửa: TRI phụ thuộc kích thước pixel.** TRI tính trên DEM Trái Đất 30 m và TRI trên MOLA 463 m không so được với nhau. Quy tắc bắt buộc: **mỗi cặp so sánh dùng chung baseline L = độ phân giải thô hơn trong hai bên**, bên mịn hơn được gộp về L trước khi tính.

**Lỗi 2 cần sửa: so phổ trực tiếp cube CRISM thô với EMIT là không khả thi trong 48 giờ** (hiệu chỉnh khí quyển Sao Hỏa, nhiễu, định dạng PDS). Thay bằng: chạy **đúng bộ công thức summary parameter của CRISM (Viviano-Beck và cs. 2014, 60 tham số) trên phản xạ EMIT**, và phía Sao Hỏa dùng **thư viện MICA** — 30 phổ chuẩn khoáng vật lấy từ chính bề mặt Sao Hỏa, tải ~3 MB từ PDS Geosciences Node [Đã kiểm]. Cube MTRDR thật chỉ là mục tiêu mở rộng.

| Nhóm | Descriptor (công thức giống hệt hai phía) | Trái Đất | Moon | Mars | Ghi chú trung thực |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Terrain | Phân bố dốc ở baseline L: p50, p90, tỷ lệ diện tích >8°, >15°, >20° | Copernicus GLO-30 | LOLA LDEM cực 20 m; PGDA 78 (5 m) gộp về 30 m | MOLA 463 m hoặc blend HRSC–MOLA 200 m; Earth gộp về cùng L | Góc dốc là đại lượng không thứ nguyên, không phụ thuộc trọng lực |
| Terrain | Phổ nhám đa tỷ lệ: độ lệch RMS ν(L) tại L, 2L, 4L, 8L, 16L; **số mũ Hurst H** = độ dốc log ν–log L | như trên | như trên | như trên | H là chữ ký của quá trình tạo bề mặt (Rosenburg 2011 cho Moon; Kreslavsky & Head 2000 cho Mars) [Nhớ]; ít nhạy với khác biệt độ phân giải hơn TRI |
| Terrain | Tỷ lệ diện tích trong bóng khi Mặt Trời cao 2°, 5°, 7° (trung bình mọi phương vị) | tính từ DEM | tính từ DEM, đối chiếu bản đồ chiếu sáng PGDA | — | Trái Đất có ánh sáng tán xạ từ bầu trời lấp bóng → ghi vào sổ chuyển giao |
| Thiên văn | Số giờ/năm Mặt Trời ở 0–7° và độ phủ phương vị ở dải đó, giao với mặt đất trơ không tuyết | hàm của vĩ độ + MODIS snow/NDVI | hằng số của mục tiêu | — | Thuần hình học thiên thể, tính được chính xác |
| Spectral | Summary parameters CRISM dùng được trong cửa sổ khí quyển Trái Đất: nhóm Fe (BD530, SH600, BD860, BD920), mafic (OLINDEX, LCPINDEX, HCPINDEX), Al/Fe/Mg-OH (BD2210, BD2250, BD2290, D2300, BD2355), sulfate (BD2100, SINDEX, BD2265), carbonate (MIN2295_2480, MIN2345_2537) | EMIT L2A reflectance | — | MICA type spectra; mở rộng: MTRDR Jezero | Cả hai phía được nội suy về cùng lưới bước sóng trước khi tính. Tham số nào phải rút gọn vì dải 1,35–1,45 và 1,8–1,95 µm bị khí quyển Trái Đất che thì rút gọn **ở cả hai phía** |
| Spectral | Góc phổ (SAM) trên dải 2,0–2,45 µm đã loại continuum | EMIT | — | MICA | Chỉ dùng làm bằng chứng phụ trên top ứng viên |
| TIR | Chỉ số mafic/thạch anh từ phát xạ nhiệt | ASTER GED AG100 | Diviner CF (stretch) | giả định nền bazan (TES) | Vai trò chính: **loại mồi nhử giàu thạch anh** |
| Ice | Nhiệt độ đất trung bình năm, bề dày tầng hoạt động ≤1 m, chỉ số khô hạn P/PET, số chu kỳ đóng–tan băng/năm | MODIS LST, sản phẩm permafrost (Obu 2019 hoặc ESA CCI), TerraClimate/ERA5-Land | Diviner (nhiệt độ PSR), độ sâu ổn định băng | SWIM, bản đồ độ sâu băng | Nhiệt độ tuyệt đối không khớp được; so **cấu hình** (băng dưới lớp phủ khô) và tỷ số độ sâu băng / độ sâu thấm nhiệt |
| Mặt nạ | Đất trơ: NDVI thấp, không nước, không đô thị/canh tác | MODIS NDVI, ESA WorldCover | — | — | Cổng nhị phân, không tham gia điểm |

**Giới hạn phải nói thẳng trên slide:** dải hydrat hóa 1,4 / 1,9 / 3 µm — nơi CRISM mạnh nhất — bị hơi nước khí quyển Trái Đất che. Đó là giới hạn *quan sát*, không phải của địa điểm. EMIT cũng chỉ phủ khoảng ±52° vĩ độ (quỹ đạo ISS) [Nhớ], nên lens phổ không áp dụng cho vùng cực.

#### (3) Fidelity engine — mượn nguyên khung "climate analog" của khoa học khí hậu

Bài toán "nơi nào hôm nay có khí hậu giống thành phố X năm 2080" đã có lời giải thống kê chín muồi: **sigma dissimilarity** (Mahony và cs. 2017) và khái niệm **no-analog / novel climate** (Williams & Jackson 2007) [Nhớ]. Áp nguyên xi:

- Với lens ℓ có K descriptor, mục tiêu có vector **t**, ô Trái Đất có vector **e**.
- Hiệp phương sai **Σ** ước lượng từ *quần thể footprint trên chính thiên thể đích* (ví dụ 9 vùng ứng viên Artemis III + N footprint ngẫu nhiên quanh cực; N footprint trên các bãi đáp ứng viên Sao Hỏa). Ý nghĩa: đo khoảng cách bằng đơn vị "biến thiên tự nhiên giữa các địa điểm trên thiên thể đó".
- d² = (**e** − **t**)ᵀ Σ⁻¹ (**e** − **t**); đổi d qua phân bố χ bậc K thành **σ tương đương**. Nếu Σ kém điều kiện: PCA rồi cắt, hoặc lùi về dạng đường chéo.
- **Fidelity** hiển thị dạng σ và dạng phần trăm (1 − CDFχ).
- **Yếu tố giới hạn** = descriptor có độ lệch chuẩn hóa lớn nhất (ý tưởng MESS của Elith và cs. 2010 trong mô hình hóa phân bố loài) → mỗi kết quả tự giải thích "khớp vì đâu, lệch vì đâu".
- **No-analog flag:** nếu ô Trái Đất tốt nhất vẫn >2σ, mục tiêu đó không có analog tự nhiên cho lens này → khuyến nghị buồng thử/mô phỏng. Đây là Delta-Limit phía dữ liệu.
- **Không cộng gộp giữa các lens.** Mỗi địa điểm có hồ sơ lens (radar chart), tránh đúng sai lầm số 6 trong ABOUT.md.

Chi phí tính toán: số học trên bảng vài trăm nghìn dòng, chạy trong vài giây bằng NumPy.

#### (4) Transfer Ledger — Delta-Limit có số

Mỗi lens có một bảng cố định, soạn từ vật lý, hiển thị trên mọi Test Card:

| Đại lượng | Trái Đất | Moon | Mars | Hệ quả cho phép thử |
| :--- | :--- | :--- | :--- | :--- |
| Trọng lực | 9,81 m/s² | 1,62 (0,165 g) | 3,71 (0,378 g) | Hình học dốc chuyển giao tốt; **độ lún bánh xe, lực kéo, quỹ đạo hạt bụi không chuyển giao** → hệ treo giảm trọng lực, bay parabol. Góc nghỉ thay đổi nhẹ theo g (Kleinhans 2011) [Nhớ] |
| Áp suất | 101 kPa | ~chân không | ~0,6 kPa | Tản nhiệt đối lưu, hành vi bụi, thăng hoa băng không chuyển giao → buồng nhiệt–chân không có bụi |
| Chu kỳ ngày | 24 h | 29,5 ngày | 24,66 h | Ứng suất nhiệt và sống sót qua đêm Mặt Trăng không có analog thực địa |
| Liều bức xạ bề mặt | ~2,4 mSv/năm | ~1,37 mSv/ngày (Chang'e-4 LND) | ~0,67 mSv/ngày (MSL RAD) | Không chuyển giao [Nhớ các con số; kiểm lại trước khi đưa lên slide] |
| Nhiệt độ | — | PSR <110 K | trung bình ~210 K ở vĩ độ trung bình | Băng Trái Đất gần điểm nóng chảy; băng PSR là băng lạnh sâu, cơ tính khác hẳn |
| Ánh sáng tán xạ | có bầu trời | không | ít | Bóng Trái Đất không đen tuyệt đối → thử cảm biến quang học chỉ chuyển giao một phần |
| Vật liệu | phong hóa hóa học, hạt tròn | hạt sắc cạnh, tích điện, agglutinate | perchlorate, bụi mịn | Mài mòn và bám dính không chuyển giao → dùng simulant |

Điểm quan trọng: hai trục **Fidelity (từ dữ liệu)** và **Irreproducible physics (từ bảng này)** được trình bày tách nhau, không nhân thành một con số. Nhân vào sẽ tạo ra hệ số chủ quan mà giám khảo chuyên môn bắt lỗi ngay.

Liên kết Impact: sổ này nối thẳng tới danh mục *architecture-driven technology gaps* của NASA Moon to Mars (ví dụ gap #0301 "Systems to Survive and Operate through Extended Periods of Lunar Shadow", các gap về thu hồi nước từ regolith/băng và tách kim loại từ regolith) [Đã kiểm sự tồn tại và tên các gap này; **chưa đọc được bảng xếp hạng đầy đủ**]. Câu chốt: *"Gap #0301 has no field analog on Earth — our engine says so with a number."*

#### (5) Validation harness — nơi thắng điểm Validity

| Phép kiểm | Thiết kế | Kết quả kỳ vọng [Giả thuyết] |
| :--- | :--- | :--- |
| **Đối chứng dương** | Các cặp NASA đã xác nhận phải xếp cao **trên đúng lens**: Lake Salda ↔ Jezero (M1); Pilot Valley ↔ Mars (M1/muối); lava field California/Kilauea ↔ địa hình Moon (L1); Haughton/Devon Island (L1, L2); Mistastin — hố va chạm trong anorthosite, nơi phi hành đoàn Artemis II huấn luyện [Nhớ] (L3) | Percentile ≥90 trong toàn bộ ô đất trơ |
| **Mồi nhử thị giác** | Nơi trông giống nhưng vật lý khác: **Wadi Rum** (bối cảnh quay phim *The Martian*; sa thạch thạch anh) và cát đỏ thạch anh nội địa Úc cho M1 | Điểm cao ở baseline RGB, điểm thấp ở lens khoáng vật. Slide: *"Hollywood's Mars fails the mineral test."* |
| **Phân bố null** | Fidelity của toàn bộ ô đất trơ → báo cáo ứng viên theo percentile ("top 0,1% trong N ô") | Chống diễn giải thừa các con số tuyệt đối |
| **Ablation** | Cùng bài truy hồi cặp chuẩn, so ba bộ đặc trưng: (a) RGB/texture, (b) embedding nền tảng, (c) twin-formula | (c) đạt recall@k và thứ hạng trung bình tốt nhất; (a) bị mồi nhử đánh lừa |
| **Độ nhạy** | Lắc ngưỡng mặt nạ, đổi baseline L, bỏ từng descriptor | Top-10 ổn định |

Nếu một kỳ vọng không xảy ra: **báo cáo đúng như vậy**. Một kết quả âm được trình bày trung thực vẫn ghi điểm Validity; một kết quả đẹp không tái lập được thì không.

Hai phát hiện phụ đáng thử, chỉ đưa lên slide nếu số liệu ủng hộ [Giả thuyết]:
- **"Analog of the wrong Moon":** gần như mọi analog Mặt Trăng kinh điển là bazan (giống biển mare thời Apollo), trong khi Moon Base nằm trên cao nguyên feldspathic. Trên lens L3, Hawaii/Iceland nên xếp thấp hơn các khối anorthosite. Phải nói cẩn trọng: điều này chỉ đúng với lens hóa học nguyên liệu, không phủ nhận giá trị vận hành của các điểm bazan.
- **Devon Island:** phương pháp texture ảnh xếp nó kém nhất; lens L1/L2 của ta nên xếp nó cao.

#### (6) Discovery — để dữ liệu tìm ra, không phải người (hay AI) chỉ định

Phễu ba tầng của ABOUT.md được giữ lại, bổ sung ba thứ:

1. **Lưới ứng viên toàn cầu** trên đất trơ, tầng thô 5–10 km bằng các lớp rẻ (LST, NDVI, khô hạn, ASTER GED, permafrost), rồi tầng mịn (DEM 30 m, EMIT) chỉ trên vài trăm ô đứng đầu mỗi lens.
2. **Analog Attention Index** (mượn từ trắc lượng thư mục): số công trình khớp truy vấn `"<tên địa điểm>" + (analog|analogue) + (Mars|Moon|lunar|planetary)` trên OpenAlex/NASA ADS. "Hidden" được định nghĩa bằng số: **fidelity percentile cao và attention thấp**. Cộng với vùng đệm loại trừ quanh bốn điểm kinh điển và các điểm trong NASA Analog Explorer.
3. **Chỉ số tiếp cận**: thời gian di chuyển tới đô thị gần nhất (lớp Oxford MAP trên GEE), cờ khu bảo tồn (WDPA), ghi chú an ninh thủ công. Một analog hoàn hảo mà không đoàn thực địa nào tới được thì giá trị thấp; hầu như không đội nào tính đến điều này.

Tùy chọn tăng tốc: dùng **Satellite Embedding (AlphaEarth Foundations, `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, 64 chiều)** [Đã kiểm] làm bộ sinh ứng viên kiểu "tìm thêm nơi giống các analog NASA đã xác nhận", rồi **bắt buộc qua kiểm chứng twin-formula**. Embedding chỉ đề cử, vật lý mới phán quyết — và chính nó là nhánh (b) trong ablation.

#### (7) Đầu ra: Analog Test Card

Mỗi ứng viên có một phiếu, tiêu đề đặt theo **quá trình** chứ không theo địa danh ("Where olivine is turning into carbonate today — Semail, Oman"):

- Hồ sơ fidelity theo lens (σ và percentile) + yếu tố giới hạn.
- Quá trình đang vận hành và tốc độ/tần suất đo được (chu kỳ đóng–tan/năm, tỷ lệ thời gian gió vượt ngưỡng, tổ hợp khoáng biến đổi).
- "Test here": thiết bị/quy trình cụ thể và gap kiến trúc NASA tương ứng.
- "Cannot test here": trích từ Transfer Ledger + cơ sở bổ sung (buồng nhiệt–chân không, hệ treo giảm trọng lực, bay parabol, bể regolith simulant).
- Attention Index, chỉ số tiếp cận, nguồn dữ liệu.

Hai chế độ xem bổ sung, chi phí thấp vì dùng lại ma trận fidelity:
- **Near-me:** "bãi thử đạt chuẩn gần trường/viện của bạn nhất". Đây là lập luận Impact mạnh nhất cho cộng đồng toàn cầu: các nhóm ở quốc gia không có điều kiện tới Hawaii hay Iceland vẫn tìm được nơi thử hợp lệ trong khu vực.
- **Coverage/Gap:** với mỗi mục tiêu, σ của analog tốt nhất theo từng lens → bảng "đã phủ / no-analog".

### 2.3. Ranh giới module và trách nhiệm

| Module | Vào | Ra | Người | Công nghệ |
| :--- | :--- | :--- | :--- | :--- |
| A. Target Profiler | DEM LOLA/PGDA, MOLA/HRSC, MICA, SWIM, Diviner | `targets.parquet` | P1 Planetary Lead | Python, rasterio, JMARS để lấy mẫu nhanh theo ROI |
| B. Earth Profiler | Tập dữ liệu GEE + EMIT | `earth_cells.parquet` | P2 EO/GEE | GEE Python API, export theo lô |
| C. Descriptor lib | raster/phổ | hàm thuần, **dùng chung cho A và B** | P3 | NumPy; một file, có unit test với mặt phẳng nghiêng và fractal tổng hợp |
| D. Fidelity + E. Validation | hai bảng trên | `fidelity.parquet`, `validation_report.md`, hình | P3 Engine | NumPy/SciPy |
| F. Discovery | fidelity + OpenAlex + accessibility | `candidates.geojson` | P5 (hoặc P1 nếu đội 4 người) | script nhỏ |
| G. Web + Test Card | GeoJSON tĩnh | site tĩnh | P4 Frontend | MapLibre/Leaflet, WMTS Moon/Mars Trek, GitHub Pages |
| H. Story & Compliance | mọi thứ | 7 slides, Project page, khai báo SI | P5 | — |

Quy tắc giao diện: **module C là nguồn duy nhất của mọi công thức**. A và B không được tự viết lại công thức; đó là thứ bảo đảm khẳng định "same formula, both worlds" đúng theo nghĩa đen và kiểm tra được trong repo.

### 2.4. Schema dữ liệu chính

```yaml
# lenses.yaml
- id: M1_aqueous
  body: mars
  footprint_km: 5
  baseline: {type: spectral_grid_nm, value: 10}
  descriptors: [BD530, BD920, OLINDEX_r, BD2210, BD2290, D2300, MIN2295_2480, SINDEX, ...]
  gates: {ndvi_max: 0.15, emit_coverage: true}
  targets: [jezero_margin, oxia_planum, meridiani]
  ledger: ledger/mars_surface.yaml
```

```jsonc
// candidates.geojson — properties của một Feature
{
  "id": "E-0421", "name": "…", "lat": 0, "lon": 0, "footprint_km": 5,
  "process_title": "Where olivine is turning into carbonate",
  "lens_scores": {
    "M1_aqueous": {"target": "jezero_margin", "sigma": 0.8, "percentile": 99.7,
                   "limiting_factor": "MIN2345_2537", "descriptors": {"...": 0.0}}
  },
  "process_rates": {"freeze_thaw_cycles_per_yr": null, "wind_exceedance_frac": null},
  "test_here": [{"tech": "…", "nasa_gap": "…"}],
  "cannot_test": ["gravity 0.378 g", "pressure 0.6 kPa", "…"],
  "attention": {"n_pubs": 3, "query": "…", "source": "OpenAlex", "date": "2026-11-14"},
  "access": {"travel_time_h": 2.5, "protected_area": false, "note": "…"},
  "evidence_status": "engine-confirmed | literature-only | hypothesis",
  "data_sources": ["NASA EMIT L2A", "…"]
}
```

`evidence_status` là trường bắt buộc: không ứng viên nào lên slide với trạng thái `hypothesis`.

### 2.5. Hidden Analogs đề xuất

**Cách dùng danh sách này:** đây là **giả thuyết để kiểm tra phễu và làm hạt giống**, không phải kết quả. Analog chỉ được công bố khi engine xác nhận. Nếu engine đưa ra nơi khác tốt hơn, đi theo engine. Cột "Mức mới" là đánh giá sơ bộ, phải thay bằng Attention Index.

| # | Địa điểm | Cho | Lens | Lý giải khoa học | Mức mới | Rủi ro / điểm yếu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Harrat Khaybar / Harrat Rahat, Ả Rập Xê Út** — cánh đồng bazan siêu khô hạn, có ống dung nham Umm Jirsan dài 1.481 m [Đã kiểm] | Moon + Mars | L1, hang động, nền mafic cho M1 | Bazan trơ hoàn toàn, không thực vật che phổ như Hawaii; trời quang nên EMIT sạch; có đường bộ. Ống dung nham đã được chứng minh là nơi con người trú ẩn hàng nghìn năm | Cao: tra cứu chỉ thấy khảo cổ, **không thấy công trình nào coi đây là analog hành tinh** | Bazan = analog mare, không phải cao nguyên Cực Nam |
| 2 | **Ophiolite Semail, Oman** | Mars | M1 ↔ Jezero / Nili Fossae | Peridotit lộ trần đang serpentin hóa và carbonat hóa: cùng tổ hợp olivine–serpentine–Mg-carbonate mà CRISM thấy ở Jezero; suối kiềm, sinh H₂/CH₄ | Trung bình: nổi tiếng trong địa hóa, vắng mặt trong NASA Analog Explorer | Kỳ vọng là "neo khám phá" dễ thành công nhất của lens phổ |
| 3 | **Matanomadh, Kutch, Ấn Độ** | Mars | M1 ↔ Meridiani / Mawrth | Jarosite và natrojarosite trong bazan Deccan phong hóa — chỉ thị môi trường axit, oxy hóa, ít nước (JGR Planets 2016; American Mineralogist 2025; nhóm SAC-ISRO) [Đã kiểm] | Trung bình: có công bố của ISRO, ít được biết ngoài Ấn Độ | Jarosite dạng mạch nhỏ, có thể dưới ngưỡng pixel 60 m. Báo chí từng thổi phồng "nơi duy nhất" — không dùng lại câu đó |
| 4 | **Karakul, Đông Pamir, Tajikistan** — cấu trúc được diễn giải là hố va chạm ~45–52 km, cao ~3.900 m [Đã kiểm] | Mars | X1 + hố có hồ muối | Hố va chạm + hồ muối + khí hậu lạnh rất khô + UV cao trong cùng một footprint: tổ hợp gần với hồ hố va chạm Sao Hỏa | Cao: **không tìm thấy văn liệu analog** | Nguồn gốc va chạm là diễn giải; lượng mưa và permafrost phải lấy từ dữ liệu, chưa kiểm |
| 5 | **Cao nguyên lạnh siêu khô Đông Pamir – Tây Côn Lôn – Changtang** | Mars (+ Moon) | X1 ↔ Arcadia | Permafrost khô, sông băng phủ đá vụn, băng nông dưới lớp phủ khô ở nơi mưa rất ít — cấu hình gần lobate debris apron và băng nông vĩ độ trung bình | Cao | Khả năng tiếp cận; đây là vùng nên để phễu tự khoanh |
| 6 | **Peary Land (Bắc Greenland) và các hoang mạc cực >80°N** | Moon | L2 | Chỉ ở vĩ độ rất cao Mặt Trời mới đi vòng quanh chân trời ở độ cao thấp suốt 24 giờ — đúng hình học chiếu sáng Cực Nam Mặt Trăng; nền đất trơ, ít tuyết, có permafrost | Cao cho mục đích này; Devon Island (75°N) là đối chứng dương | Mùa Mặt Trời thấp trùng mùa có tuyết → phải giao với lớp tuyết MODIS; hậu cần cực khó. Nam Cực cho kết quả tương tự nhưng thuộc nhóm đã bão hòa |
| 7 | **Hố va chạm nguyên vẹn trong sa mạc: Tenoumer (Mauritania, 1,9 km), Roter Kamm (Namibia, 2,5 km), Wolfe Creek (Úc), Kamil (Ai Cập, 45 m, <5.000 năm, còn tia ejecta)** | Moon + Mars | L1 | Sa mạc bảo tồn vành và ejecta; Kamil là hố duy nhất trên Trái Đất còn tia ejecta kiểu thiên thể không khí quyển [Đã kiểm] — đúng tỷ lệ một chuyến EVA | Trung bình–cao | **Kamil nhỏ hơn 2 pixel DEM 30 m: engine không đo được**, chỉ là analog theo văn liệu. Roter Kamm bị cát lấp một phần |
| 8 | **Khối anorthosite lộ trần: Fiskenæsset (Tây Greenland), Sittampundi (Tamil Nadu)** | Moon | L3 | Regolith Cực Nam là feldspathic; đây là nguồn nguyên liệu ISRU tương ứng. Sittampundi được cho là nguồn simulant của ISRO cho Chandrayaan [Nhớ, **tra cứu trong phiên không xác nhận được**] | Cao với vai trò analog thực địa | Plagioclase gần như không có dấu phổ ở VSWIR → phải dùng TIR; Sittampundi nhiều thực vật |
| 9 | **Hang băng trong ống dung nham ở nơi nhiệt độ trung bình năm >0 °C** (ví dụ các hang băng Teide, Etna, Phú Sĩ, El Malpais) | Moon | X1 (quá trình) | Băng tồn tại nhờ bẫy lạnh do địa hình — cùng nguyên lý ổn định nhiệt do che chắn như PSR, khác cơ chế truyền nhiệt | Cao về cách đóng khung | Dưới ngưỡng viễn thám: **engine không xác nhận được**, chỉ ghi nhận là analog quá trình theo văn liệu. Tên hang cụ thể cần kiểm chứng |
| 10 | **Sa mạc Lut, Iran** (mega-yardang) | Mars | M2 ↔ Medusae Fossae | NASA đã nêu Lut làm so sánh cho yardang Sao Hỏa [Đã kiểm]; gió đổi hướng theo mùa, gần như không thực vật | Trung bình | Lens stretch; tiếp cận khó. Qaidam là đối chứng dương (đã có nhiều công bố) |
| 11 | **Emi Koussi, Tibesti, Chad** | Mars | hình thái núi lửa khiên | Từng được so với Elysium Mons [Nhớ] | Trung bình | Gần như không tiếp cận được → dùng làm **ví dụ minh họa cho chỉ số tiếp cận** |

Kỳ vọng thực tế cho slide 5: 2 analog Mars (một từ M1, một từ X1) + 1–2 analog Moon (L1/L2), tất cả `engine-confirmed`.

### 2.6. Ánh xạ sang 5 tiêu chí chấm

| Tiêu chí | Bằng chứng cụ thể | Nằm ở đâu |
| :--- | :--- | :--- |
| **Impact** | Test Card nối địa điểm → thiết bị → technology gap của NASA; chế độ Near-me cho mọi quốc gia; trả lời đúng nhu cầu mà USGS đang khảo sát; mục tiêu gồm cả bãi đáp ESA (Oxia Planum) | Slide 6, web |
| **Creativity** | Luật đồng dạng thay cho tương đồng; khung climate-analog/no-analog chuyển sang hành tinh học; chạy công thức CRISM trên EMIT; chỉ số "Mặt Trời vòng quanh chân trời"; Attention Index định lượng hóa chữ "hidden" | Slide 3, 5 |
| **Validity** | Đối chứng dương + mồi nhử + null + ablation; quy tắc baseline chung; Transfer Ledger có số; nêu rõ dải phổ bị che và vùng EMIT không phủ; trạng thái bằng chứng trên từng ứng viên | Slide 4, `validation_report.md` |
| **Relevance** | Hai thiên thể, bốn lens, mục tiêu là vị trí Moon Base thật và bãi đáp thật; dữ liệu NASA ở cả hai phía; web tĩnh chạy được | Slide 3, 6 |
| **Presentation** | Một ẩn dụ (hầm gió), một cú móc (Hollywood's Mars), một sản phẩm (Test Card) | Toàn bộ |

**Dàn 7 slide đề xuất:** (1) Tên + hook hầm gió. (2) Vấn đề: bẫy thị giác, kèm ví dụ Devon Island bị phương pháp ảnh xếp chót. (3) Phương pháp: same formula, both worlds; bốn lens; sơ đồ dữ liệu NASA. (4) Validation: bảng đối chứng dương, mồi nhử Wadi Rum, ablation. (5) Khám phá: 3–4 hidden analog với σ, percentile, Attention Index. (6) Test Card + Transfer Ledger + Near-me + QR. (7) Dữ liệu, giấy phép, khai báo SI, giới hạn.

---

## 3. Phương án đã loại

| Phương án | Innovation Point | Lý do loại |
| :--- | :--- | :--- |
| **B. Analog Gap Atlas / Portfolio** — tối ưu hóa phủ tập: chọn bộ địa điểm Trái Đất tối thiểu phủ hết không gian đặc trưng của các mục tiêu (mượn từ quy hoạch bảo tồn) | Đảo câu hỏi: "phần nào của Moon/Mars *chưa* có analog?" | Cần ma trận fidelity đầy đủ trước, tức phụ thuộc toàn bộ phương án A. Làm sản phẩm chính thì trừu tượng, khó demo. **Giữ lại dạng rút gọn** là chế độ Coverage/Gap, gần như miễn phí khi A xong |
| **C. Tìm kiếm bằng foundation model** (AlphaEarth embeddings, Prithvi) xuyên hành tinh | Hiệu ứng "AI" mạnh, làm nhanh | Chính là "AI + dữ liệu NASA" mà số đông sẽ làm; hộp đen; không có embedding chung Earth–Mars đã kiểm chứng; rơi lại vào tương đồng thị giác. **Giữ lại** làm bộ sinh ứng viên tùy chọn và nhánh so sánh trong ablation |
| **D. Process Time-Machine** — chữ ký quá trình từ chuỗi thời gian (dịch chuyển cồn cát bằng optical flow, trồi sụt đóng–tan bằng InSAR/NISAR) | Đo trực tiếp "quá trình" | Xử lý SAR và chuỗi ảnh không khả thi trong 48 giờ; phía Sao Hỏa thiếu dữ liệu tương ứng sẵn dùng. Chỉ giữ các tốc độ quá trình rẻ (chu kỳ đóng–tan, tần suất gió) |
| **E. Khung gốc ABOUT.md** (TRI + cosine phổ trên cube CRISM) | Đã định lượng | Không loại mà **được thay thế**: TRI khác độ phân giải không so được; xử lý cube CRISM thô quá nặng; điểm tổng dễ mắc sai lầm số 6; Delta-Limit mới ở dạng mô tả |
| **F. Chatbot/RAG trên văn liệu analog** | Dễ dùng | Không có tính toán trên dữ liệu vệ tinh; đúng kiểu ABOUT.md cảnh báo; rủi ro bịa |
| **G. Game / mô phỏng chiến dịch thực địa** | Giáo dục, lan tỏa | Yếu ở Validity; tốn công dựng nội dung. Có thể làm lớp trình bày sau nếu vào chung kết |
| **H. Lưới toàn cầu đầy đủ ở 30 m cho mọi lens** | Khám phá "thật" nhất | Thời gian export GEE không kiểm soát được trong 48 giờ; phễu hai tầng cho kết quả tương đương với chi phí nhỏ hơn nhiều |

---

## 4. Giả định / rủi ro cần kiểm chứng trước khi code

| Giả định | Mức rủi ro | Cách kiểm chứng rẻ nhất |
| :--- | :--- | :--- |
| **R0. Tuân thủ SI:** bản thiết kế này do AI hỗ trợ soạn, trong khi tóm tắt địa phương ghi không dùng SI để nghĩ ý tưởng cốt lõi | **Cao — có thể mất tư cách xét giải** | Đọc nguyên văn Project Submission Guide và FAQ ngay (15 phút). Hỏi Local Lead nếu câu chữ mơ hồ. Đội tự quyết định ý tưởng nào là của mình, chỉnh sửa, và khai báo trung thực cách dùng SI. Không được khai sai |
| R1. Trang đề, tab Resources, giới hạn 7 slide / 30 s đúng như ABOUT.md | Trung bình | Mở trang đề bằng trình duyệt; đối chiếu 12 Considerations và danh sách tài nguyên với mục 2.2 |
| R2. Công thức CRISM chạy trên EMIT phân biệt được khoáng vật thật (carbonate, smectite, olivine) dù mất dải 1,4/1,9 µm | **Cao — quyết định lens trung tâm** | Phép thử 2 giờ: tải MICA (3 MB); lấy EMIT tại Lake Salda (đối chứng dương), một điểm peridotit Oman, và Wadi Rum (mồi nhử); tính ~10 tham số. Đạt nếu Salda và Oman tách khỏi Wadi Rum và gần phổ MICA carbonate/olivine hơn. Trượt → lùi về sản phẩm khoáng vật EMIT L2B (tải từ LP DAAC, **không có trên GEE** [Đã kiểm]) hoặc chỉ số SWIR Sentinel-2 + ASTER GED |
| R3. Có cảnh EMIT không mây tại các điểm cần, trong ±52° vĩ độ | Trung bình | Truy vấn `earthaccess`/CMR theo bbox cho 6–8 điểm ngay giờ đầu. Kiểm tra ID tập dữ liệu trên GEE (ABOUT.md ghi `NASA/EMIT/L2A_RFL`; có thể là `NASA/EMIT/L2A/RFL`) |
| R4. DEM cực Mặt Trăng tải và đọc được nhanh; gộp 5 m → 30 m cho thống kê ổn định | Trung bình | Tải một tile PGDA 78 quanh Connecting Ridge, tính dốc ở 30 m, so với bản đồ dốc PGDA có sẵn. Trượt → dùng thẳng sản phẩm dốc/chiếu sáng dựng sẵn của PGDA |
| R5. Descriptor địa hình ở baseline chung thực sự tách được địa điểm (không phải nơi nào cũng "khá giống") | Trung bình | Tính cho 1 mục tiêu Moon + 5 nơi trên Trái Đất (2 đối chứng dương, 3 ngẫu nhiên). Nếu σ không tách → thêm phổ nhám đa tỷ lệ, hoặc thu hẹp footprint |
| R6. Ước lượng Σ từ quần thể footprint đủ ổn định (ít mẫu, nhiều chiều) | Trung bình | Bắt đầu bằng dạng đường chéo; chỉ dùng Mahalanobis đầy đủ khi số footprint ≥ 5× số descriptor |
| R7. Export GEE cho tầng thô toàn cầu xong trong vài giờ | Trung bình | Khởi chạy ngay giờ đầu ở 10 km; song song chuẩn bị danh sách hạt giống ~150 footprint (hố va chạm, trường núi lửa Holocene, playa, khối anorthosite) làm đường lùi |
| R8. Dữ liệu băng: SWIM tải được dạng raster; có sản phẩm permafrost dùng ngay | Trung bình | Mở tab Products của swim.psi.edu; tìm bản đồ Obu 2019 hoặc ESA CCI. Trượt → X1 rút thành lens mô tả dựa trên LST + khô hạn, nói rõ là bán định lượng |
| R9. Đối chứng dương có đủ số lượng để ablation có ý nghĩa | Thấp–trung bình | Lập danh sách ≥10 cặp từ NASA Analog Explorer + văn liệu ngay từ đầu; nếu <10, trình bày là nghiên cứu tình huống, không tuyên bố thống kê |
| R10. Các con số trong Transfer Ledger và các mục [Nhớ] | Thấp | P1 tra lại từng con số với nguồn gốc trước Data Freeze; mục nào không tra được thì bỏ |
| R11. Thông tin Moon Base (Shackleton rim / Connecting Ridge) | Thấp–trung bình | Đọc trực tiếp *Moon Base Architecture User's Guide* trên nasa.gov |
| R12. WMTS của Moon/Mars Trek hoạt động từ trang tĩnh (CORS, phép chiếu cực) | Trung bình | P4 dựng trang thử 30 phút. Trượt → dùng ảnh nền tĩnh cho các mục tiêu đã khóa |
| R13. OpenAlex trả số lượng công trình hợp lý cho tên địa điểm | Thấp | Thử 5 tên: Atacama (phải rất cao), Harrat Khaybar (phải rất thấp) |

---

## 5. Thứ tự triển khai cấp cao

Phân vai: **P1** Planetary (mục tiêu, ledger, kiểm chứng số liệu) · **P2** EO/GEE · **P3** Engine + validation · **P4** Web · **P5** Story, compliance, Attention/Access (đội 4 người: P5 gộp vào P1 và P4).

| Mốc (UTC+7) | Việc | Điều kiện qua cổng / đường lùi |
| :--- | :--- | :--- |
| **Ngay → 12:30, 14/11** | Cả đội: xử lý **R0, R1**. Khóa danh sách mục tiêu (2 Moon, 3 Mars). Tạo repo công khai Apache 2.0, trang Project nháp | Nếu R0 không cho phép: đội tự định hình lại ý tưởng của mình trước khi làm tiếp |
| **12:30 → 15:30** | Ba phép thử song song: P2+P3 làm **R2/R3** (phổ); P1 làm **R4/R5** (địa hình Moon); P2 khởi chạy export tầng thô **R7**; P4 làm **R12**; P5 lập danh sách đối chứng và mồi nhử **R9** | **Cổng G1 lúc 15:30:** chốt tập lens. Phổ trượt → M1 dùng đường lùi. Băng trượt → X1 rút gọn. Không thêm lens mới sau G1 |
| **15:30 → 21:00** | P3 hoàn thiện module C (thư viện descriptor dùng chung) + unit test. P1 xuất `targets.parquet`. P2 xuất tầng thô, chọn vài trăm ô đứng đầu mỗi lens | Module C phải xong trước khi A, B tính hàng loạt |
| **21:00 → 03:00, 15/11** | Tầng mịn (DEM 30 m, EMIT) trên ô đã chọn. P3 chạy fidelity + toàn bộ validation harness. P5 tính Attention Index và chỉ số tiếp cận | **Data Freeze 03:00.** Ứng viên nào chưa `engine-confirmed` thì không lên slide |
| **03:00 → 09:00** | Chia ca ngủ. P4 dựng web từ GeoJSON đóng băng: bản đồ, chọn lens, Test Card. P3 viết `validation_report.md` và xuất hình | Web tối thiểu: bản đồ + Test Card. Near-me và Coverage là phần thêm |
| **09:00 → 15:00** | P4: Near-me, Coverage/Gap, so sánh cạnh nhau với nền Moon/Mars Trek. P1: rà Transfer Ledger, liên kết gap NASA. P5: bản nháp 7 slide | **Code Freeze 15:00.** README, giấy phép, trích dẫn dữ liệu đầy đủ |
| **15:00 → 21:00** | Hoàn thiện slide tiếng Anh, trang Project, khai báo SI, kiểm tra mọi link ở cửa sổ ẩn danh, rà quy định người dưới 18 tuổi. **Nộp trước 21:00** | Ba giờ đệm trước hạn 23:59 |

**Thứ tự cắt bỏ khi thiếu thời gian (cắt từ trên xuống):** lens stretch M2/L3 → embedding và nhánh ablation (b) → Coverage/Gap → Near-me → X1 đầy đủ (giữ bản rút gọn). **Không bao giờ cắt:** validation harness, Transfer Ledger, trạng thái bằng chứng.

**Sản phẩm tối thiểu vẫn đủ sức cạnh tranh:** L1+L2 (Moon) và M1 (Mars), mỗi lens có đối chứng dương, một mồi nhử, và ít nhất một hidden analog được engine xác nhận, trên web tĩnh có Test Card.

---

## Phụ lục: Kho ý tưởng sáng tạo bổ sung

**Thụ phấn chéo từ ngành khác (đã dùng ✔ / để dành ○):**

| Ngành | Ý tưởng | Áp dụng |
| :--- | :--- | :--- |
| Kỹ thuật hàng không / cơ lưu chất | Luật đồng dạng, Buckingham π | ✔ khung tư duy chính |
| Khoa học khí hậu | Climate analog, sigma dissimilarity, no-analog climate | ✔ fidelity engine |
| Sinh thái học | MESS (yếu tố giới hạn); mô hình ổ sinh thái: coi bãi đáp là "loài", chiếu "ổ sinh thái" của nó lên Trái Đất | ✔ MESS; ○ MaxEnt |
| Quy hoạch bảo tồn | Tính bổ sung, phủ tập (Marxan) | ○ chế độ portfolio |
| Trắc lượng thư mục | Chỉ số chú ý / bị bỏ quên | ✔ Attention Index |
| Khoa học vật liệu | Biểu đồ Ashby: vẽ địa điểm trong không gian hai tính chất với "vùng bao" của mục tiêu | ○ một hình rất đẹp cho slide 5 nếu còn thời gian |
| Phân tích địa hình quân sự | Bản đồ go/no-go, NATO Reference Mobility Model, cone index | ○ lens cơ động chi tiết |
| Tin sinh học | Căn chỉnh chuỗi: so *hồ sơ lộ trình* (độ cao/dốc dọc tuyến LTV dự kiến) bằng dynamic time warping; phân biệt "tương đồng" (cùng nguồn gốc quá trình) và "tương tự" (chỉ giống hình dạng) | ○ câu chữ kể chuyện: "process twins, not look-alikes" |
| Dược học | Phễu sàng lọc ảo; tái định vị thuốc | ✔ phễu ba tầng |
| Y học lâm sàng | Giá trị ngoại suy của thử nghiệm | ✔ Transfer Ledger |
| Khảo cổ học | Mô hình dự báo vị trí di chỉ; ống dung nham là nơi trú ẩn đã được "kiểm chứng" bởi con người hàng nghìn năm (Umm Jirsan) | ○ chi tiết kể chuyện |
| Thị giác máy tính | Embedding tự giám sát, tìm kiếm tương tự | ✔ chỉ làm bộ đề cử |

**Ý tưởng để dành:**

1. **Cầu nối TIR cho Mặt Trăng:** Diviner Christiansen Feature ↔ phát xạ ASTER/ECOSTRESS, là bản sao của cầu EMIT↔CRISM cho phía Moon. Khoa học vững nhưng cần hiệu chỉnh hiệu ứng chân không.
2. **Quán tính nhiệt ba thế giới:** TES/THEMIS (Mars) ↔ Diviner (Moon) ↔ quán tính nhiệt biểu kiến MODIS (Trái Đất), làm đại diện cho cỡ hạt và độ cố kết. Độ ẩm đất làm nhiễu phía Trái Đất, chỉ dùng được ở vùng siêu khô.
3. **Tỷ số gió/ngưỡng khởi động hạt:** tỷ lệ thời gian vận tốc ma sát vượt ngưỡng, từ ERA5 (Trái Đất) và Mars Climate Database. Là số không thứ nguyên thật cho lens M2.
4. **Analog dưới pixel:** hang băng, hố va chạm cỡ EVA, mỏ ngầm. Engine vệ tinh không thấy; cần lớp dữ liệu điểm từ văn liệu. Nêu thẳng là giới hạn tỷ lệ của phương pháp.
5. **Dữ liệu đối tác để tăng điểm Relevance:** ISRO Chandrayaan-2 (ảnh cực OHRC, radar DFSAR), JAXA Kaguya (bản đồ khoáng vật), ESA Mars Express (HRSC, OMEGA), Copernicus DEM, CSA RADARSAT.
6. **Hướng mở rộng sau hackathon:** mở Test Card thành chuẩn dữ liệu cộng đồng đóng góp, đáp đúng lời kêu gọi "cơ sở dữ liệu mở toàn cầu" của Preston và cs.; thêm thiên thể khác (Europa/Enceladus đã có trong NASA Analog Explorer).
7. **Phương án video 30 giây:** một cảnh duy nhất — ảnh Wadi Rum cạnh Sao Hỏa "trông y hệt", thanh điểm khoáng vật tụt xuống; cắt sang Oman trông không giống gì, thanh điểm vọt lên; kết bằng Test Card.

**Câu hỏi mở cho đội:**

- Điểm thi TP. HCM có thuyết trình trực tiếp không, thời lượng bao nhiêu?
- Đội có ai đọc được dữ liệu PDS/hành tinh không? Nếu không, P1 nên dùng JMARS để lấy mẫu theo ROI thay vì tự xử lý raster.
- Chọn slide hay video? Bản thiết kế này tối ưu cho slide.

**Nguồn đã tra trong phiên:**

- Foucher và cs. 2021, *Definition and use of functional analogues in planetary exploration* — https://doi.org/10.1016/j.pss.2021.105162
- NASA Analog Explorer — https://science.nasa.gov/solar-system/analog-explorer/
- Tổng quan 33 điểm analog (Int. J. Astrobiology 2013) — https://www.cambridge.org/core/product/244C9EB88B74D6905133DD2228DD3112/core-reader
- ESA, *Cataloguing otherworldly landscapes on Earth* — https://www.esa.int/Our_Activities/Preparing_for_the_Future/Discovery_and_Preparation/Cataloguing_otherworldly_landscapes_on_Earth
- USGS Terrestrial Analogs Survey (tin 08/09/2026) — https://www.natureworldnews.com/articles/73238/20260908/usgs-reopens-comment-its-survey-earth-sites-that-stand-other-planets.htm
- NHSJS 2026, xếp hạng bãi thử bằng texture ảnh — https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/
- Deep learning chọn analog ở Qaidam — https://arxiv.org/abs/2501.08584
- Moon Base Architecture User's Guide (chưa đọc được toàn văn) — https://nasa.gov/wp-content/uploads/2026/04/moon-base-architecture-users-guide.pdf
- Viviano-Beck và cs. 2014 — https://ui.adsabs.harvard.edu/abs/2014JGRE..119.1403V ; thư viện MICA — https://crismtypespectra.rsl.wustl.edu
- EMIT L2B Mineral (LP DAAC) — https://data.nasa.gov/dataset/emit-l2b-estimated-mineral-identification-and-band-depth-and-uncertainty-60-m-v001-7fe29
- Satellite Embedding trên Earth Engine — https://developers.google.com/earth-engine/tutorials/community/satellite-embedding-01-introduction
- SWIM — https://swim.psi.edu/
- Umm Jirsan — https://www.livescience.com/archaeology/humans-were-living-in-a-lava-tube-7000-years-ago-on-the-arabian-peninsula
- Kamil Crater — https://staff.polito.it/amelia.sparavigna/kamilcrater.htm
- Natrojarosite Matanomadh — https://cosmochemistry-papers.com/2025/10/10/natrojarosite-formed-in-the-matanomadh-formation-kutch-india-a-na-analog-of-jarosite-on-mars/
- Karakul — https://earthobservatory.nasa.gov/images/4537/kara-kul-structure-tajikistan
- Yardang Medusae Fossae và Lut — https://science.nasa.gov/photojournal/pj-medusae-fossae-formation-2/
- Technology gaps Moon to Mars — https://www.nasa.gov/wp-content/uploads/2024/12/2024-architecture-executive-overview.pdf
