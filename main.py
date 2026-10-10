"""背诵单词 — 圆角高级白界面桌面程序。"""

from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

from wordbook.errors import get_error_count, record_wrong
from wordbook.parser import match_chinese, match_english, parse_input_text
from wordbook.storage import (
    RECORDS_DIR_NAME,
    app_base_dir,
    collection_dir,
    list_wordbooks,
    load_wordbook,
    sanitize_filename,
    save_wordbook,
)


def resource_path(*parts: str) -> Path:
    """开发目录或 PyInstaller 解包目录下的资源路径。"""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


def load_ctk_image(filename: str, size: tuple[int, int]) -> ctk.CTkImage | None:
    path = resource_path("assets", filename)
    if not path.exists():
        return None
    try:
        img = Image.open(path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except OSError:
        return None

# —— 视觉：柔白 + 圆角 + 克制高级感 ——
COLORS = {
    "bg": "#F4F6F8",
    "card": "#FFFFFF",
    "ink": "#1A1D21",
    "muted": "#6B7280",
    "line": "#E6E9EE",
    "accent": "#2F6FED",
    "accent_hover": "#2558C7",
    "soft": "#EEF3FC",
    "success": "#1F8A5B",
    "danger": "#C23B3B",
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class RoundedCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["card"])
        kwargs.setdefault("corner_radius", 22)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["line"])
        super().__init__(master, **kwargs)


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("背诵单词")
        self.geometry("520x680")
        self.minsize(460, 600)
        self.configure(fg_color=COLORS["bg"])
        self._set_window_icon()

        collection_dir()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew", padx=28, pady=28)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames: dict[str, ctk.CTkFrame] = {}
        for name, cls in {
            "home": HomeFrame,
            "input": InputFrame,
            "practice": PracticeFrame,
        }.items():
            frame = cls(self.container, self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show("home")

    def _set_window_icon(self) -> None:
        candidates = [
            resource_path("assets", "app_icon.ico"),
            app_base_dir() / "assets" / "app_icon.ico",
        ]
        for icon in candidates:
            if icon.exists():
                try:
                    self.iconbitmap(str(icon))
                    return
                except Exception:
                    continue

    def show(self, name: str, **kwargs) -> None:
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            frame.on_show(**kwargs)
        frame.tkraise()


class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)

        hero = RoundedCard(self)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero,
            text="背诵单词",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=28, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(26, 4))

        ctk.CTkLabel(
            hero,
            text="安静练习 · 本地词库 · 输入默写",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 24))

        card = RoundedCard(self)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="选择目录",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            text_color=COLORS["muted"],
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(26, 8))

        self.book_var = ctk.StringVar(value="")
        self.combo = ctk.CTkComboBox(
            card,
            variable=self.book_var,
            values=["（暂无词库）"],
            state="readonly",
            height=44,
            corner_radius=14,
            border_width=1,
            border_color=COLORS["line"],
            fg_color=COLORS["soft"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["card"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=14),
            dropdown_font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
        )
        self.combo.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 22))

        buttons = [
            ("背诵单词", "memorize"),
            ("背诵英文", "recite_en"),
            ("背诵中文", "recite_zh"),
            ("录入单词", "input"),
        ]
        for i, (label, mode) in enumerate(buttons):
            is_primary = mode == "input"
            btn = ctk.CTkButton(
                card,
                text=label,
                height=52,
                corner_radius=16,
                font=ctk.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold"),
                fg_color=COLORS["accent"] if is_primary else COLORS["soft"],
                hover_color=COLORS["accent_hover"] if is_primary else "#E4EAF6",
                text_color="#FFFFFF" if is_primary else COLORS["ink"],
                border_width=0 if is_primary else 1,
                border_color=COLORS["line"],
                command=(
                    (lambda m=mode: self.open_practice(m))
                    if mode != "input"
                    else (lambda: self.app.show("input"))
                ),
            )
            btn.grid(row=2 + i, column=0, sticky="ew", padx=28, pady=(0, 12))

        ctk.CTkLabel(
            card,
            text=f"词库保存在程序同级「{RECORDS_DIR_NAME}」文件夹",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=11),
            text_color=COLORS["muted"],
        ).grid(row=6, column=0, sticky="w", padx=28, pady=(8, 24))

    def on_show(self, select: str | None = None, **_) -> None:
        names = list_wordbooks()
        if names:
            self.combo.configure(values=names)
            if select and select in names:
                self.book_var.set(select)
            elif self.book_var.get() not in names:
                self.book_var.set(names[0])
        else:
            self.combo.configure(values=["（暂无词库）"])
            self.book_var.set("（暂无词库）")

    def open_practice(self, mode: str) -> None:
        name = self.book_var.get()
        if not name or name == "（暂无词库）":
            messagebox.showinfo("提示", "请先选择词库，或先去录入单词。")
            return
        pairs = load_wordbook(name)
        if pairs is None:
            messagebox.showerror("提示", "词库无法读取。")
            return
        if not pairs:
            messagebox.showinfo("提示", "当前词库没有有效词条，请先录入。")
            return
        self.app.show("practice", mode=mode, book_name=name, pairs=pairs)


class InputFrame(ctk.CTkFrame):
    def __init__(self, master, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        head = RoundedCard(self)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        head.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            head,
            text="返回",
            width=72,
            height=36,
            corner_radius=12,
            fg_color=COLORS["soft"],
            hover_color="#E4EAF6",
            text_color=COLORS["ink"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            command=lambda: self.app.show("home"),
        ).grid(row=0, column=0, padx=(20, 10), pady=16)

        ctk.CTkLabel(
            head,
            text="录入单词",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=1, sticky="w", pady=16)

        body = RoundedCard(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            body,
            text="粘贴或输入纯文本，程序会自动区分英文与中文并配对。\n推荐：apple 苹果",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLORS["muted"],
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 10))

        self.text = ctk.CTkTextbox(
            body,
            corner_radius=16,
            border_width=1,
            border_color=COLORS["line"],
            fg_color="#FAFBFC",
            text_color=COLORS["ink"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
        )
        self.text.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))

        ctk.CTkButton(
            body,
            text="完成录入",
            height=48,
            corner_radius=16,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.finish_input,
        ).grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))

    def on_show(self, **_) -> None:
        pass

    def finish_input(self) -> None:
        raw = self.text.get("1.0", "end").strip()
        pairs, ignored = parse_input_text(raw)
        if not pairs:
            messagebox.showinfo("提示", "没有可配对的词条，请检查输入内容。")
            return
        if ignored:
            if not messagebox.askokcancel(
                "提示",
                f"已配对 {len(pairs)} 条，忽略落单片段 {ignored} 个。\n继续保存已配对部分？",
            ):
                return

        dialog = FilenameDialog(self, title="确认文件名")
        self.wait_window(dialog)
        if not dialog.result:
            return

        stem, err = sanitize_filename(dialog.result)
        if err or stem is None:
            messagebox.showwarning("提示", err or "文件名无效")
            return

        from wordbook.storage import wordbook_path

        path = wordbook_path(stem)
        if path.exists():
            if not messagebox.askyesno(
                "确认覆盖", f"文件「{stem}.md」已存在，是否覆盖？"
            ):
                return

        try:
            save_wordbook(stem, pairs)
        except ValueError as exc:
            messagebox.showwarning("提示", str(exc))
            return
        except OSError as exc:
            messagebox.showerror("错误", f"保存失败：{exc}")
            return

        messagebox.showinfo("完成", f"已保存 {len(pairs)} 条到「{stem}.md」")
        self.text.delete("1.0", "end")
        self.app.show("home", select=stem)


class FilenameDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str = "确认文件名") -> None:
        super().__init__(master)
        self.result: str | None = None
        self.title(title)
        self.geometry("440x320")
        self.minsize(440, 320)
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.update_idletasks()
        parent = master.winfo_toplevel()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - 440) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - 320) // 2
            self.geometry(f"440x320+{max(x, 40)}+{max(y, 40)}")
        except Exception:
            pass

        card = RoundedCard(self)
        card.pack(fill="both", expand=True, padx=22, pady=22)

        ctk.CTkLabel(
            card,
            text="为此次录入命名",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=COLORS["ink"],
        ).pack(anchor="w", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            card,
            text=f"将保存为「{RECORDS_DIR_NAME}」下的 md 文件",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            text_color=COLORS["muted"],
        ).pack(anchor="w", padx=24, pady=(0, 16))

        self.entry = ctk.CTkEntry(
            card,
            height=48,
            corner_radius=14,
            border_width=1,
            border_color=COLORS["line"],
            fg_color=COLORS["soft"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
            placeholder_text="例如：四单元单词",
        )
        self.entry.pack(fill="x", padx=24, pady=(0, 28))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda _e: self.confirm())

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkButton(
            row,
            text="取消",
            width=120,
            height=48,
            corner_radius=14,
            fg_color=COLORS["soft"],
            hover_color="#E4EAF6",
            text_color=COLORS["ink"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            row,
            text="确认保存",
            width=140,
            height=48,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold"),
            command=self.confirm,
        ).pack(side="right")

    def confirm(self) -> None:
        value = self.entry.get().strip()
        if not value:
            messagebox.showwarning("提示", "请输入文件名", parent=self)
            return
        self.result = value
        self.destroy()


class PracticeFrame(ctk.CTkFrame):
    MODE_TITLE = {
        "memorize": "背诵单词",
        "recite_en": "背诵英文",
        "recite_zh": "背诵中文",
    }

    def __init__(self, master, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.mode = "recite_en"
        self.book_name = ""
        self.pairs = []
        self.index = 0
        self.awaiting_continue = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        head = RoundedCard(self)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        head.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            head,
            text="返回",
            width=72,
            height=36,
            corner_radius=12,
            fg_color=COLORS["soft"],
            hover_color="#E4EAF6",
            text_color=COLORS["ink"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            command=lambda: self.app.show("home"),
        ).grid(row=0, column=0, padx=(20, 10), pady=16)

        self.title_label = ctk.CTkLabel(
            head,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=COLORS["ink"],
        )
        self.title_label.grid(row=0, column=1, sticky="w")

        self.progress_label = ctk.CTkLabel(
            head,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLORS["muted"],
        )
        self.progress_label.grid(row=0, column=2, padx=20)

        body = RoundedCard(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self.body = body

        self.prompt_hint = ctk.CTkLabel(
            body,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13),
            text_color=COLORS["muted"],
        )
        self.prompt_hint.grid(row=0, column=0, sticky="w", padx=28, pady=(28, 8))

        # 上方英文（背诵单词模式）/ 题目提示（默写模式）
        self.prompt_label = ctk.CTkLabel(
            body,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=32, weight="bold"),
            text_color=COLORS["ink"],
            wraplength=400,
            justify="center",
        )
        self.prompt_label.grid(row=1, column=0, padx=28, pady=(16, 8))

        # 下方中文（仅背诵单词模式显示）
        self.meaning_label = ctk.CTkLabel(
            body,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=24),
            text_color=COLORS["accent"],
            wraplength=400,
            justify="center",
        )
        self.meaning_label.grid(row=2, column=0, padx=28, pady=(8, 28))

        # 完成页庆祝图
        self.finish_image = ctk.CTkLabel(body, text="")
        self.finish_image.grid(row=3, column=0, padx=28, pady=(4, 12))
        self.finish_image.grid_remove()
        self._img_finish_en = load_ctk_image("finish_en.jpg", (320, 200))
        self._img_finish_zh = load_ctk_image("finish_zh.jpg", (320, 200))

        self.answer = ctk.CTkEntry(
            body,
            height=48,
            corner_radius=16,
            border_width=1,
            border_color=COLORS["line"],
            fg_color=COLORS["soft"],
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=16),
            placeholder_text="在此输入答案",
        )
        self.answer.grid(row=4, column=0, sticky="ew", padx=28, pady=(0, 12))
        self.answer.bind("<Return>", lambda _e: self.on_primary())

        self.feedback = ctk.CTkLabel(
            body,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=14),
            text_color=COLORS["muted"],
            wraplength=400,
            justify="left",
        )
        self.feedback.grid(row=5, column=0, sticky="w", padx=28, pady=(4, 12))

        nav = ctk.CTkFrame(body, fg_color="transparent")
        nav.grid(row=6, column=0, sticky="ew", padx=28, pady=(0, 12))
        nav.grid_columnconfigure(0, weight=1)
        nav.grid_columnconfigure(1, weight=1)

        self.prev_btn = ctk.CTkButton(
            nav,
            text="上一个",
            height=46,
            corner_radius=14,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
            fg_color=COLORS["soft"],
            hover_color="#E4EAF6",
            text_color=COLORS["ink"],
            border_width=1,
            border_color=COLORS["line"],
            command=self.go_prev,
        )
        self.prev_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.next_btn = ctk.CTkButton(
            nav,
            text="下一个",
            height=46,
            corner_radius=14,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
            fg_color=COLORS["soft"],
            hover_color="#E4EAF6",
            text_color=COLORS["ink"],
            border_width=1,
            border_color=COLORS["line"],
            command=self.go_next,
        )
        self.next_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.primary_btn = ctk.CTkButton(
            body,
            text="提交",
            height=48,
            corner_radius=16,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.on_primary,
        )
        self.primary_btn.grid(row=7, column=0, sticky="ew", padx=28, pady=(0, 28))

    def _apply_mode_layout(self, finished: bool = False) -> None:
        """背诵单词：只看词翻页；背诵英/中：输入默写。"""
        browse = self.mode == "memorize"
        if finished:
            self.meaning_label.grid_remove()
            self.answer.grid_remove()
            self.feedback.grid()
            self.primary_btn.grid()
            self.finish_image.grid()
            self.prompt_label.grid_configure(pady=(16, 8))
            return

        self.finish_image.grid_remove()
        self.finish_image.configure(image=None, text="")
        if browse:
            self.meaning_label.grid()
            self.answer.grid_remove()
            self.feedback.grid_remove()
            self.primary_btn.grid_remove()
            self.prompt_label.grid_configure(pady=(28, 8))
            self.meaning_label.grid_configure(pady=(8, 36))
        else:
            self.meaning_label.grid_remove()
            self.answer.grid()
            self.feedback.grid()
            self.primary_btn.grid()
            self.prompt_label.grid_configure(pady=(10, 24))

    def on_show(self, mode: str = "recite_en", book_name: str = "", pairs=None, **_) -> None:
        self.mode = mode
        self.book_name = book_name
        self.pairs = list(pairs or [])
        self.index = 0
        self.awaiting_continue = False
        self.title_label.configure(text=self.MODE_TITLE.get(mode, "练习"))
        self.answer.configure(state="normal")
        self.render_question()

    def _update_nav_buttons(self) -> None:
        total = len(self.pairs)
        if total == 0:
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            return
        at_end = self.index >= total
        self.prev_btn.configure(state="normal" if (at_end or self.index > 0) else "disabled")
        self.next_btn.configure(state="disabled" if at_end else "normal")

    def go_prev(self) -> None:
        if not self.pairs:
            return
        if self.index >= len(self.pairs):
            self.index = len(self.pairs) - 1
        elif self.index > 0:
            self.index -= 1
        else:
            return
        self.awaiting_continue = False
        self.answer.configure(state="normal")
        self.render_question()

    def go_next(self) -> None:
        if not self.pairs or self.index >= len(self.pairs):
            return
        en, zh = self.pairs[self.index]
        skipped = f"上一题答案：{en}  /  {zh}"
        if self.index >= len(self.pairs) - 1:
            self.index = len(self.pairs)
            self.awaiting_continue = False
            self.render_question()
            return
        self.index += 1
        self.awaiting_continue = False
        self.answer.configure(state="normal")
        self.render_question()
        # 默写模式跳过时提示答案；背诵单词本身已对照显示，无需再提示
        if self.mode != "memorize":
            self.feedback.configure(text=skipped, text_color=COLORS["muted"])

    def render_question(self) -> None:
        if self.index >= len(self.pairs):
            self._show_finished()
            return

        en, zh = self.pairs[self.index]
        total = len(self.pairs)
        self.progress_label.configure(text=f"{self.index + 1} / {total}")
        self.feedback.configure(text="", text_color=COLORS["muted"])
        self.answer.delete(0, "end")
        self.answer.configure(state="normal")
        self.primary_btn.configure(text="提交")
        self.awaiting_continue = False
        self._apply_mode_layout(finished=False)

        if self.mode == "memorize":
            self.prompt_hint.configure(text="对照记忆 · 上一个 / 下一个")
            self.prompt_label.configure(text=en)
            self.meaning_label.configure(text=zh)
        elif self.mode == "recite_en":
            self.prompt_hint.configure(text="根据中文，默写英文")
            self.prompt_label.configure(text=zh)
            self.meaning_label.configure(text="")
        else:
            self.prompt_hint.configure(text="根据英文，默写中文")
            self.prompt_label.configure(text=en)
            self.meaning_label.configure(text="")

        self._update_nav_buttons()
        if self.mode != "memorize":
            self.answer.focus_set()

    def _show_finished(self) -> None:
        self.prompt_hint.configure(text="本组已完成")
        self.prompt_label.configure(text="恭喜刷完")
        self.meaning_label.configure(text="")
        self.progress_label.configure(text=f"{len(self.pairs)} / {len(self.pairs)}")
        # 背诵中文用第三张图，其余完成页用第二张图
        if self.mode == "recite_zh":
            img = self._img_finish_zh
        else:
            img = self._img_finish_en
        if img is not None:
            self.finish_image.configure(image=img, text="")
        else:
            self.finish_image.configure(image=None, text="")
        self.feedback.configure(
            text=f"词库「{self.book_name}」已刷完",
            text_color=COLORS["success"],
        )
        self.answer.configure(state="disabled")
        self.primary_btn.configure(text="再来一遍")
        self.awaiting_continue = True
        self._finish_action = "restart"
        self._apply_mode_layout(finished=True)
        self._update_nav_buttons()

    def _error_tip(self, count: int) -> str:
        if count <= 0:
            return ""
        return f"背诵错误{count}次！"

    def on_primary(self) -> None:
        if self.mode == "memorize" and not self.awaiting_continue:
            return

        if self.awaiting_continue:
            action = getattr(self, "_finish_action", "next")
            if action == "restart":
                self.index = 0
                self.awaiting_continue = False
                self.answer.configure(state="normal")
                self.render_question()
            elif action == "next_after_wrong":
                self._advance_after_answer()
            return

        if self.index >= len(self.pairs):
            return

        user = self.answer.get()
        en, zh = self.pairs[self.index]

        if self.mode == "recite_en":
            ok = match_english(user, en)
            expected = en
        else:
            ok = match_chinese(user, zh)
            expected = zh

        if ok:
            count = get_error_count(self.book_name, en, zh)
            tip = self._error_tip(count)
            text = "正确" if not tip else f"正确\n{tip}"
            self.feedback.configure(text=text, text_color=COLORS["success"])
            self.after(700 if tip else 450, self._advance_after_answer)
        else:
            count = record_wrong(self.book_name, en, zh)
            tip = self._error_tip(count)
            self.feedback.configure(
                text=f"不正确。标准答案：{expected}\n{tip}",
                text_color=COLORS["danger"],
            )
            self.answer.configure(state="disabled")
            self.primary_btn.configure(text="下一题")
            self.awaiting_continue = True
            self._finish_action = "next_after_wrong"

    def _advance_after_answer(self) -> None:
        self.awaiting_continue = False
        self.index += 1
        self.render_question()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
