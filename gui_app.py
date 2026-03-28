#!/usr/bin/env python3
"""
НСПД Парсер - GUI приложение для Windows
Standalone приложение с графическим интерфейсом
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from typing import List
from datetime import datetime
import sys
import os

from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template


class NSPDParserGUI:
    """Главное окно приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title("НСПД Парсер - Кадастровые данные")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Переменные
        self.is_processing = False
        self.api_client = None

        # Создаем интерфейс
        self._create_widgets()

        # Центрируем окно
        self._center_window()

    def _center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """Создание виджетов интерфейса"""

        # Заголовок
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)

        ttk.Label(
            header_frame,
            text="🏘️ НСПД Парсер - Получение кадастровых данных",
            font=("Arial", 14, "bold")
        ).pack()

        ttk.Label(
            header_frame,
            text="Введите кадастровые номера (по одному на строку)",
            font=("Arial", 9)
        ).pack()

        # Разделитель
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # Область ввода номеров
        input_frame = ttk.LabelFrame(self.root, text="Кадастровые номера", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Текстовое поле для ввода
        self.text_input = scrolledtext.ScrolledText(
            input_frame,
            height=8,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.text_input.pack(fill=tk.BOTH, expand=True)

        # Placeholder текст
        self.placeholder_text = "Пример:\n77:05:0001016:22\n77:06:0002008:40\n77:01:0005016:3275"
        self.is_placeholder_active = True
        self.text_input.insert("1.0", self.placeholder_text)
        self.text_input.config(fg="gray")

        # Обработка placeholder
        self.text_input.bind("<FocusIn>", self._on_input_focus_in)
        self.text_input.bind("<FocusOut>", self._on_input_focus_out)
        self.text_input.bind("<Key>", self._on_input_key)

        # Обработка вставки (Ctrl+V / Cmd+V)
        self.text_input.bind("<Control-v>", self._on_paste)  # Windows/Linux
        self.text_input.bind("<Command-v>", self._on_paste)  # macOS

        # Кнопки управления
        buttons_frame = ttk.Frame(self.root, padding="10")
        buttons_frame.pack(fill=tk.X)

        self.btn_process = ttk.Button(
            buttons_frame,
            text="📥 Загрузить данные",
            command=self._on_process_click,
            style="Accent.TButton"
        )
        self.btn_process.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(
            buttons_frame,
            text="🗑️ Очистить",
            command=self._on_clear_click
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="❌ Выход",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=5)

        # Прогресс-бар
        self.progress = ttk.Progressbar(
            self.root,
            mode='determinate',
            length=300
        )
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        self.progress_label = ttk.Label(self.root, text="Готов к работе")
        self.progress_label.pack()

        # Разделитель
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # Область логов
        log_frame = ttk.LabelFrame(self.root, text="Лог выполнения", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _on_input_focus_in(self, event):
        """Удаление placeholder при фокусе"""
        if self.is_placeholder_active:
            self.text_input.delete("1.0", tk.END)
            self.text_input.config(fg="black")
            self.is_placeholder_active = False

    def _on_input_focus_out(self, event):
        """Возврат placeholder если поле пустое"""
        if not self.text_input.get("1.0", tk.END).strip():
            self.text_input.insert("1.0", self.placeholder_text)
            self.text_input.config(fg="gray")
            self.is_placeholder_active = True

    def _on_input_key(self, event):
        """Обработка нажатия клавиш - удаляет placeholder"""
        if self.is_placeholder_active and event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Command']:
            self.text_input.delete("1.0", tk.END)
            self.text_input.config(fg="black")
            self.is_placeholder_active = False

    def _on_paste(self, event):
        """Обработка вставки (Ctrl+V / Cmd+V)"""
        if self.is_placeholder_active:
            # Удаляем placeholder перед вставкой
            self.text_input.delete("1.0", tk.END)
            self.text_input.config(fg="black")
            self.is_placeholder_active = False
        # Tkinter сам обработает вставку после нашего обработчика
        return None  # Продолжить стандартную обработку

    def _on_clear_click(self):
        """Очистка полей"""
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", self.placeholder_text)
        self.text_input.config(fg="gray")
        self.is_placeholder_active = True
        self._clear_log()
        self.progress['value'] = 0
        self.progress_label.config(text="Готов к работе")

    def _on_process_click(self):
        """Обработка нажатия кнопки загрузки"""
        if self.is_processing:
            messagebox.showwarning("Внимание", "Обработка уже выполняется!")
            return

        # Проверка на placeholder
        if self.is_placeholder_active:
            messagebox.showwarning(
                "Внимание",
                "Введите кадастровые номера!\n\nПо одному на строку."
            )
            return

        # Получаем номера из текстового поля
        text = self.text_input.get("1.0", tk.END).strip()

        # Проверка что текст не пустой
        if not text:
            messagebox.showwarning(
                "Внимание",
                "Введите кадастровые номера!\n\nПо одному на строку."
            )
            return

        # Парсим номера (по одному на строку)
        cadastral_numbers = [
            line.strip()
            for line in text.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

        if not cadastral_numbers:
            messagebox.showwarning(
                "Внимание",
                "Не найдены кадастровые номера!"
            )
            return

        # Выбор места сохранения
        default_filename = f"cadastral_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_file = filedialog.asksaveasfilename(
            title="Сохранить результат как",
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")]
        )

        if not output_file:
            return  # Пользователь отменил сохранение

        # Запускаем обработку в отдельном потоке
        self._clear_log()
        self._log("=" * 80)
        self._log("НАЧАЛО ОБРАБОТКИ")
        self._log("=" * 80)
        self._log(f"\n📋 Найдено номеров: {len(cadastral_numbers)}")
        for idx, cn in enumerate(cadastral_numbers, 1):
            self._log(f"   {idx}. {cn}")
        self._log(f"\n💾 Файл будет сохранён: {output_file}\n")

        # Запускаем в отдельном потоке
        thread = threading.Thread(
            target=self._process_cadastral_numbers,
            args=(cadastral_numbers, output_file),
            daemon=True
        )
        thread.start()

    def _process_cadastral_numbers(self, cadastral_numbers: List[str], output_file: str):
        """Обработка кадастровых номеров (выполняется в отдельном потоке)"""
        self.is_processing = True
        self._set_buttons_state(False)

        results = []
        total = len(cadastral_numbers)

        try:
            # Создаем API клиент
            self._log("🔌 Создание API клиента...")
            self.api_client = NSPDAPIClient()
            self._log("✅ API клиент создан\n")

            self._log("=" * 80)
            self._log("ОБРАБОТКА НОМЕРОВ")
            self._log("=" * 80)

            # Обрабатываем каждый номер
            for idx, cadastral_number in enumerate(cadastral_numbers, 1):
                self._update_progress(idx, total, cadastral_number)

                self._log(f"\n{'─' * 80}")
                self._log(f"[{idx}/{total}] {cadastral_number}")
                self._log(f"{'─' * 80}")

                try:
                    # Получаем данные
                    self._log("⏳ Загрузка данных участка...")
                    result = self.api_client.get_full_parcel_info_with_objects(cadastral_number)

                    parcel = result['parcel_data']
                    objects = result['objects_data']

                    # Ограничиваем длину адреса для вывода
                    address_short = parcel.address[:60] + "..." if len(parcel.address) > 60 else parcel.address
                    self._log(f"✅ Участок: {address_short}")
                    self._log(f"✅ Объектов найдено: {len(objects)}")

                    # Формируем ParseResult
                    parse_result = ParseResult(
                        cadastral_number=cadastral_number,
                        parcel=parcel,
                        objects=objects,
                        status="Успешно"
                    )

                    results.append(parse_result)
                    self._log("✅ Данные обработаны")

                except Exception as e:
                    self._log(f"❌ Ошибка: {e}")
                    # Создаем результат с ошибкой
                    error_result = ParseResult(
                        cadastral_number=cadastral_number,
                        parcel=None,
                        objects=[],
                        status=f"Ошибка: {str(e)}"
                    )
                    results.append(error_result)

            # Закрываем клиент
            self._log("\n🔒 Закрытие API клиента...")
            self.api_client.close()
            self.api_client = None

            # Создаем Excel файл
            self._log("\n" + "=" * 80)
            self._log("СОЗДАНИЕ EXCEL ФАЙЛА")
            self._log("=" * 80)
            self._log(f"\n📝 Создание файла: {output_file}...")

            create_excel_with_template(results, output_file)

            self._log("✅ Excel файл создан!")

            # Финальная статистика
            success_count = sum(1 for r in results if r.status == "Успешно")
            error_count = total - success_count

            self._log("\n" + "=" * 80)
            self._log("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
            self._log("=" * 80)
            self._log(f"\n📊 Статистика:")
            self._log(f"   Обработано номеров: {total}")
            self._log(f"   Успешно: {success_count}")
            if error_count > 0:
                self._log(f"   Ошибок: {error_count}")
            self._log(f"\n💾 Файл сохранён: {output_file}")

            # Обновляем прогресс
            self._update_progress_label(f"✅ Готово! Обработано: {total}")

            # Показываем сообщение
            self.root.after(0, lambda: messagebox.showinfo(
                "Успех!",
                f"Обработка завершена!\n\n"
                f"Обработано номеров: {total}\n"
                f"Успешно: {success_count}\n"
                f"Ошибок: {error_count}\n\n"
                f"Файл сохранён:\n{output_file}"
            ))

        except Exception as e:
            self._log(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            self._log("\nПодробности:")
            self._log(traceback.format_exc())

            self._update_progress_label("❌ Ошибка")

            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка",
                f"Произошла критическая ошибка:\n\n{str(e)}"
            ))

        finally:
            # Закрываем клиент если был создан
            if self.api_client:
                try:
                    self.api_client.close()
                except:
                    pass

            self.is_processing = False
            self._set_buttons_state(True)
            self._update_progress(100, 100, "")

    def _log(self, message: str):
        """Добавление сообщения в лог"""
        def update():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        self.root.after(0, update)

    def _clear_log(self):
        """Очистка лога"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _update_progress(self, current: int, total: int, cadastral_number: str):
        """Обновление прогресс-бара"""
        def update():
            progress_percent = (current / total) * 100
            self.progress['value'] = progress_percent

            if cadastral_number:
                self.progress_label.config(
                    text=f"Обработка [{current}/{total}]: {cadastral_number}"
                )
            else:
                self.progress_label.config(text=f"[{current}/{total}]")

        self.root.after(0, update)

    def _update_progress_label(self, text: str):
        """Обновление текста прогресса"""
        self.root.after(0, lambda: self.progress_label.config(text=text))

    def _set_buttons_state(self, enabled: bool):
        """Включение/выключение кнопок"""
        def update():
            state = tk.NORMAL if enabled else tk.DISABLED
            self.btn_process.config(state=state)
            self.btn_clear.config(state=state)

        self.root.after(0, update)


def main():
    """Главная функция"""
    # Создаем главное окно
    root = tk.Tk()

    # Настраиваем стили
    style = ttk.Style()

    # Пытаемся использовать современную тему
    try:
        style.theme_use('vista')  # Windows
    except:
        try:
            style.theme_use('clam')  # Кросс-платформенная
        except:
            pass  # Используем тему по умолчанию

    # Создаем приложение
    app = NSPDParserGUI(root)

    # Запускаем главный цикл
    root.mainloop()


if __name__ == "__main__":
    main()
