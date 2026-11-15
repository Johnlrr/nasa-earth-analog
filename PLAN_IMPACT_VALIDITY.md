# PLAN: SIMILITUDE — từ tìm analog đến lập chiến dịch kiểm thử có bằng chứng

Nguồn: yêu cầu trực tiếp của người dùng ngày 15/11/2026; đánh giá được đính kèm; khảo sát repo và nguồn NASA/USGS. Cổng 1: chưa chạy. Đây là đề xuất kế hoạch mới theo mẫu `.agent/templates/PLAN.md`, không thay thế trạng thái đã duyệt của `PLAN.md` cũ.

## Phạm vi

### 1. Quyết định sản phẩm

**Đề xuất: xây SIMILITUDE thành công cụ hỗ trợ kỹ sư lập kế hoạch kiểm thử navigation/mobility cho rover Moon/Mars.** Tìm địa điểm vẫn là một khâu, nhưng đơn vị đầu ra là **chiến dịch kiểm thử**: mục tiêu, địa điểm/tuyến dự kiến, điều kiện chiếu sáng, tình huống được bao phủ, khoảng trống bằng chứng, phép đo bổ sung và hồ sơ để review.

Lời hứa đề xuất trên website:

> Plan Earth tests for planetary terrain and lighting challenges. See what your campaign covers, what remains untested, and what evidence supports each choice.

Không hứa chứng nhận chuyến bay hoặc chứng minh transfer chỉ bằng ảnh vệ tinh. Không lấy số lượng địa điểm/lens làm KPI. Không hứa điểm giám khảo trước khi có kết quả kiểm chứng mới.

Người dùng chính: kỹ sư test/verification phụ trách xây test matrix và chọn môi trường cho perception, localization và traverse planning. Người review: mobility lead và systems engineer. Nhà địa chất và người xem phổ thông là người dùng phụ; không ép một giao diện giải quyết mọi nghiệp vụ.

Job to be done: “Với hệ thống, vùng đích và ngân sách thử nghiệm này, tôi cần đi đâu, chạy những tình huống nào, đo gì và bổ sung phép thử nào trước khi review?”

### 2. Cơ sở thực tế và mức độ chắc chắn

Các vấn đề sau có bằng chứng công khai; nhu cầu sử dụng chính SIMILITUDE vẫn là giả thuyết cần phỏng vấn/đánh giá người dùng:

| Bằng chứng | Vấn đề kỹ thuật có thật | Hệ quả cho sản phẩm đề xuất |
|---|---|---|
| NASA/JPL ERNEST thử terrain và autonomy ngoài sa mạc, gồm các thời điểm ánh sáng khác nhau [S1] | Hệ thống phải chịu tổ hợp địa hình và điều kiện nhìn; các bước thử đi qua mô phỏng, bãi thử, thực địa | Đánh giá tổ hợp tình huống, có chuyển tiếp giữa môi trường thử |
| Nghiên cứu NASA về driving dưới ánh sáng cực Nam [S2] | Hướng ánh sáng, tốc độ và hình dạng địa hình ảnh hưởng việc nhận biết nguy hiểm | Không đủ chỉ thống kê số giờ Mặt Trời thấp; cần hướng chạy tương đối với ánh sáng và nhiệm vụ cụ thể |
| Ames có testbed với đèn tái tạo ánh sáng góc thấp [S3] | Điều kiện thử có thể được tạo có chủ đích | L2 nên đề xuất cửa sổ tự nhiên hoặc cấu hình đèn; không dừng ở NO-ANALOG |
| Glenn SLOPE/TREC kiểm tra lực kéo, tải và vật liệu mô phỏng [S4] | Cơ học tiếp xúc cần điều kiện có kiểm soát và đo thực nghiệm | Lập yêu cầu năng lực facility và thông số thử; không suy lực kéo từ DEM |

Khoảng trống cần kiểm chứng: công cụ có giúp nhóm nối dữ liệu quỹ đạo → điều kiện thử → bằng chứng review nhanh/chặt chẽ hơn workflow GIS + spreadsheet hiện tại không? Không tuyên bố NASA chưa có công cụ tương tự hoặc đang cần sản phẩm này nếu chưa xác minh.

### 3. Chẩn đoán repo hiện tại

| Quan sát trong repo | Ý nghĩa | Hành động |
|---|---|---|
| `web/index.html` lấy Da Qaidam làm hero; bốn lens được đặt ngang nhau | Người dùng thấy kết quả khoa học trước khi biết có thể dùng nó vào việc gì | Hero theo tình huống kỹ sư; chọn demo sau khi có dữ liệu thực tiễn |
| `web/app.js` dùng “Qualified for”, “the field test is valid for the target” | Ngôn ngữ vượt quá bằng chứng terrain matching | Phân biệt similarity, coverage và validation |
| `docs/validation_report.md` nêu 102/109 verdict ổn định giữa DEM; độ lệch slope rất nhỏ | Có giá trị kiểm chứng tính toán/độ bền dữ liệu; chưa chứng minh hiệu suất thiết bị | Giữ nguyên kết quả, thêm kiểm chứng ở cấp nhiệm vụ |
| Peary Land không giữ nguyên trạng thái với DEM thứ hai; footprint lân cận khác kết quả | Bất định có thể đổi quyết định | Hiện footprint, độ ổn định và thứ cần khảo sát ngay trên card |
| L1 dùng footprint 4 km và terrain thô; M1 trượt; X1 bán định lượng | Bốn module chưa có cùng mức trưởng thành | Ưu tiên terrain/navigation; đưa M1/X1 vào Research |
| L2 có terrain-shadow match nhưng không tái tạo đầy đủ Sun geometry | Không đồng nghĩa mọi bài thử chiếu sáng ngoài trời đều vô ích | Định nghĩa bài thử theo thời gian hữu hạn và điều kiện cụ thể |
| `docs/test_protocols.md` đã có nguồn requirement và giới hạn TRL | Không cần viết lại toàn bộ; thiếu giao diện nhập requirement và sinh test case cụ thể | Tái sử dụng provenance, bổ sung planning engine |

Đánh giá Opus đúng ở khoảng cách giữa proxy và usefulness, nhưng cần chỉnh ba điểm:

1. Không có analog toàn phần có thể là kết quả khoa học hợp lệ. Vấn đề là đầu ra tiếp theo chưa đủ hữu ích.
2. Nhiều deviations không tự chứng minh nghiên cứu sai. Cần phân biệt exploratory với confirmatory, giữ lịch sử và chạy bộ kiểm chứng mới chưa bị dùng để tinh chỉnh.
3. Wolf Amendment liên quan hạn chế hoạt động song phương được NASA tài trợ, không đủ để kết luận đơn giản “mọi dữ liệu/địa điểm ở Trung Quốc đều cấm”. Đọc NASA FAQ [S5]; dùng cờ policy review với nguồn, không tự cấp phán quyết pháp lý. Khu vực tại Mỹ cũng không mặc nhiên có quyền vào hoặc thử robot.

### 4. Năm năng lực cốt lõi

**A. Mission-to-test brief.** Người dùng chọn target polygon, nhiệm vụ, thông số sensor/rover có liên quan, phạm vi thử, khoảng thời gian và ràng buộc chiến dịch. Mỗi requirement lưu nguồn, đơn vị, baseline không gian, phiên bản và người chịu trách nhiệm. Phân biệt yêu cầu NASA được công bố, giả định của dự án và cấu hình do người dùng nhập. Không lấy giới hạn landing của HLS làm giới hạn rover mặc định.

**B. Đánh giá địa hình theo đúng tỷ lệ và nhiệm vụ.** Giữ DEM thô cho tìm kiếm vùng. Tại shortlist, dùng dữ liệu độ phân giải cao nếu có: Earth 3DEP/LiDAR, Moon LOLA/LROC phù hợp, Mars HiRISE DTM/ortho [S6, S7]. Không nội suy 30 m thành 1 m rồi coi là thông tin mới. Pixel size không bằng độ chính xác hoặc kích thước vật nhỏ nhất phát hiện được. DEM bare-earth 1 m cũng chưa bảo đảm giữ đá hoặc cấu trúc nhỏ; kiểm tra point cloud/ảnh/khảo sát trước khi gắn rock metric.

Tính dốc dọc/ngang hướng tuyến, relief và roughness theo baseline, tính liên thông của hành lang hình học, đoạn chuyển vùng sáng–tối. Thêm rock size/density và soil properties chỉ khi có dữ liệu đủ chứng cứ. Đường nối được trên raster không đồng nghĩa đường đi an toàn cho rover.

**C. Terrain × lighting test coverage.** Xây tập tình huống từ target và test objectives: slope, roughness, hướng di chuyển so với nguồn sáng, góc cao nguồn sáng, đoạn chuyển shadow, tốc độ/sensor mode khi có. Dùng tổ hợp chung; không cộng các phân bố biên rồi nói đã cover tương tác. Mỗi tình huống có observation metric, số lần lặp và điều kiện chấp nhận do test owner quyết định.

L2 mới có hai đầu ra: cửa sổ ngày/giờ đủ dài cho test run; hoặc bố trí đèn dự kiến và yêu cầu đo hiệu chuẩn. Giữ các chênh lệch sky scattering, albedo/BRDF, quang phổ, camera exposure. Bóng hình học giống nhau chưa chứng minh chất lượng camera trên Moon giống nhau. Xét sai số do đèn gần, độ phân kỳ chùm sáng và sự không đều trên cả tuyến.

**D. Campaign builder.** So sánh tập lựa chọn `site + route + time/setup`, chọn tổ hợp bao phủ mục tiêu dưới ràng buộc thời gian/chi phí/quyền tiếp cận. Hiện Pareto trade-off thay vì một “Earth analog score” duy nhất. Địa điểm quen thuộc có thể là lựa chọn tốt nếu phục vụ test; độ mới là lớp discovery riêng.

Tách ba cổng: suitability khoa học; completeness của bằng chứng; feasibility vận hành. Road distance chỉ là proxy, không phải permit. Chi phí chưa có báo giá là estimate có nguồn hoặc unknown. Catalog facility chỉ nói năng lực, không ngầm xác nhận có lịch trống hay chấp thuận sử dụng.

**E. Reconnaissance + evidence pack.** Mỗi khoảng trống sinh nhiệm vụ khảo sát có lý do: đo kích thước đá, khảo sát địa hình cục bộ, lấy chỉ tiêu đất phù hợp bài thử, đo shadow contrast, xác nhận đường vận chuyển/quyền vào. Ưu tiên theo khả năng phép đo làm thay đổi lựa chọn; chỉ dùng Expected Value of Information khi có mô hình xác suất và chi phí đủ cơ sở. Trước đó dùng sensitivity/rank reversal, tránh một điểm “VOI” tự gán.

File xuất: brief, test matrix, hình có scale/legend, GeoJSON tuyến/polygon, sources và run manifest, giả định, biến chưa đo, yêu cầu facility, checklist reconnaissance. Đây là draft để review, không phải safety clearance hay chứng nhận TRL.

### 5. Chiến lược Moon/Mars và địa điểm

- Case Moon chủ lực: kế hoạch thử navigation trong địa hình cực Nam và ánh sáng góc thấp, giới hạn rõ vào những yếu tố quan sát được.
- Case Mars thứ hai: terrain/perception test campaign cho một polygon Jezero có DTM/ảnh thật. Tái sử dụng kiến trúc, nhưng có target profile và validation riêng. Không dùng lunar thresholds cho Mars.
- M1: giữ kết quả FAIL hiện tại. Chỉ đưa lại sản phẩm khi có protocol mới và đối chứng độc lập; không hạ ngưỡng để cứu demo.
- X1: nghiên cứu riêng về ice configuration; cần dữ liệu độ sâu băng/lớp phủ độc lập trước khi biến thành đề xuất drilling test.
- Earth shortlist đầu tiên: khảo sát vùng Flagstaff/San Francisco Volcanic Field, Mojave/Colorado Desert và testbed được tài liệu cơ quan mô tả. Đây là **vùng để kiểm tra dữ liệu và feasibility**, chưa là địa điểm được xác nhận phù hợp. JPL Mars Yard/Ames/Glenn là tham chiếu năng lực, không phải điểm có thể tự tới.
- Không bỏ tìm analog mới: dùng search toàn cầu để phát hiện nơi bổ sung các tình huống còn thiếu, sau đó mới kiểm chứng vận hành.

### 6. Kế hoạch tăng Validity

**V0 — Đóng băng khám phá hiện tại.** Lưu manifest/hash của config, code, dữ liệu và kết quả; ghi rõ toàn bộ kết quả cũ là development/exploratory theo lịch sử thật. Không hồi tố gọi seed/threshold là preregistered.

**V1 — Khóa protocol mới trước khi xem holdout.** Chọn nhiệm vụ, endpoint chính, baseline, giả thuyết, rule dừng và phân hoạch theo site/region; ghi hash và timestamp có thể kiểm tra. Người giữ holdout độc lập nếu có. Pixel/footprint kề nhau không được rải ngẫu nhiên giữa train và test. Với cohort nhỏ, công bố limited evidence, không suy rộng toàn cầu.

**V2 — Kiểm chứng construct.** So geometry descriptors với khảo sát/DTM độc lập tại cùng footprint và baseline. Kiểm tra joint terrain-lighting configurations và khả năng thực hiện test case. NASA slope raster cùng nguồn DEM xác minh implementation, không phải độc lập về dữ liệu. Kiểm tra lineage giữa các DEM trước khi gọi “independent”.

**V3 — Kiểm chứng task.** Nếu có phần cứng: cố định sensor/algorithm, chạy lặp có ground truth và điều kiện được đo. Chọn endpoint phù hợp, ví dụ localization drift trên quãng đường, hazard recall tại mức false-positive cố định hoặc intervention rate; tách theo terrain/light bin. Nếu chỉ có mô phỏng: gọi simulation validation, báo giả định renderer/sensor và chưa chứng minh transfer vật lý. Không dùng simulator cùng công thức score để tự chứng minh score đúng.

**V4 — So baseline đủ mạnh.** So với chọn site quen thuộc, GIS + spreadsheet, slope-only, nearest-feasible và random đã ghép ràng buộc. Cùng số site, thời gian, dữ liệu và phạm vi khả dụng. Ablation terrain-only / terrain+lighting / thêm operational constraints. Không lấy chênh “76% vs 9%” hiện tại làm chứng minh tác động độc lập vì engine đã chọn theo các descriptor liên quan.

**V5 — Độ bền quyết định.** Perturb uncertainty có cấu trúc không gian, DEM resolution, tọa độ, target polygon, trọng số và weather assumptions; báo rank stability, selection frequency và khoảng kết quả. Bootstrap theo site/region, không coi hàng triệu pixel là hàng triệu mẫu độc lập. Nếu perturbation đổi shortlist, gắn sensitive và nêu phép đo nào giải quyết được.

**V6 — Tác động sử dụng.** Pilot đề xuất với 5–8 kỹ sư/nhà nghiên cứu robotics hoặc analog field testing; ghi rõ affiliation, không gọi họ là NASA engineers nếu không đúng. Cỡ này phục vụ usability ban đầu, không đủ chứng minh hiệu quả toàn ngành. Bài tập đối chứng có thứ tự đảo/counterbalance: lập cùng loại campaign bằng workflow hiện tại và SIMILITUDE. Đo thời gian tạo hồ sơ review, lỗi giả định, số missing requirements phát hiện được và chất lượng hồ sơ do reviewer chấm mù. Muốn kết luận efficacy cần thiết kế/cỡ mẫu tiếp theo theo pilot variance.

Gate phát hành: có một campaign tái lập được; không có critical constraint bị “unknown → pass”; claim nối được đến dữ liệu; holdout đáp ứng criterion đã khóa. Nếu predictive validation thất bại, giữ sản phẩm ở mức planning/reconnaissance và công bố thất bại. Không dùng số lượng unit tests thay cho gate khoa học.

### 7. Website: mạch quyết định và câu chuyện

Mạch chính: **Mission → Test objectives → Candidate comparison → Campaign → Evidence export.** Map là công cụ trong workflow, không là câu trả lời đầu tiên.

| Màn hình | Câu hỏi người dùng | Nội dung và thao tác |
|---|---|---|
| Home / guided case | Công cụ giúp tôi ra quyết định gì? | Một cặp ảnh target–Earth thật, cùng tỷ lệ; tình huống kỹ sư; CTA “Plan a test campaign”, CTA phụ “Explore a worked example” |
| Mission brief | Tôi đang thử hệ thống nào? | Target polygon, mục tiêu, sensor/rover, constraints; preset có nguồn và editable assumptions |
| Target profile | Tôi cần tái tạo những tình huống nào? | Geometry/light profile, thước đo, độ phân giải, điều chưa quan sát; tránh ép đọc sigma ở bước đầu |
| Compare | Ba lựa chọn khác nhau ở đâu? | Bản đồ song song, scale đồng nhất, ground images nếu có, joint coverage và feasibility; lý do bị loại |
| Campaign | Tôi sẽ làm gì tại từng nơi? | Test runs, route dự kiến, time windows/setup, duplicate coverage, uncovered cases và reconnaissance |
| Evidence | Tôi bảo vệ lựa chọn này thế nào? | Claim → source → transformation → uncertainty → validation; tải hồ sơ và tái lập run |

Demo có chủ đích: người dùng chọn Moon navigation → thấy site A thiếu một nhóm tình huống → thêm time window hoặc site B → coverage thay đổi → hệ thống chỉ ra một thông số đất chưa đo → xuất hồ sơ. Mọi số trong demo phải đọc từ kết quả thật. Nếu chưa đủ dữ liệu, đánh dấu scenario illustration, không trộn mock vào evidence.

Visual direction: bản đồ/ảnh khoa học là trọng tâm; nền trung tính sáng cho bảng kỹ thuật, vùng tối khi cần đọc shadow; typography dễ đọc; bảng có unit; tránh dashboard nhiều số không gắn quyết định. Animation chỉ dùng khi thay đổi góc sáng, layer hay coverage giúp hiểu quan hệ. Không dùng hình tạo sinh làm chứng cứ địa điểm.

Trên mỗi kết quả: “Observed terrain match”, “Modelled lighting coverage”, “Needs site survey”, “Measured in this test” theo bằng chứng thực tế. Giới hạn ảnh hưởng quyết định nằm sát kết quả, không chỉ ở footer. NO-ANALOG phải phân biệt “không tìm thấy trong tập đã khảo sát” với giới hạn vật lý không thể tái tạo.

Kiểm thử UX: người mới hoàn thành guided case và nói đúng kết luận/giới hạn; người kỹ thuật truy về một claim đến source mà không cần đọc code; keyboard và mobile đọc được; không dùng màu như tín hiệu duy nhất. Chưa đánh giá giao diện hiện tại bằng browser trong phiên khảo sát này; nhận xét dựa trên HTML/JS.

## Schema / giao diện

Tái sử dụng Python pipeline và web tĩnh ở bước đầu; không bắt buộc chuyển framework/backend để làm sản phẩm chuyên nghiệp. Precompute rasters/descriptors; chạy các phép chọn nhẹ trên catalog đã kiểm tra. Khi cần AOI tùy ý hoặc tính toán nặng mới thêm job service có cache, version và trạng thái lỗi.

Các entity đề xuất:

| Entity | Trường chính |
|---|---|
| `MissionProfile` | id, body, target_geometry, task, hardware_profile, objectives, provenance |
| `Requirement` | id, metric, unit, spatial_baseline_m, threshold_or_range, authority_type, source, version |
| `SiteObservation` | geometry, measurement, unit, resolution, uncertainty, timestamp, source_lineage, quality_flags |
| `Scenario` | target_id, joint_conditions, mandatory, weight, tolerance, minimum_exposure, evidence_requirement |
| `TestOption` | site_id, route_geometry, time_window/setup, covered_scenarios, evidence_status, feasibility, cost_interval |
| `Campaign` | profile_id, selected_options, covered/uncovered/unknown, assumptions, survey_tasks, manifest_id |
| `Evidence` | claim_id, source, transform_version, input_hashes, validation_status, limitations |

Thay vì trộn các chiều vào một enum: `match_status` (match/mismatch/unknown), `evidence_status` (modelled/measured/validated_for_task), `feasibility_status` (documented/pending/restricted) và `scope` (biến, footprint, baseline, task). Thiếu dữ liệu không được biến thành NO-ANALOG hoặc pass.

Coverage định nghĩa ban đầu: `C(S) = sum_j(w_j * I_j(S)) / sum_j(w_j)`; `I_j=1` chỉ nếu một test option trong campaign đáp ứng **đồng thời** các điều kiện scenario j, đủ thời lượng và mức evidence yêu cầu. Nếu các biến chỉ xuất hiện ở các site khác nhau thì không tự tạo joint coverage. Requirement bắt buộc là hard constraint, không được bù bằng tổng điểm cao. Báo riêng modelled coverage và measured coverage; không gọi C là xác suất thành công của mission. Trọng số biểu diễn ưu tiên do người dùng chọn hoặc phân bố target được chỉ rõ, không ngầm là xác suất rủi ro đã hiệu chuẩn.

## Hạng mục

Thứ tự theo phụ thuộc. Khối lượng dưới đây là ước tính lập kế hoạch cho đội 2 người, không phải cam kết deadline. Lịch thu thập thực địa, quyền sử dụng địa điểm và phản hồi chuyên gia có thể dài hơn thời gian viết code.

| Mốc | Mục tiêu | Ước tính | Điều kiện chuyển mốc |
|---|---|---|---|
| P0 | Khóa bài toán, claim và protocol | 3–5 ngày làm việc | Một task rõ; endpoint và holdout được ghi trước |
| P1 | Một lát cắt Moon hoàn chỉnh | 2–3 tuần | Brief → data → coverage → export chạy trên nguồn thật |
| P2 | Validation và feasibility thực tế | 3–6 tuần, phụ thuộc dữ liệu/người thử | Có benchmark độc lập, hoặc giới hạn claim theo kết quả |
| P3 | Website hoàn thiện, case Mars, user pilot | 2–4 tuần | Hai case có provenance; workflow được người ngoài dùng thử |
| P4 | Nghiên cứu mở rộng | Sau các gate | M1/X1 chỉ quay lại khi có evidence đủ mạnh |

- [ ] 1. Khóa persona và decision. File: `docs/user_research.md`, `docs/product_brief.md`. Xong khi: một task ưu tiên, workflow hiện tại, output review và giả thuyết giá trị được mô tả; phân biệt literature evidence với interview. Kiểm chứng: reviewer truy từng quyết định tính năng về task. Chưa tự liên hệ bên ngoài trong kế hoạch này.
- [ ] 2. Audit claims và provenance. File: `docs/claim_audit.md`, `README.md`, `web/index.html`, `web/app.js`, `scripts/web_evidence.py`. Xong khi: không còn qualified/transfer claim vượt evidence; kết quả cũ còn truy được. Kiểm chứng: đối chiếu claim trên UI với nguồn máy sinh.
- [ ] 3. Khóa protocol v2. File: `config/validation_v2.yaml`, `docs/validation_protocol_v2.md`, `data/manifests/`. Xong khi: split theo vùng, primary endpoint, baseline, rule dừng, hashes được cố định trước holdout. Kiểm chứng: không có overlap footprint/source rò rỉ giữa development và holdout.
- [ ] 4. Viết data contract. File: `schemas/campaign.schema.json`, `src/similitude/campaign_models.py`. Xong khi: unit/baseline/provenance bắt buộc; unknown xử lý rõ. Kiểm chứng: schema rejects dữ liệu thiếu đơn vị hoặc nguồn bắt buộc.
- [ ] 5. Audit catalog khả dụng. File: `config/test_sites.yaml`, `config/facilities.yaml`, `docs/data_availability.md`. Xong khi: mỗi shortlist có footprint, catalog data, ngày kiểm tra, operational status và lý do unknown. Kiểm chứng: xem trực tiếp nguồn chính thức, không suy permit từ bản đồ đường.
- [ ] 6. Terrain đa tỷ lệ. File: `src/similitude/descriptors/terrain.py`, `scripts/build_task_terrain.py`. Xong khi: baseline thống nhất, no-data/mask/CRS có kiểm tra, route geometry có giới hạn rõ. Kiểm chứng: analytical surface + khảo sát/DTM ngoài development; audit rock features theo độ phân giải thực.
- [ ] 7. L2 time-window và light setup. File: `src/similitude/descriptors/astro.py`, `src/similitude/lighting.py`, `scripts/build_lighting_windows.py`. Xong khi: trả run window có thời lượng và hướng tuyến, phân biệt geometry/radiometry. Kiểm chứng: ephemeris độc lập và shadow test có ground truth; timezone/azimuth/near-field tests.
- [ ] 8. Coverage engine. File: `src/similitude/coverage.py`, `config/scenarios/`. Xong khi: joint coverage, missing mandatory cases và unknown đều minh bạch. Kiểm chứng: fixture mà marginal coverage cao nhưng joint coverage bằng 0; không cộng sai giữa các nơi/thời điểm.
- [ ] 9. Campaign selection. File: `src/similitude/campaign.py`, `scripts/build_campaign.py`. Xong khi: đưa trade-off khả thi và no-solution khi không đủ điều kiện. Kiểm chứng: exhaustive optimum cho bài nhỏ; so baseline trên holdout cùng budget; không tuyên bố tối ưu toàn cục nếu dùng heuristic.
- [ ] 10. Reconnaissance và facility mapping. File: `src/similitude/reconnaissance.py`, `config/test_measurements.yaml`. Xong khi: mỗi gap có phép đo/điều kiện thử, quyết định có thể thay đổi và nguồn capability. Kiểm chứng: case unknown soil không sinh rover-safe claim; không tự xác nhận booking facility.
- [ ] 11. Evidence pack. File: `scripts/export_campaign.py`, `docs/templates/campaign_report.md`, `web/data/campaigns/`. Xong khi: report, GeoJSON, JSON manifest tái lập được từ input. Kiểm chứng: trace một claim từ PDF/HTML về input hash; report không cũ hơn config.
- [ ] 12. Website workflow. File: `web/index.html`, `web/app.js`, `web/style.css`, `web/evidence.html`. Xong khi: guided case → brief → compare → campaign → export, có ảnh thật/scale và progressive disclosure. Kiểm chứng: browser end-to-end, keyboard, mobile, empty/error states; số trên UI khớp pack.
- [ ] 13. Benchmark + user study. File: `scripts/evaluate_campaign.py`, `docs/validation_v2_report.md`, `docs/user_study.md`. Xong khi: publish cả kết quả không thuận lợi, uncertainty và pilot limitations. Kiểm chứng: người không xây score review mù; endpoints đúng protocol.
- [ ] 14. Mars terrain case. File: `config/scenarios/mars_navigation.yaml`, `scripts/build_mars_terrain.py`, `web/data/campaigns/`. Xong khi: dùng Mars DTM/target riêng và output thật; không phụ thuộc “cứu” M1. Kiểm chứng: unit/baseline, controls và coverage theo Mars profile.
- [ ] 15. Hồ sơ trình bày. File: `docs/project_page.md`, `docs/slides_draft.md`, `docs/video_script.md`. Xong khi: một kỹ sư, một quyết định, một kết quả đo được, một giới hạn rõ. Kiểm chứng: mọi số truy được về benchmark. Kiểm tra thể lệ chính thức tại thời điểm nộp; chưa xác nhận lại quy định SI/thời hạn trong phiên này.

## Edge-cases

- Không có site đạt constraint: xuất unmet requirements và đề nghị khảo sát/facility; không nới threshold tự động.
- Chỉ có coarse DEM: cho regional screening; không sinh boulder-scale verdict hoặc route safety.
- Site có match đẹp nhưng thiếu quyền tiếp cận: vẫn có giá trị nghiên cứu, chưa là campaign feasible.
- Bổ sung một site chỉ lặp lại tình huống đã cover: marginal coverage gain phải bằng 0.
- Requirement hard thiếu dữ liệu: campaign chưa đủ bằng chứng; không renormalize để điểm cao hơn.
- Thay weight hoặc footprint làm đổi lựa chọn: hiển thị sensitivity, không giấu sau số trung bình.
- Time window tự nhiên quá ngắn hoặc weather không chắc: trả contingency/unknown, không coi astronomical window là thời gian sử dụng bảo đảm.
- Chưa có ngân sách thực: cho so tương đối và khoảng estimate, không công bố tiết kiệm USD giả.
- Metadata target sai (ví dụ tên rim nhưng polygon nằm trên inner wall): chặn narrative sai bằng kiểm tra geometry trước scoring.
- Muốn thử lực kéo, bụi hoặc khoan: mở task profile riêng với phép đo và model được validate; không suy từ navigation coverage.

## Câu hỏi mở

Các lựa chọn mặc định ở trên đủ để bắt đầu P0; không cần trì hoãn kế hoạch để hỏi lại người dùng.

1. Đội có tiếp cận được rover/camera và người làm test để có V3/V6 không? Nếu không, scope claim dừng ở decision support + simulation; không đổi nhãn thành field validated.
2. Polygon nào có dữ liệu độ phân giải phù hợp ở cả target và Earth? Quyết định sau data availability audit, không chọn chỉ vì ảnh đẹp.
3. Bài thi đòi mức bao phủ Moon/Mars cụ thể thế nào? Đối chiếu nguyên văn challenge/guide hiện hành, không dựa hoàn toàn vào ABOUT.md.
4. Kế hoạch này thay đổi trọng tâm DESIGN cũ: từ toàn cầu/bốn lens sang campaign/task. Cần ghi quyết định thiết kế khi chuyển sang triển khai; không giả vờ đây chỉ là sửa giao diện.
5. Vì user bỏ ràng buộc công sức/thời gian, roadmap lấy research gates làm mốc. Không ngầm giữ lịch 48 giờ trong PLAN cũ hoặc hứa xong trong ngày.

## Nhật ký

- 2026-11-15 · Codex · Đọc đánh giá, AGENTS, PLAN/DESIGN, README, báo cáo validation, protocol và HTML/JS; tra nguồn chính thức; viết đề xuất này. Chưa sửa application code, dữ liệu hay kết quả khoa học. `ruff check . --no-cache`: PASS. `python -m pytest -q -p no:cacheprovider`: không chạy được collection vì Python hiện tại thiếu `numpy`; chưa xác nhận test suite pass.

Nguồn chính, truy cập 15/11/2026 (nội dung lịch sử của facility/mission không tự chứng minh availability hiện tại):

- [S1 — NASA/JPL ERNEST field testing, 2026](https://www.nasa.gov/solar-system/moon/nasa-testing-advanced-capabilities-for-moon-mars-rovers/).
- [S2 — NASA, South Pole Lunar Lighting Studies for Driving Exploration on the Lunar Surface](https://ntrs.nasa.gov/api/citations/20240011393/downloads/Lighiting%20Study%20IEEE%20Paper%20FINAL-1.pdf).
- [S3 — NASA Ames Lunar Lab and Regolith Testbeds](https://www.nasa.gov/centers-and-facilities/ames/the-lunar-lab-and-regolith-testbeds/).
- [S4 — NASA Glenn Planetary Exploration Test Facilities](https://www.nasa.gov/centers-and-facilities/glenn/planetary-exploration-test-facilities/).
- [S5 — NASA PRC FAQ for ROSES](https://science.nasa.gov/researchers/sara/faqs/prc-faq-roses/).
- [S6 — USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services).
- [S7 — HiRISE Jezero DTM and orthoimages](https://www.uahirise.org/dtm/ESP_048842_1985).
