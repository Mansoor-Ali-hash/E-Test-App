import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
import os
from datetime import datetime

# Files & Colors
RESULT_DIR = "results"
PRIMARY_COLOR = "#0d6efd"
SECONDARY_COLOR = "#f8fafc"
ACCENT_COLOR = "#198754"
ERROR_COLOR = "#dc3545"
TEXT_COLOR = "#212529"
CARD_BG = "#ffffff"
FONT_LARGE = ("Segoe UI", 18, "bold")
FONT_MEDIUM = ("Segoe UI", 14)
FONT_SMALL = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 24, "bold")

# ---- Helper: Category file mapping ----
def get_question_file_for_category(category):
    mapping = {
        "DIT": "questions_DIT.txt",
        "CIT": "questions_CIT.txt",
        "OAP": "questions_OAP.txt"
        # Add more if needed
    }
    file = mapping.get(category.upper())
    if not file or not os.path.exists(file):
        messagebox.showerror("Error", f"No question file found for category: {category}")
        return None
    return file

# ---- Question parsing ----
def parse_questions_from_file(file_path):
    questions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                question = lines[i]
                options = [opt.strip() for opt in lines[i+1].split('|')]
                answer = lines[i+2]
                questions.append({
                    "question": question,
                    "options": options,
                    "answer": answer
                })
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read questions file: {e}")
    return questions

def save_result_card(username, score, total, answers, questions, category):
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{RESULT_DIR}/{username}_result.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Result Card\n")
        f.write(f"Name: {username}\n")
        f.write(f"Category: {category}\n")
        f.write(f"Date: {dt}\n")
        f.write(f"Score: {score} / {total}\n")
        f.write("\nQuestion-wise Details:\n")
        for idx, q in enumerate(questions):
            sel = answers.get(idx, "")
            correct = q['answer']
            f.write(f"Q{idx+1}. {q['question']}\n")
            f.write(f"Your Answer: {sel}\n")
            f.write(f"Correct Answer: {correct}\n\n")

# ------------------- App Class -------------------
class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Test Portal")
        self.root.configure(bg=SECONDARY_COLOR)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=FONT_MEDIUM, foreground=PRIMARY_COLOR, padding=8, background=CARD_BG)
        style.configure("TLabel", font=FONT_MEDIUM, background=CARD_BG, foreground=TEXT_COLOR)
        style.configure("Card.TFrame", background=CARD_BG, borderwidth=2, relief="groove")
        style.configure("Accent.TButton", font=FONT_MEDIUM, foreground="white", background=PRIMARY_COLOR)

        self.category = None
        self.score = 0
        self.current = 0
        self.username = ""
        self.selected_answers = {}
        self.questions = []
        self.total_time_seconds = 0
        self.remaining_time = 0
        self.timer_id = None

        # Timer label (create once, always visible)
        self.timer_label = ttk.Label(self.root, text="", font=FONT_MEDIUM, foreground=ERROR_COLOR, background=SECONDARY_COLOR)
        self.timer_label.place(x=20, y=20)  # Top-left, adjust if needed

        self.create_welcome_screen()

    def card_frame(self):
        frame = ttk.Frame(self.root, style="Card.TFrame", padding=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        return frame

    def create_welcome_screen(self):
        for widget in self.root.winfo_children():
            # Don't destroy timer_label!
            if widget != self.timer_label:
                widget.destroy()
        frame = self.card_frame()
        logo = tk.Canvas(frame, width=80, height=80, bg=CARD_BG, highlightthickness=0)
        logo.create_oval(10, 10, 70, 70, fill=PRIMARY_COLOR, outline="")
        logo.create_text(40, 40, text="ST", fill="white", font=("Segoe UI", 22, "bold"))
        logo.pack(anchor="center", pady=5)

        ttk.Label(frame, text="Smart Test Portal", font=FONT_TITLE, background=CARD_BG, foreground=PRIMARY_COLOR).pack(pady=(0,10))
        ttk.Label(frame, text="Enter your name:", font=FONT_MEDIUM).pack(pady=5)
        self.name_entry = ttk.Entry(frame, font=FONT_MEDIUM)
        self.name_entry.pack(pady=5, ipadx=5, ipady=3)

        ttk.Label(frame, text="Select Test Category:", font=FONT_MEDIUM).pack(pady=5)
        self.category_var = tk.StringVar(value="DIT")
        categories = ["DIT", "CIT", "OAP"]
        self.category_menu = ttk.Combobox(frame, textvariable=self.category_var, values=categories, font=FONT_MEDIUM, state="readonly")
        self.category_menu.pack(pady=5, ipadx=5, ipady=3)

        ttk.Button(frame, text="Start Test", style="Accent.TButton", command=self.start_test).pack(pady=10, fill="x")

        # Hide timer on welcome
        self.timer_label.config(text="")

    def start_test(self):
        name = self.name_entry.get()
        self.category = self.category_var.get()
        question_file = get_question_file_for_category(self.category)
        if not name.strip():
            messagebox.showwarning("Warning", "Name is required!")
            return
        if not question_file:
            self.timer_label.config(text="")  # Hide timer
            return
        self.questions = parse_questions_from_file(question_file)
        if not self.questions:
            messagebox.showwarning("Warning", "No questions available for this category!")
            self.timer_label.config(text="")  # Hide timer
            return
        self.username = name.strip()
        self.score = 0
        self.current = 0
        self.selected_answers = {}
        self.total_time_seconds = len(self.questions) * 60  # 1 min per question
        self.remaining_time = self.total_time_seconds
        self.show_question()
        self.start_timer()

    # ---------- TIMER LOGIC --------------
    def start_timer(self):
        self.update_timer()

    def update_timer(self):
        mins, secs = divmod(self.remaining_time, 60)
        # Clock icon (🕒) + timer text
        self.timer_label.config(text=f"🕒  {mins:02d}:{secs:02d}")
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        else:
            self.show_result()  # Time's up! Show result

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    # ---------- QUESTION SCREEN ----------
    def show_question(self):
        for widget in self.root.winfo_children():
            if widget != self.timer_label:
                widget.destroy()
        frame = self.card_frame()
        frame.place(relx=0.5, rely=0.48, anchor="center", relwidth=0.85, relheight=0.75)

        if self.current < len(self.questions):
            q = self.questions[self.current]
            ttk.Label(frame, text=f"Question {self.current+1} of {len(self.questions)} [{self.category}]",
                      font=FONT_MEDIUM, foreground=PRIMARY_COLOR).pack(pady=(0,5))
            ttk.Label(frame, text=q['question'], font=FONT_LARGE, wraplength=520, justify="center").pack(pady=12)

            # Timer label already created, just update text
            # self.timer_label.config(text=f"🕒  {mins:02d}:{secs:02d}") is handled by update_timer

            self.selected_option = tk.StringVar(value=self.selected_answers.get(self.current, None))
            for opt in q['options']:
                btn = tk.Radiobutton(
                    frame, text=opt, variable=self.selected_option, value=opt,
                    font=FONT_MEDIUM, padx=12, pady=8,
                    indicatoron=0,
                    width=40, anchor="w",
                    relief="groove", bd=3,
                    bg="white", fg=TEXT_COLOR,
                    selectcolor=ACCENT_COLOR,
                    activebackground=PRIMARY_COLOR, activeforeground="white"
                )
                btn.pack(anchor="w", pady=6, padx=10)

                def on_click(opt=opt, b=btn):
                    self.selected_option.set(opt)
                    for w in frame.winfo_children():
                        if isinstance(w, tk.Radiobutton):
                            w.config(text=w.cget("value"))
                    b.config(text=f"✅ {opt}")

                btn.config(command=on_click)

            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=18)
            ttk.Button(btn_frame, text="Previous", command=self.previous_question).pack(side="left", padx=10)
            ttk.Button(btn_frame, text="Next", style="Accent.TButton", command=self.next_question).pack(side="left", padx=10)
        else:
            self.stop_timer()
            self.show_result()

    def next_question(self, auto=False):
        selected = self.selected_option.get()
        if not selected and not auto:
            messagebox.showwarning("Warning", "Please select an option!")
            return
        self.selected_answers[self.current] = selected if selected else ""
        self.current += 1
        self.show_question()

    def previous_question(self):
        selected = self.selected_option.get()
        if selected:
            self.selected_answers[self.current] = selected
        if self.current > 0:
            self.current -= 1
        self.show_question()

    def show_result(self):
        self.stop_timer()
        self.timer_label.config(text="")  # Hide timer on result
        self.score = sum(
            1 for idx, q in enumerate(self.questions)
            if self.selected_answers.get(idx, "") == q['answer']
        )
        for widget in self.root.winfo_children():
            if widget != self.timer_label:
                widget.destroy()
        frame = self.card_frame()
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total = len(self.questions)
        percentage = (self.score / total) * 100
        is_pass = percentage >= 50
        result_color = ACCENT_COLOR if is_pass else ERROR_COLOR
        result_icon = "✔" if is_pass else "✖"
        result_text = "Congratulations! You Passed 🎉" if is_pass else "Best of luck for next time!"

        canvas = tk.Canvas(frame, width=60, height=60, bg=CARD_BG, highlightthickness=0)
        canvas.create_text(30, 30, text=result_icon, font=("Segoe UI", 40), fill=result_color)
        canvas.pack()

        ttk.Label(frame, text="Result Card", font=FONT_TITLE, foreground=PRIMARY_COLOR).pack(pady=6)
        ttk.Label(frame, text=f"Name: {self.username}", font=FONT_MEDIUM).pack()
        ttk.Label(frame, text=f"Category: {self.category}", font=FONT_MEDIUM).pack()
        ttk.Label(frame, text=f"Date: {dt}", font=FONT_SMALL).pack()
        ttk.Label(frame, text=f"Score: {self.score} / {total}  ({percentage:.1f}%)",
                  font=FONT_MEDIUM, foreground=result_color).pack(pady=3)
        ttk.Label(frame, text=result_text, font=FONT_MEDIUM, foreground=result_color).pack(pady=10)

        save_result_card(self.username, self.score, total, self.selected_answers, self.questions, self.category)

        ttk.Label(frame, text=f"Result saved in '{RESULT_DIR}/{self.username}_result.txt'",
                  font=FONT_SMALL, foreground=PRIMARY_COLOR).pack(pady=3)

        ttk.Button(frame, text="Restart", style="Accent.TButton", command=self.create_welcome_screen).pack(pady=8, fill="x")

# ------------------- Run App -------------------
if __name__ == "__main__":
    root = tk.Tk()
    if os.path.exists("Icon.webp"):
        image = Image.open("Icon.webp")
        icon = ImageTk.PhotoImage(image)
        root.iconphoto(False, icon)
    root.geometry("600x700")
    root.configure(bg=SECONDARY_COLOR)
    app = TestApp(root)
    root.mainloop()