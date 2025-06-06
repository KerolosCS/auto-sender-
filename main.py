import tkinter as tk
from tkinter import filedialog, messagebox
import pyautogui
import time
import threading
import os
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global variables
file_paths = []
file_path = ""  # Still needed for deleting numbers
numbers = []
index = 0
running = False
last_hash = ""
file_observer = None
current_file_label = None
language = "arabic"  # Default language

# Language dictionaries
translations = {
    "arabic": {
        "title": "🧠 مرسل الأرقام التلقائي - التحديث التلقائي",
        "no_file": "لا يوجد ملف محمل",
        "load_button": "📂 تحميل ملف أرقام",
        "textbox_label": "📌 إحداثيات مربع الإدخال:",
        "button_label": "📌 إحداثيات زر الضغط:",
        "delay_label": "⏱️ وقت الانتظار بين كل رقم:",
        "start_button": "▶️ ابدأ",
        "stop_button": "⛔ إيقاف",
        "not_loaded": "لم يتم التحميل بعد",
        "mouse_pos": "🖱️ Mouse: X=0, Y=0",
        "coords_instruction": "لتحديث الإحداثيات: ضع مؤشر الفأرة ثم اضغط (t) لمربع النص أو (b) للزر",
        "button_text": "إحداثيات الزر:",
        "textbox_text": "إحداثيات مربع النص:",
        "not_captured": "لم يتم التقاط",
        "no_numbers": "لا توجد أرقام مُحمّلة!",
        "coord_error": "❌ تأكد من كتابة الإحداثيات بشكل صحيح (مثال: 800,400)",
        "delay_error": "❌ تأكد من كتابة وقت الانتظار بشكل صحيح (مثال: 2)",
        "loaded_status": "📄 تم تحميل {count} رقم من {files} ملف",
        "sending_status": "✅ تم إرسال: {current}/{total}",
        "paused_status": "⛔ تم الإيقاف المؤقت.",
        "completed": "✅ كل الأرقام خلصت.",
        "update_button": "إنجليزي / English",
        "button_update": "📍 تم تحديث إحداثيات الزرار: {x},{y}",
        "textbox_update": "📍 تم تحديث إحداثيات مربع النص: {x},{y}",
        "auto_update": "♻️ تم التحديث التلقائي ({count} رقم)"
    },
    "english": {
        "title": "🧠 Auto Number Sender - Auto Reload",
        "no_file": "No file loaded",
        "load_button": "📂 Load Numbers File",
        "textbox_label": "📌 Textbox Coordinates:",
        "button_label": "📌 Button Coordinates:",
        "delay_label": "⏱️ Delay between numbers:",
        "start_button": "▶️ Start",
        "stop_button": "⛔ Stop",
        "not_loaded": "Not loaded yet",
        "mouse_pos": "🖱️ Mouse: X=0, Y=0",
        "coords_instruction": "To update coordinates: Position mouse then press (t) for textbox or (b) for button",
        "button_text": "Button Coordinates:",
        "textbox_text": "Textbox Coordinates:",
        "not_captured": "Not captured",
        "no_numbers": "No numbers loaded!",
        "coord_error": "❌ Make sure coordinates are correct (example: 800,400)",
        "delay_error": "❌ Make sure delay is correct (example: 2)",
        "loaded_status": "📄 Loaded {count} numbers from {files} files",
        "sending_status": "✅ Sent: {current}/{total}",
        "paused_status": "⛔ Paused.",
        "completed": "✅ All numbers completed.",
        "update_button": "عربي / Arabic",
        "button_update": "📍 Button coordinates updated: {x},{y}",
        "textbox_update": "📍 Textbox coordinates updated: {x},{y}",
        "auto_update": "♻️ Auto updated ({count} numbers)"
    }
}


class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global file_paths
        try:
            if os.path.abspath(event.src_path) in [os.path.abspath(p) for p in file_paths]:
                print(f"[DEBUG] Detected modification: {event.src_path}")
                load_file(automatic=True)
        except Exception as e:
            print(f"[ERROR] Auto reload failed: {e}")


def calculate_file_hash():
    global file_path
    if not file_path or not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_file(automatic=False):
    global numbers, index, file_paths, file_path

    if automatic:
        all_numbers = []
        try:
            for path in file_paths:
                if not os.path.exists(path):
                    continue
                with open(path, "r", encoding='utf-8') as f:
                    file_numbers = [line.strip() for line in f if line.strip()]
                    all_numbers.extend(file_numbers)

            numbers[:] = all_numbers
            index = 0
            status_label.config(text=translations[language]["auto_update"].format(count=len(numbers)))
            print(f"[DEBUG] Auto reloaded from {len(file_paths)} files.")

        except Exception as e:
            print(f"[ERROR] Auto update failed: {e}")
        return

    selected_files = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
    if not selected_files:
        return

    all_numbers = []
    combined_name = []

    try:
        for path in selected_files:
            with open(path, "r", encoding='utf-8') as f:
                file_numbers = [line.strip() for line in f if line.strip()]
                all_numbers.extend(file_numbers)
                combined_name.append(os.path.basename(path))

        numbers = all_numbers
        index = 0
        file_paths = list(selected_files)
        file_path = file_paths[0]  # Still needed for deletion after sending

        status_label.config(
            text=translations[language]["loaded_status"].format(count=len(numbers), files=len(file_paths)))
        current_file_label.config(
            text=translations[language]["no_file"] if not combined_name else ", ".join(combined_name))
        update_coordinate_display()
        start_file_monitoring()

        print(f"[DEBUG] Loaded {len(numbers)} numbers from multiple files.")

    except Exception as e:
        messagebox.showerror("Error", f"❌ Cannot read files:\n{str(e)}")
        print(f"[ERROR] Failed to load files: {e}")


def start_file_monitoring():
    global file_observer, file_paths

    try:
        if file_observer:
            file_observer.stop()
            file_observer.join()
            print("[DEBUG] Existing observer stopped.")

        if not file_paths:
            print("[DEBUG] No file paths provided for observer.")
            return

        file_observer = Observer()
        event_handler = FileChangeHandler()

        watched_dirs = set()
        for path in file_paths:
            directory = os.path.dirname(os.path.abspath(path))
            if directory not in watched_dirs:
                file_observer.schedule(event_handler, path=directory, recursive=False)
                watched_dirs.add(directory)
                print(f"[DEBUG] Watching directory: {directory}")

        file_observer.start()
        print("[DEBUG] File observer started for multiple files.")

    except Exception as e:
        print(f"[ERROR] Failed to start observer: {e}")


def send_numbers():
    global index, running

    if not numbers:
        messagebox.showwarning(translations[language]["no_numbers"], translations[language]["no_numbers"])
        return

    try:
        textbox_coords = textbox_entry.get().split(",")
        button_coords = button_entry.get().split(",")
        textbox_x = int(textbox_coords[0].strip())
        textbox_y = int(textbox_coords[1].strip())
        button_x = int(button_coords[0].strip())
        button_y = int(button_coords[1].strip())
    except:
        messagebox.showerror("Error", translations[language]["coord_error"])
        return

    try:
        delay = float(delay_entry.get().strip())
    except:
        messagebox.showerror("Error", translations[language]["delay_error"])
        return

    running = True
    time.sleep(3)

    while index < len(numbers) and running:
        number = numbers[index]

        pyautogui.click(textbox_x, textbox_y)
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(number)
        time.sleep(0.2)

        pyautogui.click(button_x, button_y)
        time.sleep(delay)

        index += 1
        # Delete the sent number from the file and update it
        try:
            from collections import Counter

            # Count remaining numbers
            remaining_numbers = numbers[index:]
            remaining_counter = Counter(remaining_numbers)

            for path in file_paths:
                if not os.path.exists(path):
                    continue
                with open(path, "r", encoding='utf-8') as f:
                    file_lines = [line.strip() for line in f if line.strip()]

                new_lines = []
                file_counter = Counter(file_lines)

                for num in file_lines:
                    if remaining_counter[num] > 0:
                        new_lines.append(num)
                        remaining_counter[num] -= 1
                    else:
                        continue  # This number has been sent, don't include it

                with open(path, "w", encoding='utf-8') as f:
                    f.write("\n".join(new_lines) + "\n")

            print(f"[DEBUG] Deleted number '{number}' from files using Counter.")

        except Exception as e:
            print(f"[ERROR] Failed to update files after sending: {e}")

        root.after(0, lambda: status_label.config(
            text=translations[language]["sending_status"].format(current=index, total=len(numbers))))

    if index >= len(numbers):
        messagebox.showinfo("Done", translations[language]["completed"])
    running = False


def start_thread():
    if not numbers:
        messagebox.showwarning("Warning", translations[language]["no_numbers"])
        return
    threading.Thread(target=send_numbers, daemon=True).start()


def stop():
    global running
    running = False
    status_label.config(text=translations[language]["paused_status"])


def update_mouse_position():
    x, y = pyautogui.position()
    mouse_pos_label.config(text=f"🖱️ Mouse: X={x}, Y={y}")
    root.after(100, update_mouse_position)


def on_key_press(event):
    x, y = pyautogui.position()
    key = event.char.lower()

    if key == 'b':
        button_entry.delete(0, tk.END)
        button_entry.insert(0, f"{x},{y}")
        status_label.config(text=translations[language]["button_update"].format(x=x, y=y))
        canvas.itemconfig(button_indicator, fill="#4CAF50", outline="#4CAF50")
        canvas.itemconfig(button_text, text=f"{x},{y}")

    elif key == 't':
        textbox_entry.delete(0, tk.END)
        textbox_entry.insert(0, f"{x},{y}")
        status_label.config(text=translations[language]["textbox_update"].format(x=x, y=y))
        canvas.itemconfig(textbox_indicator, fill="#2196F3", outline="#2196F3")
        canvas.itemconfig(textbox_text, text=f"{x},{y}")


def update_coordinate_display():
    if button_entry.get():
        coords = button_entry.get().split(",")
        if len(coords) == 2:
            canvas.itemconfig(button_indicator, fill="#4CAF50", outline="#4CAF50")
            canvas.itemconfig(button_text, text=f"{coords[0]},{coords[1]}")

    if textbox_entry.get():
        coords = textbox_entry.get().split(",")
        if len(coords) == 2:
            canvas.itemconfig(textbox_indicator, fill="#2196F3", outline="#2196F3")
            canvas.itemconfig(textbox_text, text=f"{coords[0]},{coords[1]}")

    root.after(1000, update_coordinate_display)


def toggle_language():
    global language
    language = "english" if language == "arabic" else "arabic"
    update_ui_language()
    language_button.config(text=translations[language]["update_button"])


def update_ui_language():
    root.title(translations[language]["title"])
    current_file_label.config(text=translations[language]["no_file"])
    load_btn.config(text=translations[language]["load_button"])
    textbox_label.config(text=translations[language]["textbox_label"])
    button_label.config(text=translations[language]["button_label"])
    delay_label.config(text=translations[language]["delay_label"])
    start_btn.config(text=translations[language]["start_button"])
    stop_btn.config(text=translations[language]["stop_button"])
    status_label.config(text=translations[language]["not_loaded"])
    instruction_label.config(text=translations[language]["coords_instruction"])

    # Update canvas text
    canvas.itemconfig(button_canvas_text, text=translations[language]["button_text"])
    canvas.itemconfig(textbox_canvas_text, text=translations[language]["textbox_text"])

    # Update coordinate display if empty
    if not button_entry.get():
        canvas.itemconfig(button_text, text=translations[language]["not_captured"])
    if not textbox_entry.get():
        canvas.itemconfig(textbox_text, text=translations[language]["not_captured"])


def on_closing():
    global running, file_observer
    running = False
    if file_observer:
        file_observer.stop()
        file_observer.join()
        print("[DEBUG] File observer stopped on exit.")
    root.destroy()


# GUI Setup
root = tk.Tk()
root.title(translations[language]["title"])
root.geometry("550x700")  # Slightly taller for the language button
root.protocol("WM_DELETE_WINDOW", on_closing)
root.configure(bg="#f0f0f0")

# Language button at the top
language_button = tk.Button(root, text=translations[language]["update_button"], command=toggle_language,
                            font=("Arial", 10), bg="#9E9E9E", fg="white")
language_button.pack(pady=5, fill=tk.X, padx=20)

file_frame = tk.Frame(root, bg="#f0f0f0")
file_frame.pack(pady=5, fill=tk.X)

current_file_label = tk.Label(file_frame, text=translations[language]["no_file"],
                              font=("Arial", 10, "bold"), fg="#333333", bg="#f0f0f0")
current_file_label.pack(side=tk.LEFT, padx=10)

coord_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.RIDGE)
coord_frame.pack(pady=10, padx=20, fill=tk.X)

canvas = tk.Canvas(coord_frame, width=400, height=100, bg="#ffffff", highlightthickness=0)
canvas.pack(pady=10, padx=10)

button_indicator = canvas.create_oval(350, 10, 370, 30, fill="#f0f0f0", outline="#cccccc", width=2)
textbox_indicator = canvas.create_oval(350, 50, 370, 70, fill="#f0f0f0", outline="#cccccc", width=2)

button_canvas_text = canvas.create_text(50, 20, text=translations[language]["button_text"],
                                        font=("Arial", 10, "bold"), anchor="w")
textbox_canvas_text = canvas.create_text(50, 60, text=translations[language]["textbox_text"],
                                         font=("Arial", 10, "bold"), anchor="w")
button_text = canvas.create_text(200, 20, text=translations[language]["not_captured"],
                                 font=("Arial", 10), fill="#777777")
textbox_text = canvas.create_text(200, 60, text=translations[language]["not_captured"],
                                  font=("Arial", 10), fill="#777777")

instruction_label = tk.Label(root, text=translations[language]["coords_instruction"],
                             font=("Arial", 10, "bold"), fg="#2196F3", bg="#f0f0f0")
instruction_label.pack(pady=5)

content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

load_btn = tk.Button(content_frame, text=translations[language]["load_button"],
                     command=lambda: load_file(automatic=False), font=("Arial", 12), bg="#2196F3", fg="white")
load_btn.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

textbox_label = tk.Label(content_frame, text=translations[language]["textbox_label"],
                         font=("Arial", 10), bg="#f0f0f0")
textbox_label.grid(row=1, column=0, sticky="w")
textbox_entry = tk.Entry(content_frame, font=("Arial", 11))
textbox_entry.grid(row=1, column=1, pady=5, sticky="ew")

button_label = tk.Label(content_frame, text=translations[language]["button_label"],
                        font=("Arial", 10), bg="#f0f0f0")
button_label.grid(row=2, column=0, sticky="w")
button_entry = tk.Entry(content_frame, font=("Arial", 11))
button_entry.grid(row=2, column=1, pady=5, sticky="ew")

delay_label = tk.Label(content_frame, text=translations[language]["delay_label"],
                       font=("Arial", 10), bg="#f0f0f0")
delay_label.grid(row=3, column=0, sticky="w")
delay_entry = tk.Entry(content_frame, font=("Arial", 11))
delay_entry.insert(0, "2")
delay_entry.grid(row=3, column=1, pady=5, sticky="ew")

btn_frame = tk.Frame(content_frame, bg="#f0f0f0")
btn_frame.grid(row=4, column=0, columnspan=2, pady=15)

start_btn = tk.Button(btn_frame, text=translations[language]["start_button"], command=start_thread,
                      font=("Arial", 12), bg="#4CAF50", fg="white")
start_btn.pack(side=tk.LEFT, padx=5)

stop_btn = tk.Button(btn_frame, text=translations[language]["stop_button"], command=stop,
                     font=("Arial", 12), bg="#F44336", fg="white")
stop_btn.pack(side=tk.LEFT, padx=5)

status_frame = tk.Frame(content_frame, bg="#f0f0f0")
status_frame.grid(row=5, column=0, columnspan=2, pady=10)

status_label = tk.Label(status_frame, text=translations[language]["not_loaded"],
                        font=("Arial", 11), bg="#f0f0f0")
status_label.pack()

mouse_pos_label = tk.Label(status_frame, text=translations[language]["mouse_pos"],
                           font=("Arial", 10), bg="#f0f0f0")
mouse_pos_label.pack()

content_frame.columnconfigure(1, weight=1)

root.bind('<Key>', on_key_press)
update_mouse_position()
update_coordinate_display()
root.mainloop()
# pyinstaller --noconfirm --onefile --windowed app.py

