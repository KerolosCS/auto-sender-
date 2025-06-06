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
file_path = ""  # ما زلنا نحتاجه لحذف الأرقام
numbers = []
index = 0
running = False
last_hash = ""
file_observer = None
current_file_label = None


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
            status_label.config(text=f"♻️ تم التحديث التلقائي ({len(numbers)} رقم)")
            print(f"[DEBUG] إعادة تحميل تلقائي من {len(file_paths)} ملف.")

        except Exception as e:
            print(f"[ERROR] فشل التحديث التلقائي: {e}")
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
        file_path = file_paths[0]  # نستخدمه فقط للحذف بعد الإرسال

        status_label.config(text=f"📄 تم تحميل {len(numbers)} رقم من {len(file_paths)} ملف")
        current_file_label.config(text="الملفات الحالية: " + ", ".join(combined_name))
        update_coordinate_display()
        start_file_monitoring()

        print(f"[DEBUG] تم تحميل {len(numbers)} رقم من عدة ملفات.")

    except Exception as e:
        messagebox.showerror("خطأ", f"❌ لا يمكن قراءة الملفات:\n{str(e)}")
        print(f"[ERROR] فشل تحميل الملفات: {e}")


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
        messagebox.showwarning("تحذير", "لا توجد أرقام مُحمّلة!")
        return

    try:
        textbox_coords = textbox_entry.get().split(",")
        button_coords = button_entry.get().split(",")
        textbox_x = int(textbox_coords[0].strip())
        textbox_y = int(textbox_coords[1].strip())
        button_x = int(button_coords[0].strip())
        button_y = int(button_coords[1].strip())
    except:
        messagebox.showerror("خطأ", "❌ تأكد من كتابة الإحداثيات بشكل صحيح (مثال: 800,400)")
        return

    try:
        delay = float(delay_entry.get().strip())
    except:
        messagebox.showerror("خطأ", "❌ تأكد من كتابة وقت الانتظار بشكل صحيح (مثال: 2)")
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
        # 🧹 حذف الرقم اللي اتبعت من الملف وتحديثه
        try:
            from collections import Counter

            # حساب تكرار الأرقام المتبقية
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
                        continue  # هذا الرقم تم إرساله، فلا نضيفه

                with open(path, "w", encoding='utf-8') as f:
                    f.write("\n".join(new_lines) + "\n")

            print(f"[DEBUG] تم حذف الرقم '{number}' من الملفات بدقة باستخدام Counter.")

            # print(f"[DEBUG] تم حذف الرقم '{number}' من جميع الملفات.")

        except Exception as e:
            print(f"[ERROR] فشل تحديث الملفات بعد الإرسال: {e}")

        # status_label.config(text=f"✅ تم إرسال: {index}/{len(numbers)}")
        # root.update()
        root.after(0, lambda: status_label.config(text=f"✅ تم إرسال: {index}/{len(numbers)}"))

    if index >= len(numbers):
        messagebox.showinfo("تم", "✅ كل الأرقام خلصت.")
    running = False


def start_thread():
    if not numbers:
        messagebox.showwarning("تحذير", "حمّل ملف أرقام أولاً.")
        return
    threading.Thread(target=send_numbers, daemon=True).start()


def stop():
    global running
    running = False
    status_label.config(text="⛔ تم الإيقاف المؤقت.")


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
        status_label.config(text=f"📍 تم تحديث إحداثيات الزرار: {x},{y}")
        canvas.itemconfig(button_indicator, fill="#4CAF50", outline="#4CAF50")
        canvas.itemconfig(button_text, text=f"{x},{y}")

    elif key == 't':
        textbox_entry.delete(0, tk.END)
        textbox_entry.insert(0, f"{x},{y}")
        status_label.config(text=f"📍 تم تحديث إحداثيات مربع النص: {x},{y}")
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
root.title("🧠 Auto Number Sender - التحديث التلقائي")
root.geometry("550x650")
root.protocol("WM_DELETE_WINDOW", on_closing)
root.configure(bg="#f0f0f0")

file_frame = tk.Frame(root, bg="#f0f0f0")
file_frame.pack(pady=5, fill=tk.X)

current_file_label = tk.Label(file_frame, text="لا يوجد ملف محمل", font=("Arial", 10, "bold"), fg="#333333",
                              bg="#f0f0f0")
current_file_label.pack(side=tk.LEFT, padx=10)
#
# change_file_btn = tk.Button(file_frame, text="تغيير الملف", command=lambda: load_file(automatic=False), font=("Arial", 10), bg="#607D8B", fg="white")
# change_file_btn.pack(side=tk.RIGHT, padx=10)

coord_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.RIDGE)
coord_frame.pack(pady=10, padx=20, fill=tk.X)

canvas = tk.Canvas(coord_frame, width=400, height=100, bg="#ffffff", highlightthickness=0)
canvas.pack(pady=10, padx=10)

button_indicator = canvas.create_oval(350, 10, 370, 30, fill="#f0f0f0", outline="#cccccc", width=2)
textbox_indicator = canvas.create_oval(350, 50, 370, 70, fill="#f0f0f0", outline="#cccccc", width=2)

canvas.create_text(50, 20, text="إحداثيات الزر:", font=("Arial", 10, "bold"), anchor="w")
canvas.create_text(50, 60, text="إحداثيات مربع النص:", font=("Arial", 10, "bold"), anchor="w")
button_text = canvas.create_text(200, 20, text="لم يتم التقاط", font=("Arial", 10), fill="#777777")
textbox_text = canvas.create_text(200, 60, text="لم يتم التقاط", font=("Arial", 10), fill="#777777")

instruction_label = tk.Label(root, text="لتحديث الإحداثيات: ضع مؤشر الفأرة ثم اضغط (t) لمربع النص أو (b) للزر",
                             font=("Arial", 10, "bold"), fg="#2196F3", bg="#f0f0f0")
instruction_label.pack(pady=5)

content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

load_btn = tk.Button(content_frame, text="📂 تحميل ملف أرقام", command=lambda: load_file(automatic=False),
                     font=("Arial", 12), bg="#2196F3", fg="white")
load_btn.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

tk.Label(content_frame, text="📌 إحداثيات مربع الإدخال:", font=("Arial", 10), bg="#f0f0f0").grid(row=1, column=0,
                                                                                                 sticky="w")
textbox_entry = tk.Entry(content_frame, font=("Arial", 11))
textbox_entry.grid(row=1, column=1, pady=5, sticky="ew")

tk.Label(content_frame, text="📌 إحداثيات زر الضغط:", font=("Arial", 10), bg="#f0f0f0").grid(row=2, column=0,
                                                                                             sticky="w")
button_entry = tk.Entry(content_frame, font=("Arial", 11))
button_entry.grid(row=2, column=1, pady=5, sticky="ew")

tk.Label(content_frame, text="⏱️ وقت الانتظار بين كل رقم:", font=("Arial", 10), bg="#f0f0f0").grid(row=3, column=0,
                                                                                                   sticky="w")
delay_entry = tk.Entry(content_frame, font=("Arial", 11))
delay_entry.insert(0, "2")
delay_entry.grid(row=3, column=1, pady=5, sticky="ew")

btn_frame = tk.Frame(content_frame, bg="#f0f0f0")
btn_frame.grid(row=4, column=0, columnspan=2, pady=15)

start_btn = tk.Button(btn_frame, text="▶️ ابدأ", command=start_thread, font=("Arial", 12), bg="#4CAF50", fg="white")
start_btn.pack(side=tk.LEFT, padx=5)

stop_btn = tk.Button(btn_frame, text="⛔ إيقاف", command=stop, font=("Arial", 12), bg="#F44336", fg="white")
stop_btn.pack(side=tk.LEFT, padx=5)

status_frame = tk.Frame(content_frame, bg="#f0f0f0")
status_frame.grid(row=5, column=0, columnspan=2, pady=10)

status_label = tk.Label(status_frame, text="لم يتم التحميل بعد", font=("Arial", 11), bg="#f0f0f0")
status_label.pack()

mouse_pos_label = tk.Label(status_frame, text="🖱️ Mouse: X=0, Y=0", font=("Arial", 10), bg="#f0f0f0")
mouse_pos_label.pack()

content_frame.columnconfigure(1, weight=1)

root.bind('<Key>', on_key_press)
update_mouse_position()
update_coordinate_display()
root.mainloop()
