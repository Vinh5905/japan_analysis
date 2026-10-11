"""Small HTML cards and mobile inline keyboards for the private controller."""

from datetime import datetime
from html import escape
import re
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Ho_Chi_Minh")
VIEWS = {
    "home",
    "help",
    "run_crawl",
    "status",
    "schedule",
    "history",
    "total",
    "areas",
    "refresh_areas",
}


def text(value, limit=350):
    value = str(value if value is not None else "chưa có")
    return escape(value[:limit] + ("…" if len(value) > limit else ""))


def number(value):
    return f"{int(value or 0):,}".replace(",", ".")


def timestamp(value):
    if not value or value == "chưa có":
        return "chưa có"
    try:
        return (
            datetime.fromisoformat(str(value))
            .astimezone(ZONE)
            .strftime("%d/%m/%Y %H:%M")
        )
    except ValueError:
        return text(value, 100)


def button(label, action):
    if not 1 <= len(action.encode("utf-8")) <= 64:
        raise ValueError("Telegram callback data must fit 64 UTF-8 bytes")
    return {"text": label, "callback_data": action}


def keyboard(view="home", nonce=None):
    home = button("🏠 Menu", "view:home")
    if nonce:
        rows = [
            [button("✅ Xác nhận chạy", "run:" + nonce)],
            [button("✕ Hủy", "cancel:" + nonce)],
        ]
    elif view == "home":
        rows = [
            [
                button("▶️ Chạy crawler", "view:run_crawl"),
                button("❔ Hướng dẫn", "view:help"),
            ],
            [
                button("📡 Trạng thái", "view:status"),
                button("🗓 Lịch chạy", "view:schedule"),
            ],
            [button("🕘 Lịch sử", "view:history"), button("📊 Tổng URL", "view:total")],
            [
                button("📍 Khu vực", "view:areas"),
                button("↻ Đồng bộ ward", "view:refresh_areas"),
            ],
        ]
    elif view == "help":
        rows = [[home]]
    else:
        rows = [[button("↻ Cập nhật", "view:" + view), home]]
    return {"inline_keyboard": rows}


def card(title, sections, now, markup):
    footer = datetime.fromtimestamp(now, ZONE).strftime("%H:%M · %d/%m/%Y")
    message = "\n\n".join(
        [f"<b>{title}</b>", *sections, f"🕒 {footer} · Giờ Việt Nam (UTC+7)"]
    )
    return message, markup


def home(now):
    return card(
        "🏠 SUUMO · Điều khiển crawler",
        [
            "Theo dõi crawler, lịch chạy và kết quả tại đây.",
            "<b>Chạy thủ công</b>\nBấm Chạy crawler để xem thông tin và xác nhận trước khi chạy.",
            "Chọn chức năng bên dưới ↓",
        ],
        now,
        keyboard(),
    )


def help_card(commands, now):
    return card(
        "❔ SUUMO · Hướng dẫn",
        [
            "\n".join(f"/{key} — {text(description)}" for key, description in commands),
            "<b>Cách chạy</b>\nChạy crawler → Chọn ward → Xác nhận chạy. Nút xác nhận dùng một lần, hết hạn sau 2 phút.",
            "<b>Cách đọc số liệu</b>\nMỗi lượt một ward; mục tiêu 10.000 URL/ngày, tối đa 5 lượt tự động gồm cả lỗi VPN. Thủ công được ưu tiên và có thể vượt hạn mức. Lượt tính theo ngày bắt đầu, giờ Việt Nam. Nghỉ 1 giờ từ cleanup hoàn tất. Lịch sử ghi nhận cả pipeline. Tổng URL gồm thành công, thất bại và xử lý lại; cũng tính phần đã xử lý của lượt đang chạy.",
        ],
        now,
        keyboard("help"),
    )


def confirmation(source, values, nonce, now):
    def limit(key):
        value = values.get(key, "0")
        return "Tất cả" if value == "0" else text(value, 30)

    return card(
        "▶️ SUUMO · Xác nhận chạy",
        [
            "Crawler đang rảnh. Anh muốn bắt đầu một lượt crawl mới?",
            "<b>Các bước sẽ chạy</b>\n🔐 Kiểm tra VPN\n🔎 Tìm links\n📥 Tải HTML\n🧩 Parse dữ liệu\n🔐 Tắt và kiểm tra VPN",
            f"<b>Phạm vi</b>\nSource: {text(source)} · Chạy thủ công\nGiới hạn HTML: {limit('SUUMO_HTML_LINK_LIMIT')}\nGiới hạn parse: {limit('SUUMO_PAGE_TASK_LIMIT')}",
            "⏳ Xác nhận có hiệu lực 2 phút, sử dụng một lần.\nNếu crawler bắt đầu chạy trước, bot sẽ báo trạng thái.",
        ],
        now,
        keyboard(nonce=nonce),
    )


def status(fields, now):
    running = fields.get("Crawler") == "đang chạy"
    pending = fields.get("Yêu cầu Telegram")
    headline = (
        "🔵 Đang chạy"
        if running
        else "🟠 Đang chờ khởi động"
        if pending
        else "🟢 Sẵn sàng"
    )
    step_label = "Bước hiện tại" if running else "Bước gần nhất"
    vpn = str(fields.get("VPN", "chưa có"))
    if vpn.startswith("inactive"):
        vpn = "Đã tắt"
    result = fields.get("Kết quả gần nhất", "chưa có")
    result = {
        "success": "Thành công",
        "exit-code": "Thất bại",
        "timeout": "Quá thời gian",
    }.get(result, result)
    sections = [
        f"<b>{headline}</b>\n{step_label}: {text(fields.get(step_label))}\nLượt chạy: {text(fields.get('Lượt chạy'))}\nWard: {text(fields.get('Khu vực'))}\nHôm nay: {text(fields.get('Hôm nay'))}",
        f"🔐 VPN: {text(vpn)}\nFile: {text(fields.get('Cấu hình VPN'))}\nKết quả gần nhất: {text(result)}",
        f"🗓 Lịch: {text(fields.get('Lịch'))}\nLần kế tiếp: {timestamp(fields.get('Lần kế tiếp'))}",
    ]
    if pending:
        sections.append("⏳ Ward đang chờ: " + text(pending))
    return card("📡 SUUMO · Trạng thái", sections, now, keyboard("status"))


def schedule(fields, now):
    active = fields.get("Timer") == "đang bật"
    calendar = str(fields.get("Lịch thực tế", "chưa có"))
    # systemd includes last/next metadata around the actual calendar expression.
    match = re.search(r"OnCalendar=(.*?)(?:\s*;|\s*})", calendar)
    if match:
        calendar = match.group(1)
    boot = {
        "enabled": "Có",
        "disabled": "Không",
        "static": "Theo cấu hình systemd",
    }.get(fields.get("Tự bật khi boot"), "chưa có")
    remaining = fields.get("Còn lại", "chưa có")
    minutes = re.fullmatch(r"(\d+) phút", str(remaining))
    if minutes:
        days, hours = divmod(int(minutes.group(1)), 1440)
        hours, minutes_left = divmod(hours, 60)
        remaining = (
            " ".join(
                f"{n} {unit}"
                for n, unit in [(days, "ngày"), (hours, "giờ"), (minutes_left, "phút")]
                if n
            )
            or "Dưới 1 phút"
        )
    sections = [
        f"<b>{'🟢 Lịch đang bật' if active else '🟠 ' + text(fields.get('Timer', fields.get('Lịch', 'Lịch chưa có')))}</b>",
        f"Điều phối: {text(fields.get('Điều phối'))}",
        f"<b>Lần chạy kế tiếp</b>\n{timestamp(fields.get('Lần kế tiếp (giờ Việt Nam)'))}\nCòn lại: {text(remaining)}",
        f"<b>Cấu hình trên VPS</b>\nLịch: {text(calendar, 250)}\nTimezone: {text(fields.get('Timezone VPS'))}\nTự bật khi khởi động VPS: {boot}",
    ]
    return card("🗓 SUUMO · Lịch chạy", sections, now, keyboard("schedule"))


def history(rows, source, now):
    sections = []
    for row in rows[:5]:
        state = row.get("pipeline_status") or (
            "đã kết thúc HTML · pipeline cũ chưa xác định"
            if row["finished_at"]
            else "đang tải HTML"
        )
        icon = "🔵" if not row["finished_at"] else "🟠" if row["html_failed"] else "🟢"
        origin = {"manual": "thủ công", "schedule": "theo lịch"}.get(
            row["created_by"], row["created_by"]
        )
        sections.append(
            f"<b>{icon} #{text(row['run_id'], 30)} · {timestamp(row['created_at'])}</b>\n"
            f"Ward: {text((row.get('area_snapshot') or {}).get('display_name'))}\n"
            f"VPN: {text((row.get('vpn_snapshot') or {}).get('filename'))}\n"
            f"{text(state)} · {text(origin, 60)}\n"
            f"URL đã xử lý: <b>{number(row['total_urls'])}</b>\n"
            f"HTML thành công: {number(row['html_success'])} · thất bại: {number(row['html_failed'])}"
        )
    if not sections:
        sections.append("Chưa có lượt tải HTML cho source này.")
    sections.append(
        f"Source {text(source)} · Tối đa 5 lượt gần nhất.\nBao gồm lỗi trước HTML và cleanup."
    )
    return card("🕘 SUUMO · Lịch sử pipeline", sections, now, keyboard("history"))


def total(data, source, now):
    return card(
        "📊 SUUMO · Tổng URL đã xử lý",
        [
            f"URL đã xử lý: <b>{number(data['total_urls'])}</b>\nLượt crawl: <b>{number(data['runs'])}</b>",
            f"Hôm nay: <b>{number(data.get('today', {}).get('total_urls'))} / 10.000 URL</b>\nLượt đã dùng: {number(data.get('today', {}).get('runs'))} / 5",
            f"<b>Phạm vi thống kê</b>\nToàn bộ lịch sử của source {text(source)}.",
            "Gồm URL thành công, thất bại, xử lý lại và phần đã xử lý của lượt đang chạy. Một URL được xử lý ở lượt khác được tính thêm một lần.",
        ],
        now,
        keyboard("total"),
    )


def notice(title, description, now, view="status"):
    return card(title, [description], now, keyboard(view))


def areas(rows, select, page, now):
    page = max(0, min(page, max(0, (len(rows) - 1) // 5)))
    shown = rows[page * 5 : (page + 1) * 5]
    sections, buttons = [], []
    mode = "run" if select else "list"
    for area in shown:
        last = (
            timestamp(area["last_run"]).split(" ")[0]
            if area["last_run"]
            else "Chưa chạy"
        )
        sections.append(
            f"<b>{text(area['display_name'])}</b> · {number(area['runs'])} lượt · {last}"
        )
        if select:
            buttons.append([button(area["display_name"], f"pick:{area['area_id']}")])
    nav = []
    if page:
        nav.append(button("← Trước", f"page:{mode}:{page - 1}"))
    if (page + 1) * 5 < len(rows):
        nav.append(button("Sau →", f"page:{mode}:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([button("🏠 Menu", "view:home")])
    sections.append(
        f"大阪府 · 大阪市 · Trang {page + 1}/{max(1, (len(rows) + 4) // 5)}"
    )
    return card(
        "📍 SUUMO · " + ("Chọn ward để chạy" if select else "Danh mục khu vực"),
        sections or ["Chưa có khu vực"],
        now,
        {"inline_keyboard": buttons},
    )


def area_confirmation(area, values, nonce, now, pending=None, pipeline=None):
    address = " · ".join(
        str(area[k])
        for k in ("prefecture", "district", "municipality", "ward")
        if area.get(k)
    )
    sections = [
        f"<b>{text(area['display_name'])}</b>\n{text(address)}\nMột ward · sc {text(area['sc'])}",
        f"HTML: {text(values.get('SUUMO_HTML_LINK_LIMIT') or '0')} (0 = tất cả)\nParse: {text(values.get('SUUMO_PAGE_TASK_LIMIT') or '0')}",
        "🔐 VPN → 🔎 Links → 📥 HTML → 🧩 Parse → 🔐 Cleanup",
        "Xác nhận dùng một lần trong 2 phút. Nếu bận, ward được xếp chờ sau cleanup. Thủ công được chạy vượt hạn mức ngày.",
    ]
    if pending:
        sections.append(
            "Đang chờ: "
            + text(pending["area"]["display_name"])
            + "; yêu cầu mới sẽ không thay thế."
        )
    if pipeline and pipeline.get("status") in {"running", "launching"}:
        sections.append(
            "Đang chạy: " + text(pipeline.get("area", {}).get("display_name"))
        )
    return card("▶️ SUUMO · Xác nhận ward", sections, now, keyboard(nonce=nonce))
