# ARCHITECTURAL REVIEW & VISION ELEVATION (CHECKPOINT G1)

> Soạn 14/11/2026 ~16:45 (UTC+7), Fable 5.2 (Solution Architect). Đọc cùng `DESIGN.md`; chỗ nào hai tài liệu mâu thuẫn thì bản này thay thế.
> Trạng thái được xét là `main` @ `541f0fe`: cả bốn lens đã chấm bằng engine chung (`data/derived/fidelity.parquet`, `docs/validation_report.md`), mới hơn bối cảnh ~16:00 trong đề bài review.
> Bốn phép thử mới trong mục 1 do tôi chạy trên dữ liệu thật của repo bằng script tạm (không nằm trong repo). Chúng là **thăm dò**: 4 địa điểm, mỗi nơi một cảnh EMIT, ngưỡng đặt tay. Đội phải dựng lại trong pipeline trước khi dùng con số nào lên slide.

## 1. Kiểm toán hiện trạng (Current State Audit & Ground Truth Check)

### 1.1. Những gì đã được dữ liệu chứng minh

| Khẳng định | Bằng chứng |
| :--- | :--- |
| "Cùng một công thức, hai thế giới" đúng theo nghĩa đen ở nhánh địa hình | Dốc tính bằng thư viện chung khớp sản phẩm dốc PGDA trong 0,001° ở cả 6 site (R4) |
| Phễu thô → mịn chọn đúng hướng | 300 ô xếp hạng: d trung vị 3,98; 200 ô ngẫu nhiên: 10,33 |
| **(mới)** Ô Trái Đất tốt nhất gần Connecting Ridge hơn phần lớn chính các footprint Mặt Trăng lân cận | 53 footprint Artemis khác ("anh em", đã bỏ 1 footprint trùng chính mục tiêu) cách Connecting Ridge: trung vị d = 3,28. Ba ô Trái Đất tốt nhất (d = 0,86–1,07) gần hơn **cả 53**; 38 % số ô xếp hạng gần hơn footprint anh em trung vị. Mới tính trên metric đường chéo hiện tại, chưa qua kiểm tra tập bền vững |
| Engine bác được mồi nhử và nói được lý do | Wadi Rum: 0 % pixel có dấu carbonate/Mg-OH; dương ở BD2210 (+0,05, sét Al-OH) |
| **(mới)** Lens phổ hoạt động khi so ở đúng tỷ lệ | Ở mức pixel 60 m: Semail 49 % pixel (≈12 km²) và Lake Salda 38 % pixel hợp lệ (≈1,4 km²) có đồng thời D2300 > 0,04 và MIN2295_2480 > 0,03; Wadi Rum 0 %; Harrat Khaybar 0 % |
| Attention Index định lượng được chữ "hidden" | Atacama 223, Haughton 130, Lake Salda 14, Semail 9, Harrat 0 |
| X1 nhận ra chuẩn vàng | Beacon Valley ở percentile 98,1 |
| Kỷ luật quy trình | Kỳ vọng ghi trước trong `controls.yaml`; kết quả trượt được ghi nguyên trạng |

### 1.2. Các bất thường, mổ xẻ tới nguyên nhân

**(a) Lake Salda — hai lỗi chồng nhau, không lỗi nào thuộc về địa điểm.**
1. Tọa độ đối chứng (37,55; 29,68) là **tâm hồ**. Footprint 5 km gần như toàn nước, còn 142 pixel bờ ẩm. Cùng loại lỗi với Karakul và Mistastin ở L1 (dốc 0° vì rơi vào mặt hồ).
2. Sai tỷ lệ so sánh: phổ MICA là phổ của **những pixel tốt nhất** trên Sao Hỏa (cỡ 18–54 m), còn phía Trái Đất ta lấy **trung vị 5 km**. Đây là vi phạm quy tắc "baseline chung" của chính DESIGN, ở trục không gian của nhánh phổ. PLAN ghi "phổ trung vị footprint"; lỗi này là của thiết kế, không phải của người triển khai.

Khi mở cửa sổ 8 km và xét từng pixel, Salda hiện ra đúng là analog carbonate: 1,4 km² khớp. Kết luận đúng: **Lake Salda là analog thật ở tỷ lệ ~1 km², không phải ở tỷ lệ 20 km².**

**(b) Độ lệch >4σ của mọi điểm Trái Đất — không phải khoáng vật.**
- Phân rã z trung bình của toàn bộ ô Trái Đất: HCPINDEX −4,6 đến −6,7; BD2250 khoảng −4 đến −6; MIN2250 −2,5 đến −4. Đây là các tham số nhạy với **dạng continuum** (I/F có bụi và khí quyển Sao Hỏa so với phản xạ bề mặt EMIT, cộng các cửa sổ EMIT bị che). Các tham số chẩn đoán hẹp (D2300, BD2290, MIN2295_2480) không mang độ lệch hệ thống này.
- Quần thể Σ của M1 là 29 phổ chuẩn thuộc nhiều lớp khoáng. σ ở M1 vì thế đo "khác biệt giữa các lớp khoáng", không phải "biến thiên giữa các địa điểm" như ở L1. Cùng ký hiệu σ, hai nghĩa khác nhau.

**(c) "Khớp rỗng" — vết nứt nguy hiểm nhất hiện có.**
Harrat Rahat/Khaybar đạt σ 0,24–0,63 so với Oxia Planum và đang mang nhãn `engine-confirmed` trên lens "khoáng vật do nước". Nhưng phổ mục tiêu Oxia (FE_SMECTITE) có D2300 = 0,030 và BD2290 = 0,015, tức xấp xỉ sàn dung sai 0,01. Bazan không có dấu phổ khớp với một mục tiêu gần như không có dấu phổ. Phép thử pixel xác nhận: Harrat Khaybar có **0 %** pixel mang dấu biến đổi do nước. Khoảng cách Mahalanobis đối xứng nên không diễn đạt được yêu cầu "phải *có* đặc trưng chẩn đoán".

**(d) X1 — dữ liệu bác giả thuyết của DESIGN, và dữ liệu đúng.**
Băng nông vĩ độ trung bình trên Sao Hỏa nằm dưới lớp phủ khô **không bao giờ tan**. 160–230 ngày đóng–tan mỗi năm ở Tây Tạng/Pamir nghĩa là tầng hoạt động ướt, xáo trộn do băng: cấu hình ngược lại. Hoang mạc cực (8–13 ngày) mới đúng. Giả thuyết số 5 của DESIGN (Pamir–Changtang cho X1) bị bác. Điểm yếu còn lại của X1: quần thể chỉ 5 điểm Sao Hỏa mã hóa từ văn liệu, và cổng `permafrost_min` được thêm sau khi xem kết quả.

**(e) L1 — chạy được, nhưng cách trình bày hiện tại sẽ bị bắt lỗi.**
- "σ = 0,00" là hệ quả của phép đổi χ₁₁ → χ₁ (mọi d ≲ 2 đều ra ≈ 0), trông như kết quả quá đẹp.
- Metric đường chéo trên 11 descriptor tương quan mạnh (các đại lượng dốc và nhám) đếm cùng một thông tin nhiều lần.
- Top-10 không ổn định (Jaccard trung vị 0,18): hàng chục ô cùng ở d ≈ 1.
- Hai DEM khác bản chất: LOLA là laser nội suy giữa các vệt bay (mịn giả ở tỷ lệ ngắn), GLO-30 là DSM radar có nhiễu 1–2 m (dốc giả ~1° trên đồng bằng).
- Baseline 30 m không thấy chướng ngại cỡ mét (đá tảng, hố nhỏ) vốn quyết định an toàn hạ cánh.
- Các ô đứng đầu ở vĩ độ cao phủ tuyết gần quanh năm: ô 81°N có `snow_free_frac` = 0,12; ô Baffin 71°N = 0,07. Chưa kiểm tra đó là đá lộ hay sông băng. Ô Changtang (33,5°N) = 0,80.
- Ô L1/L2 chưa có tên nên Attention = rỗng, và quy tắc hiện tại coi rỗng là "ẩn".
- Haughton trượt là lỗi kỳ vọng của DESIGN (tôi đã ghi "nên xếp cao"), không phải lỗi engine.

Một ý tưởng tôi đã thử và **bác bỏ**, để đội không tốn thời gian: tỷ lệ diện tích "trũng kín" (hố không thoát nước) làm chữ ký "bề mặt do va chạm tạo ra". Ở 30 m trên footprint 4 km, chính Mặt Trăng cũng gần bằng 0 (trung vị 0,001), nên không phân biệt được gì.

**(f) L2** — trục thiên văn là hàm thuần của vĩ độ; "no-analog" (σ 13,9) chính là kết quả. Không có gì để sửa, chỉ cần trình bày đúng.

**(g) Các quy tắc đã đổi sau khi thấy kết quả:** cổng σ ≤ 2 trong discovery, cổng permafrost X1, dời mốc D2300/BD2100, bỏ BD1750. Từng cái đều có lý do và đã được ghi, nhưng đang rải rác ở ba file.

### 1.3. Giám khảo chuyên môn sẽ hỏi gì nếu nộp nguyên trạng

1. "Các bạn so phổ của pixel đẹp nhất trên Sao Hỏa với trung vị 5 km trên Trái Đất. Vì sao?"
2. "Bazan khô là analog tốt nhất cho sét ở Oxia Planum?"
3. "σ = 0 nghĩa là gì? Và σ của M1 có cùng nghĩa với σ của L1 không?"
4. "DEM 30 m thì nói gì được về hạ cánh an toàn?"
5. "Các ô 'ẩn' ở Ellesmere: đã tra văn liệu chưa, và đó có phải mặt sông băng không?"
6. "Quy tắc nào được đặt sau khi các bạn đã nhìn thấy kết quả?"

Hiện tại câu 2 không có câu trả lời; các câu còn lại trả lời được nếu làm mục 3–4.

## 2. Nâng tầm tầm nhìn & Đột phá thiết kế (Elevated Architecture & Paradigm Shift)

### 2.1. Từ "Analog Finder" sang "Test-Transfer Matrix"

Đơn vị đầu ra không còn là "nơi giống nhất" mà là một **phán quyết ba trạng thái cho từng biến mà phép thử nhạy cảm**:

| Trạng thái | Nghĩa | Hành động của người lập kế hoạch thử nghiệm |
| :--- | :--- | :--- |
| **TRANSFERS** | Biến này khớp, có số đo và tỷ lệ áp dụng | Thử tại thực địa |
| **NO-ANALOG** | Không nơi nào trên Trái Đất khớp, có số đo khoảng cách tốt nhất | Chuyển sang buồng thử / mô phỏng |
| **UNOBSERVED** | Dữ liệu mở từ quỹ đạo không đo được biến này | Phải khảo sát thực địa trước khi cam kết |

Trạng thái thứ ba là phần mới so với DESIGN và là thứ biến giới hạn thành tính năng chẩn đoán: dải hydrat hóa 1,4/1,9 µm bị khí quyển che, chướng ngại cỡ mét dưới ngưỡng DEM 30 m, hằng số điện môi của lớp phủ cho radar. Hệ thống nói rõ "tôi không chứng nhận được điều này" thay vì im lặng.

### 2.2. Ba đại lượng mới, đều rẻ và đã có số thăm dò

1. **Native rank (thứ hạng giữa anh em).** Thay cho "σ = 0": *"Ô này gần Connecting Ridge hơn N trong 53 footprint ứng viên Artemis khác."* (số thăm dò: ba ô đứng đầu đạt 53/53) Tính bằng cách chấm chính quần thể Mặt Trăng như chấm ô Trái Đất. Trực giác, kiểm chứng được, và trả lời luôn câu hỏi số 3.
2. **Matched area và tỷ lệ hiệu lực.** Với lens phổ, so khớp từng pixel rồi báo **diện tích khớp (km²)** và mảng liền lớn nhất. Diện tích quyết định loại phép thử: vài hecta đủ cho thử thiết bị tại vết lộ, vài km² mới đủ cho một hành trình rover. Số thăm dò: Semail ≈ 12 km², Lake Salda ≈ 1,4 km².
3. **Presence gate (cổng hiện diện, một chiều).** Một pixel chỉ được tính là khớp khi *có* đặc trưng chẩn đoán của mục tiêu: mỗi tham số chẩn đoán ≥ một tỷ lệ cố định của giá trị mục tiêu **và** vượt sàn nhiễu. Thiếu đặc trưng thì không thể "giống" một mục tiêu có đặc trưng. Điều này đóng vết nứt "khớp rỗng".

### 2.3. Biến hai thất bại thành luận điểm

- **Lake Salda:** không phải "engine sai", cũng không phải "NASA sai". Phát hiện là: *độ tương đồng có tỷ lệ hiệu lực*. Analog nổi tiếng nhất của Jezero đúng ở 1 km², còn một ophiolite ít được nhắc tới (Semail, 9 bài) cho diện tích khớp lớn gấp ~9 lần. Lần chấm đầu của chính chúng tôi cho Salda percentile 12; truy nguyên nhân dẫn tới khái niệm matched area. Kể đúng trình tự đó lên slide.
- **Độ lệch 4σ:** trình bày thành bảng "bridge bias": tham số nào chuyển được giữa hai thiết bị, tham số nào không, kèm độ lệch đo được. Đây là kết quả đo lường về cặp CRISM–EMIT mà một nhóm muốn dùng lại sẽ cần.
- **Khung tương phản "Famous ≠ faithful":** ma trận 2×2 Attention × Fidelity. Haughton (130 bài) trượt lens địa hình vì quá phẳng; Wadi Rum (phim trường) trượt lens khoáng vật vì sét Al-OH; Salda (14 bài) đúng nhưng nhỏ; Semail (9) đúng và lớn; Harrat (0) không phải analog nước nhưng là nền bazan sạch.

### 2.4. Cầu phổ CRISM–EMIT đã hiệu chỉnh

| Vấn đề | Quy định mới |
| :--- | :--- |
| Sai tỷ lệ | So ở **pixel EMIT 60 m** (CRISM targeted gộp 3×3 ≈ 54 m: cùng cỡ). Bỏ trung vị footprint khỏi fidelity |
| Tham số nhạy continuum | HCPINDEX, BD2250, MIN2250 ra khỏi fidelity, vẫn báo cáo trong bảng bridge bias |
| Chọn tham số | Theo **họ chẩn đoán cho từng mục tiêu**, lấy từ định nghĩa browse product của Viviano-Beck 2014 (chuẩn bên ngoài, không tự chọn sau kết quả). Khai báo trong `lenses.yaml` trước khi chạy lại |
| Ngưỡng khớp | Quy tắc cố định cho mọi mục tiêu: tham số chẩn đoán ≥ 50 % giá trị mục tiêu và ≥ sàn nhiễu (đo từ phân vị 95 của pixel null). Ngưỡng 0,04/0,03 trong phép thử của tôi chỉ là thăm dò |
| Tỷ số hóa theo trung vị cảnh | **Không dùng.** Khi khoáng vật phủ rộng, trung vị cũng mang đặc trưng và phép chia xóa mất nó (Semail: MIN2295_2480 p90 tụt từ 0,087 xuống 0,008) |
| Phổ mục tiêu | Dùng bản MICA `ratioed` cho OLINDEX (numerator 0,384 so với ratioed 0,247; Semail p90 = 0,276). Các tham số hẹp gần như không đổi giữa hai bản |
| Mục tiêu quá yếu | Oxia (FE_SMECTITE) và Meridiani (JAROSITE) có đặc trưng ≤ 0,03 trong tập tham số dùng được trên Trái Đất → phán quyết **UNOBSERVED**, không tìm analog cho chúng bằng lens này |
| Giới hạn phải nói | 2,3 µm không tách được serpentine với Mg-carbonate khi mốc 2,5 µm nằm ở mép EMIT; gọi là "họ Mg-carbonate/serpentine" |

### 2.5. Định vị lại các ứng viên theo kịch bản sứ mệnh

| Ứng viên | Vai trò đúng | Phép thử gắn với sứ mệnh | Trạng thái bằng chứng hiện tại |
| :--- | :--- | :--- | :--- |
| **Semail, Wadi Tayin (Oman)** | Analog họ olivine–serpentine–carbonate ở tỷ lệ hành trình rover, cho rìa Jezero | Lập bản đồ khoáng bằng phổ kế VSWIR, quy trình chọn và khoan lấy mẫu trong đá siêu mafic bị biến đổi (bối cảnh mẫu Mars 2020 / Mars Sample Return) | Thăm dò (1 footprint); cần chạy pipeline |
| **Lake Salda** | Analog carbonate ở tỷ lệ vết lộ | Thử thiết bị và quy trình bảo tồn dấu hiệu sinh học tại chỗ | Thăm dò; cần sửa tọa độ theo quy tắc |
| **Harrat Khaybar / Rahat** | **Nền bazan không biến đổi** (đồng bằng núi lửa Sao Hỏa), Attention 0; L1 ở percentile 93,5 | Điểm "không" để hiệu chuẩn phổ kế, thử cơ động trên bazan; ống dung nham Umm Jirsan chỉ là bằng chứng văn liệu | Phải **gỡ nhãn analog nước** |
| **Sườn núi Changtang (33,5°N; 84,2°E)** | Analog phân bố dốc–nhám của Connecting Ridge, ít tuyết (0,80) | Thử tuyến LTV theo phân bố dốc 30–480 m | Engine xác nhận ở L1; cần tên, Attention, ảnh |
| **Ellesmere bắc / Baffin** | Kết hợp tốt nhất có thể trên Trái Đất giữa dốc khớp và Mặt Trời thấp (20–27 % thời gian ban ngày, so với 100 % ở cực Mặt Trăng) | Thử cảm biến dẫn đường với bóng dài thật | Chờ kiểm tra tuyết/băng |
| **Hoang mạc cực Bắc Canada** | Gần nhất ngoài Nam Cực cho băng dưới lớp phủ khô, nhưng σ 2,4 | Phát biểu đúng: "ngoài Nam Cực không nơi nào trong 2σ" | Bán định lượng |

Một điểm đáng đưa lên slide: **Changtang bị bác ở lens băng nhưng đứng đầu ở lens địa hình.** Cùng một cao nguyên, hai lens, hai phán quyết ngược nhau: minh họa trực tiếp cho nguyên tắc "fidelity theo nhiệm vụ".

## 3. Quyết định kỹ thuật tại cổng G1 (G1 Decisions & Architectural Fixes)

### 3.1. M1 — giữ đường chính, đổi đơn vị so sánh

- **Giữ** EMIT + công thức CRISM. **Không lùi** về EMIT L2B: lùi là bỏ luôn khẳng định "cùng công thức".
- **Đổi:** so khớp theo pixel, họ chẩn đoán theo mục tiêu, presence gate, đầu ra là matched area. Mục tiêu tìm analog: Jezero margin (chính) và Nili Fossae olivine. Oxia và Meridiani chuyển sang UNOBSERVED.
- **Gỡ ngay** nhãn `engine-confirmed` của Harrat Rahat, Harrat Khaybar, Pinacate trên M1.
- **Tiêu chí dừng lúc 21:00:** chạy pipeline pixel trên đối chứng và mồi nhử. Đạt nếu Salda và Semail có matched area > 0, còn Wadi Rum và Simpson ≈ 0. Không đạt → M1 lên slide dưới dạng "phương pháp minh họa trên 4 địa điểm + kết quả âm ở tỷ lệ footprint", không công bố hidden analog cho M1.
- **Đính chính tọa độ theo quy tắc, không theo ý muốn:** một quy tắc chung cho mọi điểm (ví dụ: nếu < 50 % footprint là đất hợp lệ thì mở cửa sổ tới khi đủ, hoặc dời tới tâm vùng đất hợp lệ gần nhất). Áp cho Salda, Karakul, Mistastin; báo cả kết quả gốc lẫn kết quả sau đính chính.

### 3.2. X1 — giữ bán định lượng, chuyển từ "độ giống" sang "danh sách điều kiện cấu hình"

- Ba điều kiện: (1) có permafrost; (2) lớp phủ không tan tới mặt băng (số ngày đóng–tan bề mặt thấp là **điều kiện loại**, không phải trục tương đồng); (3) lớp phủ khô.
- Sàn của từng điều kiện lấy từ Beacon Valley (chuẩn tham chiếu) và vật lý của mục tiêu, ghi rõ là đặt sau khi xem dữ liệu.
- Ghi trên phiếu: nhiệt độ đất ERA5-Land là **đầu ra mô hình tái phân tích lưới ~9 km**, không phải quan trắc; số ngày đóng–tan từ MODIS là nhiệt độ bề mặt trời quang.
- Phát biểu kết quả: Beacon Valley đạt; ngoài Nam Cực, nơi gần nhất ở σ 2,4. Giả thuyết Pamir–Changtang ghi là **bị dữ liệu bác**. Trạng thái tối đa `engine-semiquant`. Không đầu tư thêm thời gian vào X1.

### 3.3. L1 / L2

- Hiển thị **native rank + d**; σ chỉ ghi "< 0,1" khi cần.
- Công bố **tập bền vững**, không công bố thứ hạng: ô phải nằm trong nhóm gần nhất dưới cả ba cấu hình — metric đường chéo 11 descriptor (hiện tại), metric đầy đủ trên 6 descriptor (slope_p50, slope_p90, frac_gt20, rms_s1, rms_s16, hurst), và baseline L = 90 m. Cách này trả lời cùng lúc vấn đề tương quan, độ bất ổn top-10 và khác biệt bản chất hai DEM.
- Phạm vi khẳng định ghi rõ: "khớp thống kê dốc–nhám ở baseline 30–480 m". Chướng ngại cỡ mét: UNOBSERVED.
- Ô vĩ độ cao phải qua kiểm tra tuyết/băng (WorldCover lớp 70, ảnh Sentinel-2) trước khi gọi là ứng viên.
- L2: tách hai dòng trên mọi phiếu — hình học Mặt Trời: NO-ANALOG (tốt nhất trong mẫu Trái Đất 28 % ở 69,5°N, so với 100 %); bóng đổ địa hình: TRANSFERS kèm σ_shadow.

### 3.4. Chuẩn hiển thị trên Test Card và web

```
[Tiêu đề theo quá trình] — [tên địa điểm]            Vai trò: analog nước | nền bazan | địa hình
Đạt chuẩn cho:    <phép thử>  — <biến> TRANSFERS (native rank N/53 | X km² khớp)
Không đạt cho:    <phép thử>  — <biến> NO-ANALOG (Trái Đất tốt nhất: 28 % so với 100 %) → <cơ sở thử>
Chưa chứng nhận:  <phép thử>  — <biến> UNOBSERVED (lý do) → cần đo tại chỗ
Yếu tố giới hạn: <descriptor>     Tỷ lệ hiệu lực: <km² / baseline>
Transfer Ledger:  g 0,165 · áp suất · bức xạ … (có nguồn)
Bằng chứng: engine-confirmed | engine-semiquant | literature-only     Attention: n bài
```

Ví dụ nội dung, chỉ dùng số đã có nguồn trong ledger:
- Phiếu X1: "Radar xuyên đất dò mặt băng: cấu hình băng dưới lớp phủ khô TRANSFERS; tương phản điện môi của lớp phủ UNOBSERVED từ quỹ đạo, phải đo tại chỗ."
- Phiếu L1: "Tuyến LTV theo phân bố dốc: TRANSFERS. Độ lún và lực kéo bánh xe: NO-ANALOG (trọng lực 0,165 g) → hệ treo giảm trọng lực. An toàn hạ cánh theo đá tảng: UNOBSERVED ở 30 m."

### 3.5. Bảng "Deviations from pre-registration"

Gom vào một bảng trong `docs/validation_report.md`: quy tắc nào đổi, lúc nào, vì sao, ảnh hưởng tới kết quả nào. Tối thiểu gồm: cổng σ ≤ 2; cổng permafrost X1; dời mốc D2300/BD2100; bỏ BD1750; chuyển M1 sang pixel; đính chính ba tọa độ; đổi nguồn nhiệt độ X1. Đây là câu trả lời cho câu hỏi số 6.

## 4. Điều chỉnh kế hoạch triển khai (Adjusted Execution Plan)

### 4.1. Việc cập nhật ngay

| Ai | Việc | Ước lượng |
| :--- | :--- | :--- |
| **Linh** | M1 pixel: tải pixel footprint bằng `computePixels` (10–50 s/footprint), chạy `crism_params` của thư viện chung trên từng pixel, xuất matched area + mảng liền lớn nhất + phân vị tham số. Chạy đối chứng/mồi nhử trước, rồi hạt giống, rank, null | 2,5–3 giờ |
| **Linh** | Khai báo họ chẩn đoán, quy tắc ngưỡng, sàn nhiễu trong `lenses.yaml` **trước** khi chạy toàn bộ; thêm trường vai trò (`aqueous` / `substrate-baseline` / `terrain`); gỡ nhãn Harrat | 45 phút |
| **Linh** | X1: đổi cách trình bày thành danh sách điều kiện; ghi chú nguồn mô hình | 30 phút |
| **Linh** | Test Card ba trạng thái; L2 hai dòng; hiển thị native rank / matched area | 1,5 giờ |
| **Bảo** | Cột native rank trong `fidelity.parquet` (chấm quần thể Mặt Trăng như ô Trái Đất) | 30 phút |
| **Bảo** | Tập bền vững L1: metric đầy đủ 6 descriptor + chạy lại ở L = 90 m từ chip đã cache | 1,5 giờ |
| **Bảo** | Đặt tên, Attention, kiểm tra tuyết/băng và ảnh cho các ô trong tập bền vững; quy tắc đính chính tọa độ | 1,5 giờ |
| **Bảo** | Báo cáo kiểm chứng bản 2: bảng ba trạng thái, bảng bridge bias, bảng Deviations | 1 giờ |

Không làm: ablation ảnh LROC, mô tả trũng kín, tỷ số hóa theo cảnh, thêm lens, mở rộng X1.

### 4.2. Dự phòng

- **21:00:** tiêu chí dừng M1 (mục 3.1). Nếu tập bền vững L1 rỗng → công bố tập dưới metric hiện tại kèm ghi chú độ nhạy.
- **Data Freeze 03:00 — câu chuyện tối thiểu vẫn đứng được:** L1 tập bền vững với native rank; L2 con số no-analog; M1 bốn địa điểm ở mức pixel; X1 Beacon Valley và phát biểu khan hiếm.
- **Code Freeze 15:00:** nếu Test Card ba trạng thái chưa xong trên web → dùng bảng tĩnh trong slide 6; web giữ bản hiện tại nhưng **bắt buộc** đã gỡ nhãn sai của Harrat và sửa hiển thị L2.

### 4.3. Khung 7 slide

| # | Nội dung | Tiêu chí |
| :--- | :--- | :--- |
| 1 | **"Famous ≠ faithful."** Kỹ sư hầm gió không hỏi mô hình có giống máy bay không. Một câu định nghĩa sản phẩm: ma trận chuyển giao thử nghiệm cho Moon Base và Sao Hỏa | Presentation |
| 2 | Vấn đề: analog được chọn theo vẻ ngoài và danh tiếng. Bằng chứng ngoài: phương pháp texture ảnh xếp Devon Island chót. Bằng chứng trong: lần chấm đầu của chính chúng tôi cho Lake Salda percentile 12 | Impact, Relevance |
| 3 | Phương pháp: cùng công thức trên dữ liệu NASA của hai thế giới; bốn lens theo nhiệm vụ; phán quyết ba trạng thái | Creativity, Validity |
| 4 | Kiểm chứng trung thực: bảng kỳ vọng ghi trước gồm cả lần trượt; dốc khớp PGDA 0,001°; Wadi Rum trượt vì sét Al-OH; truy vết Salda → tỷ lệ hiệu lực; bảng Deviations | Validity |
| 5 | Phát hiện: sườn núi Trái Đất gần Connecting Ridge hơn mọi footprint Artemis khác đã lấy mẫu (nếu tập bền vững xác nhận); Semail 12 km² so với Salda 1,4 km²; Changtang: bị bác ở lens băng, đứng đầu ở lens địa hình; ma trận Attention × Fidelity | Creativity |
| 6 | Sản phẩm: một Test Card thật + Transfer Matrix. Câu chốt: hình học Mặt Trời cực Mặt Trăng không thử được ở đâu trên Trái Đất (28 % so với 100 %); đây là con số | Impact |
| 7 | Dữ liệu NASA và đối tác, giới hạn, giấy phép, khai báo SI, link repo và web | Tuân thủ |

Mọi con số trên slide 4–6 phải lấy từ pipeline sau khi chạy lại; các số thăm dò trong bản review này chỉ để định hướng.

### 4.4. Nguồn của các số thăm dò

- Script tạm: `/tmp/claude-1000/-home-toska-code-personal-nasa-earth-analog/a01d9d91-857d-4aed-8736-b9c85e2fb469/scratchpad/g1_probe.py` (phân rã z của M1, native rank L1, trũng kín) và `/tmp/claude-1000/-home-toska-code-personal-nasa-earth-analog/a01d9d91-857d-4aed-8736-b9c85e2fb469/scratchpad/g1_pixels.py` (pixel EMIT cho Semail, Lake Salda cửa sổ 8 km, Wadi Rum, Harrat Khaybar).
- Chưa kiểm: Simpson Desert ở mức pixel; các footprint Semail khác; độ ổn định theo cảnh EMIT; kiểm tra băng cho ô vĩ độ cao.
