#!/usr/bin/env python3
"""
Тест функции вставки в GUI
"""
import tkinter as tk
from tkinter import scrolledtext

def test_paste():
    """Простой тест вставки"""
    root = tk.Tk()
    root.title("Тест вставки")
    root.geometry("400x300")

    # Инструкция
    label = tk.Label(root, text="Тест вставки (Ctrl+V / Cmd+V):", font=("Arial", 12, "bold"))
    label.pack(pady=10)

    instructions = tk.Label(
        root,
        text="1. Скопируйте любой текст\n2. Кликните в текстовое поле\n3. Вставьте текст:\n   • Ctrl+V (Win/Linux) или Cmd+V (Mac)\n   • ИЛИ правая кнопка мыши → Вставить\n4. Текст должен вставиться",
        justify=tk.LEFT
    )
    instructions.pack(pady=5)

    # Текстовое поле
    text_widget = scrolledtext.ScrolledText(root, height=8, font=("Consolas", 10))
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Placeholder
    placeholder = "Вставьте текст сюда..."
    is_placeholder = [True]  # Используем список чтобы изменять в closure

    def insert_placeholder():
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", placeholder)
        text_widget.config(fg="gray")
        is_placeholder[0] = True

    def remove_placeholder():
        if is_placeholder[0]:
            text_widget.delete("1.0", tk.END)
            text_widget.config(fg="black")
            is_placeholder[0] = False

    def on_focus_in(event):
        remove_placeholder()

    def on_focus_out(event):
        if not text_widget.get("1.0", tk.END).strip():
            insert_placeholder()

    def on_key(event):
        if is_placeholder[0] and event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Command']:
            remove_placeholder()

    def on_paste(event):
        remove_placeholder()
        return None  # Продолжить стандартную обработку

    # Контекстное меню
    def create_context_menu():
        context_menu = tk.Menu(text_widget, tearoff=0)
        context_menu.add_command(label="Вырезать", command=lambda: text_widget.event_generate("<<Cut>>"))
        context_menu.add_command(label="Копировать", command=lambda: text_widget.event_generate("<<Copy>>"))
        context_menu.add_command(
            label="Вставить",
            command=lambda: (remove_placeholder(), text_widget.event_generate("<<Paste>>"))
        )
        context_menu.add_separator()
        context_menu.add_command(label="Выделить всё", command=lambda: text_widget.tag_add(tk.SEL, "1.0", tk.END))
        return context_menu

    context_menu = create_context_menu()

    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    # Установка placeholder
    insert_placeholder()

    # Привязка событий
    text_widget.bind("<FocusIn>", on_focus_in)
    text_widget.bind("<FocusOut>", on_focus_out)
    text_widget.bind("<Key>", on_key)
    text_widget.bind("<<Paste>>", on_paste)  # Универсальное событие вставки (надёжнее)
    text_widget.bind("<Control-v>", on_paste)  # Windows/Linux (дополнительно)
    text_widget.bind("<Command-v>", on_paste)  # macOS (дополнительно)
    text_widget.bind("<Button-3>", show_context_menu)  # Windows/Linux - правая кнопка
    text_widget.bind("<Button-2>", show_context_menu)  # macOS - правая кнопка (Control+Click)

    # Кнопка проверки
    def check_content():
        content = text_widget.get("1.0", tk.END).strip()
        if is_placeholder[0]:
            result_label.config(text="❌ Placeholder активен - текст не введён", fg="red")
        elif content:
            result_label.config(text=f"✅ Вставлено {len(content)} символов", fg="green")
        else:
            result_label.config(text="⚠️ Поле пустое", fg="orange")

    btn_check = tk.Button(root, text="Проверить содержимое", command=check_content)
    btn_check.pack(pady=5)

    result_label = tk.Label(root, text="", font=("Arial", 10))
    result_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    print("=" * 80)
    print("ТЕСТ ВСТАВКИ В ТЕКСТОВОЕ ПОЛЕ")
    print("=" * 80)
    print()
    print("Инструкция:")
    print("1. Откроется окно с текстовым полем")
    print("2. Скопируйте любой текст (например: 77:05:0001016:22)")
    print("3. Кликните в текстовое поле")
    print("4. Вставьте текст одним из способов:")
    print("   • Нажмите Ctrl+V (Windows/Linux) или Cmd+V (Mac)")
    print("   • ИЛИ щёлкните правой кнопкой мыши → Вставить")
    print("5. Текст должен вставиться, удалив placeholder")
    print("6. Нажмите 'Проверить содержимое' для проверки")
    print()
    print("Запуск теста...")
    print()

    test_paste()
