# ZK_Draw — Phần mềm chú thích màn hình cho Linux

Phần mềm vẽ/chú thích lên màn hình nhẹ, thay thế **IPEVO Annotator** trên
Ubuntu 24.04. Viết bằng Python + **PySide6 (Qt6, giấy phép LGPL — hợp lệ cho
mục đích dùng nội bộ, không vướng bản quyền)**. Chạy tốt cùng Bottles/iDIGI.

Ba chức năng đúng như yêu cầu: **Vẽ lên màn hình**, **Bảng trắng**, **Thu nhỏ**.

---

## Tính năng

- **Vẽ lên màn hình**: lớp phủ trong suốt để vẽ đè lên mọi ứng dụng đang mở.
  Nhấn lại vào nút bút để chuyển sang **thao tác máy tính bình thường**
  (lớp phủ cho chuột đi xuyên qua nhưng nét vẽ vẫn hiển thị).
- **Bảng trắng**: nền trắng toàn màn hình để viết.
- **Bộ công cụ vẽ**: bút, bảng màu chọn sẵn, 4 cỡ nét, tẩy (3 cỡ),
  xóa hết, hoàn tác (undo), làm lại (redo).
- **Thanh công cụ kéo được**: giữ và kéo chữ **ZK_Draw** để di chuyển cả
  thanh công cụ; bảng công cụ đi theo.
- **Thu nhỏ**: nút mũi tên ở dưới cùng thu gọn toàn bộ công cụ về một handle nhỏ.
- Hỗ trợ **bút cảm ứng / bảng vẽ / bút doc-cam** (tablet events).
- Đa màn hình, DPI cao.

---

## Tải về & Cài đặt (Ubuntu 24.04)

```bash
# 1. Tải mã nguồn (nếu chưa có git: sudo apt install -y git)
git clone https://github.com/likemoue/ZK_Draw.git
cd ZK_Draw

# 2. Cài đặt (cần sudo để cài thư viện Qt)
chmod +x install.sh run.sh
./install.sh
```

Không có git? Tải ZIP:

```bash
wget https://github.com/likemoue/ZK_Draw/archive/refs/heads/main.zip
unzip main.zip && cd ZK_Draw-main
chmod +x install.sh run.sh && ./install.sh
```

Script sẽ: cài thư viện hệ thống cho Qt (xcb), tạo môi trường ảo `.venv`,
cài PySide6, và thêm mục **ZK_Draw** vào menu ứng dụng.

### Chạy

```bash
./run.sh
```

Hoặc mở từ menu ứng dụng và tìm **ZK_Draw**.

> `run.sh` tự đặt `QT_QPA_PLATFORM=xcb` để chạy qua X11/XWayland — cần thiết để
> lớp phủ trong suốt, luôn nổi trên cùng và cho-chuột-đi-xuyên hoạt động ổn định.

---

## Hướng dẫn sử dụng

Khi mở lên bạn thấy thanh công cụ dọc nhỏ nổi ở góc trái:

| Nút | Chức năng |
|-----|-----------|
| **ZK_Draw** (trên cùng) | Giữ & kéo để di chuyển cả thanh công cụ |
| ✏️ Bút | Bật chế độ **vẽ lên màn hình** |
| 🖼️ Bảng | Bật **bảng trắng** |
| ▲ Mũi tên (dưới cùng) | **Thu nhỏ** toàn bộ công cụ |

Khi bật *Vẽ lên màn hình* hoặc *Bảng trắng*, bảng công cụ hiện ra bên cạnh:

- **Bút**: chọn để vẽ. **Nhấn lại vào bút** → dùng máy tính bình thường.
- **Tẩy**: chọn để xóa nét; chọn cỡ tẩy ở nhóm 3 chấm bên phải.
- **Bảng màu**: các ô màu chọn sẵn (chọn màu là tự chuyển về bút).
- **Cỡ nét**: 4 chấm to nhỏ dần.
- 🗑️ **Xóa hết** — xóa toàn bộ nét đã vẽ (vẫn hoàn tác được).
- ↶ **Hoàn tác** / ↷ **Làm lại**.

### Phím tắt (khi lớp vẽ đang được chọn)

| Phím | Tác dụng |
|------|----------|
| `Ctrl` + `Z` | Hoàn tác |
| `Ctrl` + `Y` / `Ctrl`+`Shift`+`Z` | Làm lại |
| `Delete` | Xóa hết |
| `Esc` | Chuyển về "dùng máy tính bình thường" |

Chuột phải vào chữ **ZK_Draw** → **Thoát ZK_Draw**.

---

## Ghi chú kỹ thuật

- **Wayland vs X11**: Ubuntu 24.04 mặc định chạy Wayland. Lớp phủ chú thích
  cần chạy qua **X11/XWayland**; `run.sh` đã tự xử lý. Nếu bạn dùng phiên
  X11 thuần thì càng chạy tốt.
- **Biểu tượng khay hệ thống (tray)**: GNOME mặc định không hiện tray. Nếu
  muốn có, cài extension **AppIndicator** (`gnome-shell-extension-appindicator`).
  Không có tray cũng không sao — điều khiển chính là thanh công cụ nổi.
- Nếu Qt báo lỗi thiếu `libxcb-cursor0`, chạy:
  `sudo apt-get install -y libxcb-cursor0`.

---

## Cấu trúc mã nguồn

```
ZK_Draw/
├── main.py                # điểm khởi chạy
├── run.sh / install.sh    # script chạy & cài đặt
├── requirements.txt
├── zk-draw.desktop.in     # mẫu mục menu ứng dụng
├── assets/                # icon ứng dụng
└── zk_draw/
    ├── app.py             # khởi tạo QApplication
    ├── controller.py      # điều phối các cửa sổ
    ├── toolbar.py         # thanh công cụ chính (dọc) + kéo thả
    ├── tools_panel.py     # bảng công cụ vẽ
    ├── windows.py         # cửa sổ toàn màn hình (overlay & bảng trắng)
    ├── canvas.py          # bề mặt vẽ + undo/redo
    ├── widgets.py         # nút/ô màu/chấm cỡ nét dùng chung
    ├── cursors.py         # con trỏ xem trước cỡ bút
    ├── icons.py           # icon vector (không cần file ảnh)
    ├── styles.py          # QSS
    └── config.py          # màu, cỡ, chủ đề
```

Muốn đổi bảng màu / cỡ nét: sửa `zk_draw/config.py`.

---

## Giấy phép

Mã nguồn ZK_Draw: bạn tự do dùng và chỉnh sửa nội bộ.
Phụ thuộc **PySide6** theo giấy phép **LGPLv3** — dùng được cho mục đích
thương mại/nội bộ mà không phải mở mã nguồn ứng dụng của bạn.
