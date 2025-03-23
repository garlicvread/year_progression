#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, date, timedelta
import calendar
import os
import locale

# Locale setup (Korean)
try:
    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Korean_Korea.949')  # Windows
    except:
        pass


class AddDDayDialog(tk.Toplevel):
    def __init__(self, parent, edit_data=None):
        super().__init__(parent)
        self.transient(parent)  # 부모 창에 종속
        self.grab_set()  # 모달 창으로 설정
        
        if edit_data:  # 수정 모드
            self.title("D-Day 수정")
            self.edit_mode = True
            self.edit_index = edit_data[0]
            name, date_obj = edit_data[1]
        else:  # 추가 모드
            self.title("D-Day 추가")
            self.edit_mode = False
            name, date_obj = "", date.today()

        self.geometry("300x200")
        self.resizable(False, False)

        # 창 중앙에 위치
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (parent.winfo_rootx() + parent.winfo_width() // 2) - (width // 2)
        y = (parent.winfo_rooty() + parent.winfo_height() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

        self.name_label = ttk.Label(self, text="이름:")
        self.name_label.pack(pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(pady=5)
        if name:
            self.name_entry.insert(0, name)

        self.date_label = ttk.Label(self, text="날짜 (YYYY-MM-DD):")
        self.date_label.pack(pady=5)
        self.date_entry = ttk.Entry(self)
        self.date_entry.pack(pady=5)
        if date_obj:
            self.date_entry.insert(0, date_obj.strftime("%Y-%m-%d"))

        button_text = "수정" if self.edit_mode else "추가"
        self.add_button = ttk.Button(self, text=button_text, command=self.save_dday)
        self.add_button.pack(pady=10)

        self.result = None

    def save_dday(self):
        name = self.name_entry.get().strip()
        date_str = self.date_entry.get().strip()

        if not name or not date_str:
            messagebox.showerror("오류", "이름과 날짜를 모두 입력하세요.")
            return

        try:
            year, month, day = map(int, date_str.split('-'))
            date_obj = date(year, month, day)
        except ValueError:
            messagebox.showerror("오류", "잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력하세요.")
            return

        self.result = (name, date_obj)
        self.destroy()


class DDayManager(tk.Toplevel):
    def __init__(self, parent, ddays=None):
        super().__init__(parent)
        self.parent = parent
        self.title("D-Day 관리자")
        self.geometry("700x500")
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # 창 닫기 이벤트 처리
        
        self.ddays = ddays if ddays is not None else []
        self.today = date.today()
        
        # 상단 프레임 (버튼 영역)
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.add_button = ttk.Button(self.button_frame, text="D-Day 추가", command=self.add_dday)
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_button = ttk.Button(self.button_frame, text="D-Day 수정", command=self.edit_dday)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(self.button_frame, text="D-Day 삭제", command=self.delete_dday)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # 스크롤 가능한 프레임 생성
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.scrollbar.pack(side="right", fill="y")
        
        # 현재 날짜 표시 레이블
        self.date_label = ttk.Label(
            self.scrollable_frame,
            text=f"오늘은 {self.today.year}년 {self.today.month}월 {self.today.day}일",
            font=('Malgun Gothic', 14, 'bold')
        )
        self.date_label.pack(pady=10)
        
        # D-Day 목록 표시
        self.update_dday_list()
    
    def on_close(self):
        # 변경된 D-Day 목록을 부모 창에 전달
        if hasattr(self.parent, 'update_ddays_from_manager'):
            self.parent.update_ddays_from_manager(self.ddays)
        self.destroy()
    
    def add_dday(self):
        dialog = AddDDayDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.ddays.append(dialog.result)
            self.ddays.sort(key=lambda x: x[1])  # 날짜 순으로 정렬
            self.update_dday_list()
    
    def edit_dday(self):
        selection = self.get_selected_dday()
        if selection is not None:
            dialog = AddDDayDialog(self, edit_data=selection)
            self.wait_window(dialog)
            if dialog.result:
                self.ddays[selection[0]] = dialog.result
                self.ddays.sort(key=lambda x: x[1])  # 날짜 순으로 정렬
                self.update_dday_list()
    
    def delete_dday(self):
        selection = self.get_selected_dday()
        if selection is not None:
            name = selection[1][0]
            result = messagebox.askyesno("확인", f"{name} D-Day를 삭제하시겠습니까?")
            if result:
                del self.ddays[selection[0]]
                self.update_dday_list()
    
    def get_selected_dday(self):
        # 현재 구현에서는 간단하게 리스트 번호로 선택
        # 실제 구현에서는 리스트박스나 트리뷰 등을 사용하여 선택 기능 개선 필요
        if not self.ddays:
            messagebox.showinfo("알림", "등록된 D-Day가 없습니다.")
            return None
        
        options = [f"{idx+1}. {name} ({date_obj.strftime('%Y-%m-%d')})" 
                  for idx, (name, date_obj) in enumerate(self.ddays)]
        
        dialog = SelectDialog(self, "D-Day 선택", "수정/삭제할 D-Day를 선택하세요:", options)
        self.wait_window(dialog)
        
        if dialog.result is not None:
            return (dialog.result, self.ddays[dialog.result])
        return None
    
    def update_dday_list(self):
        # 기존 위젯 삭제
        for widget in self.scrollable_frame.winfo_children():
            if widget != self.date_label:  # 날짜 레이블은 유지
                widget.destroy()
        
        # 현재 날짜 표시 업데이트
        self.date_label.config(text=f"오늘은 {self.today.year}년 {self.today.month}월 {self.today.day}일")
        
        # 현재 위치 표시 레이블
        position_label = ttk.Label(
            self.scrollable_frame,
            text="당신의 위치 ▼",
            font=('Malgun Gothic', 12),
            anchor='e'
        )
        position_label.pack(fill=tk.X, padx=10, pady=5)
        
        # D-Day가 없는 경우 메시지 표시
        if not self.ddays:
            no_dday_label = ttk.Label(
                self.scrollable_frame,
                text="등록된 D-Day가 없습니다. '추가' 버튼을 눌러 D-Day를 등록하세요.",
                font=('Malgun Gothic', 12)
            )
            no_dday_label.pack(pady=20)
            return
        
        # D-Day 목록 표시 (날짜 오름차순 정렬)
        sorted_ddays = sorted(self.ddays, key=lambda x: x[1])
        
        for idx, (name, date_obj) in enumerate(sorted_ddays):
            # D-Day 프레임 생성
            dday_frame = ttk.Frame(self.scrollable_frame)
            dday_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 남은 날짜 계산
            time_diff = date_obj - self.today
            days_left = time_diff.days
            
            # D-Day 텍스트 생성
            if days_left >= 0:
                dday_text = f"D-{days_left}"
            else:
                dday_text = f"D+{abs(days_left)}"
            
            # D-Day 이름 및 날짜 표시
            name_label = ttk.Label(
                dday_frame,
                text=f"{name} ({dday_text}): {date_obj.strftime('%Y-%m-%d')}",
                font=('Malgun Gothic', 11)
            )
            name_label.pack(anchor='w')
            
            # 프로그레스 바 프레임
            progress_frame = ttk.Frame(dday_frame)
            progress_frame.pack(fill=tk.X, pady=5)
            
            # 8주 기간 (앞뒤 4주) 프로그레스 바 생성
            self.create_weekly_progress_bar(progress_frame, date_obj)
    
    def create_weekly_progress_bar(self, parent_frame, target_date):
        # 오늘 날짜 기준 앞뒤 4주 계산
        start_date = self.today - timedelta(weeks=4)
        end_date = self.today + timedelta(weeks=4)
        
        # 타겟 날짜가 8주 범위를 벗어나는 경우 조정
        if target_date < start_date:
            # 타겟 날짜가 시작일보다 이전인 경우 (이미 지난 D-Day)
            weeks_diff = (start_date - target_date).days // 7
            if weeks_diff > 0:
                start_date = target_date
                end_date = target_date + timedelta(weeks=8)
        elif target_date > end_date:
            # 타겟 날짜가 종료일보다 이후인 경우 (먼 미래의 D-Day)
            weeks_diff = (target_date - end_date).days // 7
            if weeks_diff > 0:
                end_date = target_date
                start_date = target_date - timedelta(weeks=8)
        
        # 주차별 프레임 생성
        for week in range(9):  # 8주 + 구분선
            current_date = start_date + timedelta(weeks=week)
            
            # 주차 프레임
            week_frame = ttk.Frame(parent_frame)
            week_frame.pack(side=tk.LEFT, fill=tk.Y)
            
            # 현재 주가 타겟 날짜를 포함하는지 확인
            contains_target = False
            for day in range(7):
                day_date = current_date + timedelta(days=day)
                if day_date == target_date:
                    contains_target = True
                    break
            
            # 현재 주가 오늘 날짜를 포함하는지 확인
            contains_today = False
            for day in range(7):
                day_date = current_date + timedelta(days=day)
                if day_date == self.today:
                    contains_today = True
                    break
            
            # 주차 블록 생성
            if week == 4:  # 중앙 구분선
                separator = ttk.Separator(week_frame, orient='vertical')
                separator.pack(fill=tk.Y, padx=2, pady=2)
            else:
                # 주차 표시 (■ 사용)
                week_block = ttk.Label(
                    week_frame, 
                    text="■■■■■■■",
                    font=('Malgun Gothic', 10)
                )
                
                # 색상 설정
                if contains_target:
                    week_block.config(foreground='red')  # 타겟 날짜 포함 주는 빨간색
                elif contains_today:
                    week_block.config(foreground='blue')  # 오늘 날짜 포함 주는 파란색
                elif current_date <= self.today:
                    week_block.config(foreground='gray')  # 지난 주는 회색
                
                week_block.pack(padx=2)


class SelectDialog(tk.Toplevel):
    def __init__(self, parent, title, message, options):
        super().__init__(parent)
        self.transient(parent)  # 부모 창에 종속
        self.grab_set()  # 모달 창으로 설정
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        
        # 창 중앙에 위치
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (parent.winfo_rootx() + parent.winfo_width() // 2) - (width // 2)
        y = (parent.winfo_rooty() + parent.winfo_height() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # 메시지
        self.message_label = ttk.Label(self, text=message)
        self.message_label.pack(pady=10)
        
        # 리스트박스
        self.listbox = tk.Listbox(self, height=10, width=50)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 옵션 추가
        for option in options:
            self.listbox.insert(tk.END, option)
            
        # 더블 클릭 이벤트 바인딩
        self.listbox.bind("<Double-1>", self.on_double_click)
        
        # 버튼 프레임
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 확인 버튼
        self.ok_button = ttk.Button(self.button_frame, text="확인", command=self.on_ok)
        self.ok_button.pack(side=tk.LEFT, padx=5)
        
        # 취소 버튼
        self.cancel_button = ttk.Button(self.button_frame, text="취소", command=self.on_cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        self.result = None
        
    def on_double_click(self, event):
        self.on_ok()
        
    def on_ok(self):
        selection = self.listbox.curselection()
        if selection:
            self.result = selection[0]  # 선택된 인덱스
            self.destroy()
        else:
            messagebox.showinfo("알림", "항목을 선택하세요.")
            
    def on_cancel(self):
        self.result = None
        self.destroy()


class YearProgressApp:
    def __init__(self, root):
        self.root = root
        self.root.title("연간 진행률")

        width = 800
        height = 550  # D-Day 버튼을 위해 높이 증가
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

        self.root.configure(bg='black')

        # 날짜 표시를 위한 프레임
        self.date_frame = tk.Frame(root, bg='black')
        self.date_frame.pack(pady=20)
        
        # 오늘은
        self.date_prefix_label = tk.Label(
            self.date_frame,
            text="오늘은 ",
            fg='white',
            bg='black',
            font=('Malgun Gothic', 28, 'bold')
        )
        self.date_prefix_label.pack(side=tk.LEFT)
        
        # 날짜 부분 (노란색)
        self.date_colored_label = tk.Label(
            self.date_frame,
            text="",  # 업데이트 함수에서 설정
            fg='#FFFF00',  # 샛노란색
            bg='black',
            font=('Malgun Gothic', 28, 'bold')
        )
        self.date_colored_label.pack(side=tk.LEFT)
        
        # 입니다
        self.date_suffix_label = tk.Label(
            self.date_frame,
            text=" 입니다",
            fg='white',
            bg='black',
            font=('Malgun Gothic', 28, 'bold')
        )
        self.date_suffix_label.pack(side=tk.LEFT)

        self.progress_text_frame = tk.Frame(root, bg='black')
        self.progress_text_frame.pack()

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
        self.progress_frame.pack_propagate(False)

        self.gradient_frames = []
        for i in range(600):
            frame = tk.Frame(self.progress_frame, height=40, width=1)
            frame.pack(side=tk.LEFT)
            self.gradient_frames.append(frame)

        self.days_label = tk.Label(
            root,
            fg='white',
            bg='black',
            font=('Malgun Gothic', 24)
        )
        self.days_label.pack(pady=10)

        self.remaining_label = tk.Label(
            root,
            fg='#00BFFF',
            bg='black',
            font=('Malgun Gothic', 24)
        )
        self.remaining_label.pack()

        # D-Day 관리자 버튼 (기존의 추가 버튼 대체)
        self.dday_button_frame = tk.Frame(root, bg='black')
        self.dday_button_frame.pack(pady=20)
        
        # 높이가 더 큰 버튼 생성
        self.dday_manager_button = tk.Button(
            self.dday_button_frame, 
            text="D-Day 관리자 열기",
            font=('Malgun Gothic', 12),
            bg='#444444',
            fg='white',
            command=self.open_dday_manager,
            height=3,  # 버튼 높이를 명시적으로 지정
            width=20   # 버튼 너비 지정
        )
        self.dday_manager_button.pack()

        self.ddays = []  # D-Day 목록
        self.is_blinking = False
        self.load_ddays()  # D-Day 목록 불러오기
        self.update_progress()

    def open_dday_manager(self):
        manager = DDayManager(self.root, self.ddays)
        self.root.wait_window(manager)  # 관리자 창이 닫힐 때까지 기다림
        
        # D-Day 목록 업데이트 (창이 닫힌 후)
        if hasattr(manager, 'ddays'):
            self.ddays = manager.ddays
            self.save_ddays()  # 변경된 내용 저장
            self.update_progress()  # 화면 업데이트
    
    def update_ddays_from_manager(self, new_ddays):
        # D-Day 관리자에서 변경된 목록 적용
        self.ddays = new_ddays
        self.save_ddays()
        self.update_progress()

    def load_ddays(self):
        self.ddays = []
        if not os.path.exists("d-day.csv"):  # 파일 없으면 생성
            with open("d-day.csv", "w") as f:
                pass

        try:
            with open("d-day.csv", "r") as f:
                for line in f:
                    line = line.strip()
                    if line:  # 빈 줄 무시
                        parts = line.split(",")
                        if len(parts) >= 4:  # 유효한 포맷 확인
                            name, year, month, day = parts[0], parts[1], parts[2], parts[3]
                            try:
                                self.ddays.append((name, date(int(year), int(month), int(day))))
                            except ValueError:
                                # 잘못된 날짜 형식은 무시
                                pass
        except FileNotFoundError:
            pass  # 파일이 없으면 그냥 빈 리스트
        except Exception as e:
            messagebox.showerror("오류", f"d-day.csv 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
            self.ddays = []

    def save_ddays(self):
        try:
            with open("d-day.csv", "w") as f:
                for name, date_obj in self.ddays:
                    f.write(f"{name},{date_obj.year},{date_obj.month},{date_obj.day}\n")
        except Exception as e:
            messagebox.showerror("오류", f"d-day.csv 파일을 저장하는 중 오류가 발생했습니다: {str(e)}")

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

        # 날짜 부분만 노란색으로 설정
        date_colored = f"{current_date.year}년 {current_date.month}월 {current_date.day}일"
        self.date_colored_label.config(text=date_colored)
        
        self.year_label.config(text=f"당신의 {current_date.year}년은")
        self.progress_label.config(text=f"{progress:.1f}% 없어졌습니다")
        self.days_label.config(text=f"{days_passed}/{total_days}일")
        self.progress_label.config(text=f"{progress:.1f}% 없어졌습니다")
        self.days_label.config(text=f"{days_passed}/{total_days}일")

        # 가장 가까운 D-Day 찾기 (오늘 이후 날짜만)
        closest_dday = None
        closest_days_left = float('inf')  # 양의 무한대

        today = date.today()
        for name, date_obj in self.ddays:
            days = (date_obj - today).days
            if days >= 0 and days < closest_days_left:
                closest_days_left = days
                closest_dday = (name, date_obj)

        # 남은 날짜 및 깜빡임 효과
        if closest_dday:  # D-Day가 있으면
            if closest_days_left < 10 and not self.is_blinking:
                self.is_blinking = True
                self.blink_remaining_label()
            elif closest_days_left >= 10 and self.is_blinking:
                self.is_blinking = False
                self.remaining_label.config(fg='#00BFFF')

            self.remaining_label.config(text=f"{closest_dday[0]}까지 {closest_days_left}일 남음")

        else:  # D-Day 없으면
            self.remaining_label.config(text=f"{days_remaining}일 남음")  # 기본값 (연말 기준)
            if days_remaining < 10 and not self.is_blinking:  # 연말 기준 깜빡임
                self.is_blinking = True
                self.blink_remaining_label()
            elif days_remaining >= 10 and self.is_blinking:
                self.is_blinking = False
                self.remaining_label.config(fg='#00BFFF')

        # 진행률 바 그라데이션
        for i in range(600):
            if i / 600 < progress / 100:
                if progress < 30:
                    r = 255
                    g = int((progress / 30) * 255)
                    b = int((progress / 30) * 255)
                else:
                    r = int(0x4C + (0xAF - 0x4C) * (i / 600))
                    g = int(0xAF + (0x50 - 0xAF) * (i / 600))
                    b = int(0x50 + (0x50 - 0x50) * (i / 600))
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                self.gradient_frames[i].config(bg=hex_color)
            else:
                self.gradient_frames[i].config(bg='white')

        self.root.after(1000, self.update_progress)

    def blink_remaining_label(self):
        if self.is_blinking:
            current_color = self.remaining_label.cget('fg')
            new_color = 'black' if current_color == '#00BFFF' else '#00BFFF'
            self.remaining_label.config(fg=new_color)
            self.root.after(500, self.blink_remaining_label)


if __name__ == "__main__":
    root = tk.Tk()
    app = YearProgressApp(root)
    root.mainloop()
