#!/usr/bin/env python3

import tkinter as tk
from datetime import datetime, date
from tkinter import font as tkfont
import calendar

class YearProgressApp:
    def __init__(self, root):
        self.root = root
        self.root.title("연간 진행률")
        
        width = 800
        height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        
        self.root.configure(bg='black')
        
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=24)
        
        self.date_label = tk.Label(
            root, 
            fg='white', 
            bg='black', 
            font=('Malgun Gothic', 28, 'bold')
        )
        self.date_label.pack(pady=28)
        
        self.progress_text_frame = tk.Frame(root, bg='black')
        self.progress_text_frame.pack(pady=10)
        
        self.year_label = tk.Label(
            self.progress_text_frame,
            fg='white',
            bg='black',
            font=('Malgun Gothic', 28)
        )
        self.year_label.pack()
        
        self.progress_label = tk.Label(
            self.progress_text_frame,
            fg='red',
            bg='black',
            font=('Malgun Gothic', 45, 'bold')
        )
        self.progress_label.pack()
        
        self.progress_frame = tk.Frame(root, bg='white', height=40, width=600)
        self.progress_frame.pack(pady=25)
        
        self.progress_bar = tk.Frame(self.progress_frame, bg='#4CAF50', height=40, width=0)
        self.progress_bar.place(x=0, y=0)
        
        self.days_label = tk.Label(
            root, 
            fg='white', 
            bg='black', 
            font=('Malgun Gothic', 24)
        )
        self.days_label.pack(pady=13)
        
        self.remaining_label = tk.Label(
            root, 
            fg='#00BFFF', 
            bg='black', 
            font=('Malgun Gothic', 32, 'bold')
        )
        self.remaining_label.pack(pady=13)
        
        self.update_progress()
        
    def calculate_progress(self):
        current_date = datetime.now()
        current_year = current_date.year
        total_days = 366 if calendar.isleap(current_year) else 365
        
        year_end = date(current_year, 12, 31)
        days_remaining = (year_end - current_date.date()).days
        days_passed = total_days - days_remaining
        progress = (days_passed / total_days) * 100
        
        return current_date, progress, days_passed, days_remaining, total_days
    
    def update_progress(self):
        current_date, progress, days_passed, days_remaining, total_days = self.calculate_progress()
        
        self.date_label.config(
            text=f"오늘은 {current_date.year}년 {current_date.month}월 {current_date.day}일 입니다"
        )
        self.year_label.config(text=f"당신의 {current_date.year}년은")
        self.progress_label.config(text=f"{progress:.1f}% 없어졌습니다")
        self.days_label.config(text=f"{days_passed}/{total_days}일")
        self.remaining_label.config(text=f"{days_remaining}일 남음")
        
        bar_width = int((progress / 100) * 600)
        self.progress_bar.configure(width=bar_width)
        
        self.root.after(1000, self.update_progress)

if __name__ == "__main__":
    root = tk.Tk()
    app = YearProgressApp(root)
    root.mainloop()
