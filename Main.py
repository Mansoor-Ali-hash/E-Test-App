import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
import os
from datetime import datetime

# Files
QUESTION_FILE = "questions.txt"
RESULT_DIR = "results"

# Modern Color Palette (HD Look)
PRIMARY_COLOR = "#0d6efd"      # Bright Blue
SECONDARY_COLOR = "#f8fafc"    # Off White
ACCENT_COLOR = "#198754"       # Green
ERROR_COLOR = "#dc3545"        # Red
TEXT_COLOR = "#212529"         # Dark Gray
CARD_BG = "#ffffff"            # White Card Background

FONT_LARGE = ("Segoe UI", 18, "bold")
FONT_MEDIUM = ("Segoe UI", 14)
FONT_SMALL = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 24, "bold")

# ------------------- Question Parsing -------------------
def parse_questions_from_file(file_path):
    questions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]  # khali lines ignore

        for i in range(0, len(lines), 3):   # har 3 line ek question block
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

def save_result_card(username, score, total, answers, questions):
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{RESULT_DIR}/{username}_result.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Result Card\n")
        f.write(f"Name: {username}\n")
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

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=FONT_MEDIUM, foreground=PRIMARY_COLOR, padding=8, background=CARD_BG)
        style.configure("TLabel", font=FONT_MEDIUM, background=CARD_BG, foreground=TEXT_COLOR)
        style.configure("Card.TFrame", background=CARD_BG, borderwidth=2, relief="groove")
        style.configure("Accent.TButton", font=FONT_MEDIUM, foreground="white", background=PRIMARY_COLOR)

        # Load questions
        self.questions = parse_questions_from_file(QUESTION_FILE)
        self.score = 0
        self.current = 0
        self.username = ""
        self.selected_answers = {}
        self.create_welcome_screen()

    def card_frame(self):
        frame = ttk.Frame(self.root, style="Card.TFrame", padding=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        return frame

    def create_welcome_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        frame = self.card_frame()

        # Logo / Title
        logo = tk.Canvas(frame, width=80, height=80, bg=CARD_BG, highlightthickness=0)
        logo.create_oval(10, 10, 70, 70, fill=PRIMARY_COLOR, outline="")
        logo.create_text(40, 40, text="ST", fill="white", font=("Segoe UI", 22, "bold"))
        logo.pack(anchor="center", pady=5)

        ttk.Label(frame, text="Smart Test Portal", font=FONT_TITLE, background=CARD_BG, foreground=PRIMARY_COLOR).pack(pady=(0,10))

        ttk.Label(frame, text="Enter your name:", font=FONT_MEDIUM).pack(pady=5)
        self.name_entry = ttk.Entry(frame, font=FONT_MEDIUM)
        self.name_entry.pack(pady=5, ipadx=5, ipady=3)

        ttk.Button(frame, text="Start Test", style="Accent.TButton", command=self.start_test).pack(pady=10, fill="x")

        if not self.questions:
            ttk.Label(frame, text="No questions found! Please add 'questions.txt'.", font=FONT_SMALL, foreground=ERROR_COLOR).pack(pady=5)

    def start_test(self):
        name = self.name_entry.get()
        if not name.strip():
            messagebox.showwarning("Warning", "Name is required!")
            return
        if not self.questions:
            messagebox.showwarning("Warning", "No questions available!")
            return
        self.username = name.strip()
        self.score = 0
        self.current = 0
        self.selected_answers = {}
        self.show_question()   # ✅ yahan se call ho raha hai

    #✅ Yehi wo function hai jo aapne bheja tha
    def show_question(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        # Frame ko 2/3 screen ka banayenge
        frame = self.card_frame()
        frame.place(relx=0.5, rely=0.48, anchor="center", relwidth=0.85, relheight=0.75)

        if self.current < len(self.questions):
            q = self.questions[self.current]
            ttk.Label(frame, text=f"Question {self.current+1} of {len(self.questions)}", 
                      font=FONT_MEDIUM, foreground=PRIMARY_COLOR).pack(pady=(0,5))
            ttk.Label(frame, text=q['question'], font=FONT_LARGE, wraplength=520, justify="center").pack(pady=12)

            # Custom square option buttons
            self.selected_option = tk.StringVar(value=self.selected_answers.get(self.current, None))
            for opt in q['options']:
                btn = tk.Radiobutton(
                    frame, text=opt, variable=self.selected_option, value=opt,
                    font=FONT_MEDIUM, padx=12, pady=8,
                    indicatoron=0,  # removes default bullet
                    width=40, anchor="w",
                    relief="groove", bd=3,  # Square box look
                    bg="white", fg=TEXT_COLOR,
                    selectcolor=ACCENT_COLOR,
                    activebackground=PRIMARY_COLOR, activeforeground="white"
                )
                btn.pack(anchor="w", pady=6, padx=10)

                # Tick mark update on select
                def on_click(opt=opt, b=btn):
                    self.selected_option.set(opt)
                    for w in frame.winfo_children():
                        if isinstance(w, tk.Radiobutton):
                            w.config(text=w.cget("value"))  # reset text
                    b.config(text=f"✅ {opt}")  # tick with option

                btn.config(command=on_click)

            # Navigation buttons
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=18)
            ttk.Button(btn_frame, text="Previous", command=self.previous_question).pack(side="left", padx=10)
            ttk.Button(btn_frame, text="Next", style="Accent.TButton", command=self.next_question).pack(side="left", padx=10)
        else:
            self.show_result()
    
    def next_question(self):
        selected = self.selected_option.get()
        if not selected:
            messagebox.showwarning("Warning", "Please select an option!")
            return
        self.selected_answers[self.current] = selected
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
        self.score = sum(
        1 for idx, q in enumerate(self.questions)
        if self.selected_answers.get(idx, "") == q['answer']
    )
        for widget in self.root.winfo_children():
             widget.destroy()
        frame = self.card_frame()
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Calculate percentage
        total = len(self.questions)
        percentage = (self.score / total) * 100

    # Pass/Fail
        is_pass = percentage >= 50
        result_color = ACCENT_COLOR if is_pass else ERROR_COLOR
        result_icon = "✔" if is_pass else "✖"
        result_text = "Congratulations! You Passed 🎉" if is_pass else "Best of luck for next time!"

    # Icon
        canvas = tk.Canvas(frame, width=60, height=60, bg=CARD_BG, highlightthickness=0)
        canvas.create_text(30, 30, text=result_icon, font=("Segoe UI", 40), fill=result_color)
        canvas.pack()

    # Labels
        ttk.Label(frame, text="Result Card", font=FONT_TITLE, foreground=PRIMARY_COLOR).pack(pady=6)
        ttk.Label(frame, text=f"Name: {self.username}", font=FONT_MEDIUM).pack()
        ttk.Label(frame, text=f"Date: {dt}", font=FONT_SMALL).pack()
        ttk.Label(frame, text=f"Score: {self.score} / {total}  ({percentage:.1f}%)",
              font=FONT_MEDIUM, foreground=result_color).pack(pady=3)
        ttk.Label(frame, text=result_text, font=FONT_MEDIUM, foreground=result_color).pack(pady=10)

    # Save result (short version)
        save_result_card(self.username, self.score, total, self.selected_answers, self.questions)

        ttk.Label(frame, text=f"Result saved in '{RESULT_DIR}/{self.username}_result.txt'",
              font=FONT_SMALL, foreground=PRIMARY_COLOR).pack(pady=3)

        ttk.Button(frame, text="Restart", style="Accent.TButton", command=self.create_welcome_screen).pack(pady=8, fill="x")

# ------------------- Run App -------------------
if __name__ == "__main__":
    root = tk.Tk()
    # Icon (optional)
    if os.path.exists("Icon.webp"):
        image = Image.open("Icon.webp")
        icon = ImageTk.PhotoImage(image)
        root.iconphoto(False, icon)
    root.geometry("600x700")
    root.configure(bg=SECONDARY_COLOR)
    app = TestApp(root)
    root.mainloop()
