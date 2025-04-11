# -*- coding: utf-8 -*-
# Copyright 2025 AidALL Inc. All rights reserved.

# 째깍째깍째깍째깍 feat. 똥방구쟁이
# - D-Day 관리 애플리케이션

# 빌드 명령어:
# Windows: pyinstaller dday.spec
# MacOS: python setup.py py2app
# Linux: pyinstaller linux.spec

# 의존성 설치: pip install -r requirements.txt

import flet as ft
import datetime
import json
import os
import calendar

# Flet 버전 확인 - 예외 처리 추가
try:
    import pkg_resources
    flet_version = pkg_resources.get_distribution("flet").version
    print(f"Flet version: {flet_version}")
except Exception as e:
    print(f"Flet 버전을 확인할 수 없습니다: {e}")
    flet_version = "unknown"

# DatePicker 지원 확인
print("Checking DatePicker support...")
try:
    datepicker_class = ft.DatePicker
    print(f"DatePicker class exists: {datepicker_class}")
    print(f"DatePicker attributes: {[attr for attr in dir(datepicker_class) if not attr.startswith('_')]}")
except Exception as e:
    print(f"DatePicker not supported: {e}")

DATA_FILE = 'dday_data.json'

def parse_date(date_input):
    """다양한 형식의 날짜 문자열을 파싱하여 YYYY-MM-DD 형식으로 반환"""
    date_input = date_input.strip()
    
    # 이미 YYYY-MM-DD 형식이면 그대로 반환
    if len(date_input) == 10 and date_input[4] == '-' and date_input[7] == '-':
        try:
            datetime.datetime.strptime(date_input, "%Y-%m-%d")
            return date_input
        except ValueError:
            pass
    
    # YYYY.MM.DD 형식
    if len(date_input) == 10 and date_input[4] == '.' and date_input[7] == '.':
        try:
            date_obj = datetime.datetime.strptime(date_input, "%Y.%m.%d")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # YYYYMMDD 형식 (숫자 8자리)
    if len(date_input) == 8 and date_input.isdigit():
        try:
            date_obj = datetime.datetime.strptime(date_input, "%Y%m%d")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # 다른 일반적인 날짜 형식도 시도
    for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y"]:
        try:
            date_obj = datetime.datetime.strptime(date_input, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # 파싱 실패 시 None 반환
    return None

def calculate_dday(date_str):
    """Calculates D-Day string from a date string (YYYY-MM-DD)."""
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        delta = target_date - today
        days = delta.days
        if days == 0:
            return "D-Day"
        elif days > 0:
            return f"D-{days}"
        else:
            return f"D+{abs(days)}"
    except ValueError:
        return "날짜 오류" # Error with date format

def load_data():
    """Loads D-Day data from the JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                # Ensure loaded data is a list of dictionaries
                data = json.load(f)
                if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    return data
                else:
                    print("Warning: Data file does not contain a valid list of events. Starting fresh.")
                    return []
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading data: {e}") # Print error to console
            return [] # Return empty list on error
    return [] # Return empty list if file doesn't exist

def save_data(data):
    """Saves D-Day data to the JSON file."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        print(f"Error saving data: {e}") # Print error to console
        return False


class DDayManager:
    def __init__(self, page: ft.Page):
        self.page = page
        
        # 제거: 페이지 속성 설정(window_width, window_height)은 main 함수에서만 처리
        self.page.title = "째깍째깍째깍째깍 feat. 똥방구쟁이"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        
        # 데이터 및 상태 관리
        self.events = load_data()
        self.selected_event_data = None
        
        # 현재 선택 중인 날짜 필드 저장용
        self.current_date_field = None
        
        # 현재/지나간 일정 표시 모드
        self.show_past_events = False
        
        # 연간 진행률 화면 표시 상태
        self.show_year_progress = False

        # UI 요소 초기화
        self.init_ui()
        
        # 초기 테이블 정렬 및 채우기
        self.sort_and_populate()

    def init_ui(self):
        """UI 요소 초기화"""
        # 텍스트 스타일 정의
        self.text_style = ft.TextStyle(
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.NORMAL,
            size=16
        )
        
        self.hint_style = ft.TextStyle(
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.NORMAL,
            size=14
        )

        # 일정 추가 위한 TextField
        self.new_event_name = self.create_text_field(
            label="일정명", 
            on_submit=self.save_new_event
        )
        
        # 날짜 선택 버튼 (추가)
        self.new_date_picker_btn = self.create_icon_button(
            icon=ft.icons.CALENDAR_MONTH,
            tooltip="달력에서 선택",
            on_click=lambda e: self.show_date_picker(self.new_event_date_str)
        )
        
        # 날짜 입력 필드와 달력 버튼을 묶은 행 (추가)
        self.new_event_date_str = None  # 직접 참조할 수 있도록 변수 추가
        self.new_date_row = ft.Row(
            [
                self.create_text_field(
                    label="날짜", 
                    hint_text="예: 2024-12-25",
                    is_date=True,
                    on_submit=self.save_new_event,
                    ref=lambda x: setattr(self, 'new_event_date_str', x)
                ),
                self.new_date_picker_btn
            ],
            visible=False,
            spacing=0,
            alignment=ft.MainAxisAlignment.START
        )
        
        # 저장/취소 버튼
        self.save_btn = self.create_button(
            text="저장", 
            on_click=self.save_new_event, 
            is_primary=True
        )
        self.cancel_btn = self.create_button(
            text="취소", 
            on_click=self.cancel_add_form, 
            is_primary=False
        )
        
        # 입력 폼 컨테이너
        self.add_form = self.create_form_container(
            title="새 D-Day 추가",
            fields=[self.new_event_name, self.new_date_row],
            buttons=[self.save_btn, self.cancel_btn]
        )
        
        # 수정 폼 
        self.edit_event_name = self.create_text_field(
            label="일정명", 
            on_submit=self.update_event
        )
        
        # 수정 날짜 선택 버튼
        self.edit_date_picker_btn = self.create_icon_button(
            icon=ft.icons.CALENDAR_MONTH,
            tooltip="달력에서 선택",
            on_click=lambda e: self.show_date_picker(self.edit_event_date_str)
        )
        
        # 수정 날짜 입력 필드와 달력 버튼을 묶은 행
        self.edit_event_date_str = None  # 직접 참조할 수 있도록 변수 추가
        self.edit_date_row = ft.Row(
            [
                self.create_text_field(
                    label="날짜", 
                    hint_text="예: 2024-12-25",
                    is_date=True,
                    on_submit=self.update_event,
                    ref=lambda x: setattr(self, 'edit_event_date_str', x)
                ),
                self.edit_date_picker_btn
            ],
            visible=False,
            spacing=0,
            alignment=ft.MainAxisAlignment.START
        )
        
        # 수정/취소 버튼
        self.update_btn = self.create_button(
            text="수정", 
            on_click=self.update_event, 
            is_primary=True
        )
        self.cancel_edit_btn = self.create_button(
            text="취소", 
            on_click=self.cancel_edit_form, 
            is_primary=False
        )
        
        # 수정 폼 컨테이너
        self.edit_form = self.create_form_container(
            title="D-Day 수정",
            fields=[self.edit_event_name, self.edit_date_row],
            buttons=[self.update_btn, self.cancel_edit_btn]
        )

        # 정렬 드롭다운
        self.sort_dropdown = ft.Dropdown(
            label="정렬 기준",
            options=[
                ft.dropdown.Option("급한 순서"),
                ft.dropdown.Option("이름순"),
            ],
            value="급한 순서",
            width=150,
            on_change=self.sort_and_populate
        )
        
        # 지나간 일정 정렬 드롭다운
        self.past_sort_dropdown = ft.Dropdown(
            label="정렬 기준",
            options=[
                ft.dropdown.Option("날짜순"),
                ft.dropdown.Option("이름순"),
            ],
            value="날짜순",
            width=200,
            visible=False,
            on_change=self.sort_and_populate
        )

        # 지나간 일정 전환 버튼
        self.toggle_past_events_btn = ft.ElevatedButton(
            text="지나간 일정 보기",
            on_click=self.toggle_past_events,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.INDIGO,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
        )

        # 연간 진행률 버튼 추가
        self.year_progress_btn = ft.ElevatedButton(
            text="올해 진행률 보기",
            on_click=self.toggle_year_progress,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.PURPLE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
        )

        # 수정 버튼
        self.edit_button = ft.IconButton(
            ft.Icons.EDIT,
            tooltip="선택한 D-Day 수정",
            on_click=self.show_edit_form,
            disabled=True
        )

        # 삭제 버튼
        self.delete_button = ft.IconButton(
            ft.Icons.DELETE_OUTLINE,
            tooltip="선택한 D-Day 삭제",
            on_click=self.open_delete_dialog,
            disabled=True
        )

        # 이벤트 테이블
        self.events_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("일정명", color=ft.Colors.BLACK, size=14)),
                ft.DataColumn(ft.Text("날짜", color=ft.Colors.BLACK, size=14)),
                ft.DataColumn(ft.Text("D-Day", color=ft.Colors.BLACK, size=14)),
            ],
            width=750,                          # 테이블 전체 너비
            column_spacing=20,                  # 컬럼 간격
            horizontal_lines=ft.border.BorderSide(1, "grey"),
            vertical_lines=ft.border.BorderSide(1, "grey"),
            heading_row_color=ft.Colors.AMBER_100,
            border=ft.border.all(1, "grey"),
            data_row_min_height=25,             # 행 높이 조정
            data_row_max_height=45,             # 행 높이 조정
            heading_row_height=25,              # 헤더 행 높이 조정
            expand=False                        # 자동 확장 비활성화
        )

        # 연간 진행률 컨테이너
        self.year_progress_container = self.create_year_progress_ui()
        self.year_progress_container.visible = False

        # 메인 레이아웃 구성
        self.page.add(
            ft.Column(
                [
                    ft.Row([
                        self.toggle_past_events_btn,
                        self.year_progress_btn,
                        self.sort_dropdown,
                        self.past_sort_dropdown,
                        self.edit_button, 
                        self.delete_button
                    ], alignment=ft.MainAxisAlignment.START, spacing=10, height=65),
                    ft.Row(
                        [
                            # 왼쪽: 이벤트 테이블
                            ft.Container(
                                content=self.events_table,
                                expand=True,
                            ),
                            # 오른쪽: 폼 영역
                            ft.Container(
                                content=ft.Column(
                                    [
                                        self.add_form,
                                        self.edit_form
                                    ],
                                    spacing=10,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                width=250,
                                padding=10,
                                alignment=ft.alignment.top_center
                            )
                        ],
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.START
                    ),
                    # 연간 진행률 컨테이너 추가
                    self.year_progress_container
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO
            )
        )

        # 추가 버튼 (FAB) - 항상 보이도록 레이아웃 맨 아래 배치
        self.page.floating_action_button = ft.FloatingActionButton(
            content=ft.Icon(ft.Icons.ADD),
            bgcolor=ft.Colors.BLUE,
            tooltip="새 D-Day 추가",
            on_click=self.show_add_form
        )

    def toggle_form_visibility(self, form, name_field, date_row, buttons, is_visible, initial_values=None):
        """폼 가시성 전환 (표시/숨김) - 추가 및 수정 폼에 공통 사용"""
        # 모든 폼 숨기기 (하나만 보이게 하기 위해)
        self.add_form.visible = False
        self.edit_form.visible = False
        
        # 초기화 전에 UI 업데이트하여 폼이 사라지도록
        self.page.update()
        
        if is_visible:
            # 폼 초기화 및 표시
            name_field.value = initial_values['name'] if initial_values else ""
            
            # 날짜 필드 직접 참조
            date_field = date_row.controls[0]
            date_field.value = initial_values['date'] if initial_values else ""
            
            name_field.error_text = None
            date_field.error_text = None
        
        # 폼 요소들 가시성 설정
        name_field.visible = is_visible
        date_row.visible = is_visible
        date_row.controls[0].visible = is_visible  # 날짜 필드
        date_row.controls[1].visible = is_visible  # 달력 버튼
        
        for btn in buttons:
            btn.visible = is_visible
            
        form.visible = is_visible
        
        # UI 업데이트
        self.page.update()
        
        # 로그 출력
        action = "opened" if is_visible else "closed"
        form_name = "Add form" if form == self.add_form else "Edit form"
        print(f"{form_name} {action}")

    def show_add_form(self, e):
        """일정 추가 폼 표시"""
        print("show_add_form called")  # 디버깅용 로그
        self.toggle_form_visibility(
            self.add_form, 
            self.new_event_name, 
            self.new_date_row, 
            [self.save_btn, self.cancel_btn], 
            True
        )

    def cancel_add_form(self, e):
        """일정 추가 폼 취소"""
        print("cancel_add_form called")  # 디버깅용 로그
        self.toggle_form_visibility(
            self.add_form, 
            self.new_event_name, 
            self.new_date_row, 
            [self.save_btn, self.cancel_btn], 
            False
        )

    def validate_event_data(self, name_field, date_field):
        """일정 데이터 유효성 검사 (추가 및 수정에 공통으로 사용)"""
        # None 체크 추가
        if not name_field:
            print("Name field is None")
            self.show_snackbar("이름 필드가 유효하지 않습니다", ft.Colors.RED)
            return None, None
            
        if not date_field:
            print("Date field is None")
            self.show_snackbar("날짜 필드가 유효하지 않습니다", ft.Colors.RED)
            return None, None
            
        print(f"Name field: {name_field}, type: {type(name_field)}")
        print(f"Date field: {date_field}, type: {type(date_field)}")
        
        name = name_field.value.strip() if hasattr(name_field, 'value') and name_field.value else ""
        date_input = date_field.value.strip() if hasattr(date_field, 'value') and date_field.value else ""
        
        print(f"Name value: '{name}'")
        print(f"Date value: '{date_input}'")
        
        # 입력값 검증
        if not name:
            name_field.error_text = "일정 이름을 입력하세요"
            self.page.update()
            return None, None
        
        if not date_input:
            date_field.error_text = "날짜를 입력하세요"
            self.page.update()
            return None, None

        # 날짜 형식 검증 - 다양한 형식 지원
        formatted_date = parse_date(date_input)
        if not formatted_date:
            date_field.error_text = "인식할 수 없는 날짜 형식입니다"
            self.page.update()
            return None, None
            
        return name, formatted_date

    def save_new_event(self, e):
        """새 일정 저장"""
        print("save_new_event called")  # 디버깅용 로그
        print(f"Event parameter: {e}")
        print(f"Event type: {type(e)}")
        
        # new_event_date_str 참조 확인
        print(f"new_event_date_str: {self.new_event_date_str}")
        
        # 날짜 필드가 None인 경우 직접 가져오기
        if self.new_event_date_str is None:
            print("직접 날짜 필드 참조 시도")
            try:
                self.new_event_date_str = self.new_date_row.controls[0]
                print(f"날짜 필드 가져옴: {self.new_event_date_str}")
            except Exception as ex:
                print(f"날짜 필드 가져오기 실패: {ex}")
        
        try:
            # 데이터 유효성 검사
            name, formatted_date = self.validate_event_data(self.new_event_name, self.new_event_date_str)
            if not name or not formatted_date:
                print("유효성 검사 실패")
                return
                
            # 이벤트 추가
            new_event = {'name': name, 'date': formatted_date}
            self.events.append(new_event)
            print(f"Event added: {new_event}")  # 디버깅용 로그
            
            # 데이터 저장
            save_result = save_data(self.events)
            print(f"Save result: {save_result}")  # 디버깅용 로그
            
            if save_result:
                self.show_snackbar("일정이 추가되었습니다")
            else:
                self.show_snackbar("일정 저장 중 오류가 발생했습니다", ft.Colors.RED)
            
            # 테이블 업데이트
            self.sort_and_populate()
            
            # 폼 닫기
            self.cancel_add_form(None)
        except Exception as ex:
            print(f"일정 저장 오류: {ex}")
            import traceback
            print(traceback.format_exc())  # 스택 트레이스 출력
            self.show_snackbar(f"일정 저장 중 문제가 발생했습니다: {str(ex)}", ft.Colors.RED)

    def show_edit_form(self, e):
        """일정 수정 폼 표시"""
        if self.selected_event_data:
            self.toggle_form_visibility(
                self.edit_form, 
                self.edit_event_name, 
                self.edit_date_row, 
                [self.update_btn, self.cancel_edit_btn], 
                True,
                self.selected_event_data
            )
        else:
            self.show_snackbar("수정할 일정을 선택해주세요", ft.Colors.AMBER)

    def cancel_edit_form(self, e):
        """일정 수정 폼 취소"""
        print("cancel_edit_form called")  # 디버깅용 로그
        self.toggle_form_visibility(
            self.edit_form, 
            self.edit_event_name, 
            self.edit_date_row, 
            [self.update_btn, self.cancel_edit_btn], 
            False
        )

    def update_event(self, e):
        """일정 수정"""
        if self.selected_event_data:
            # 날짜 필드 참조가 없는 경우 직접 가져오기
            if not self.edit_event_date_str:
                self.edit_event_date_str = self.edit_date_row.controls[0]
                
            # 데이터 유효성 검사
            name, formatted_date = self.validate_event_data(self.edit_event_name, self.edit_event_date_str)
            if not name or not formatted_date:
                return
                
            # 이벤트 업데이트
            self.selected_event_data['name'] = name
            self.selected_event_data['date'] = formatted_date
            
            # 데이터 저장
            if save_data(self.events):
                self.show_snackbar("일정이 수정되었습니다")
            else:
                self.show_snackbar("일정 수정 중 오류가 발생했습니다", ft.Colors.RED)
            
            # 테이블 업데이트
            self.sort_and_populate()
            
            # 폼 닫기
            self.cancel_edit_form(None)
        else:
            self.show_snackbar("수정할 일정을 선택해주세요", ft.Colors.AMBER)

    def open_delete_dialog(self, e):
        """삭제 기능 - 직접 삭제 구현"""
        print("삭제 버튼 클릭됨")
        if self.selected_event_data:
            event_name = self.selected_event_data.get('name', '')
            event_date = self.selected_event_data.get('date', '')
            print(f"선택된 일정: {event_name} ({event_date})")
            
            # 직접 삭제 수행
            try:
                # 이벤트 목록에서 선택된 이벤트 제거
                self.events.remove(self.selected_event_data)
                print(f"목록에서 '{event_name}' 제거 성공")
                
                # 데이터 저장
                save_result = save_data(self.events)
                print(f"데이터 저장 결과: {save_result}")
                
                if save_result:
                    self.show_snackbar(f"'{event_name}' 일정이 삭제되었습니다")
                else:
                    self.show_snackbar("일정 저장 중 오류가 발생했습니다", ft.Colors.RED)
                
                # 선택 상태 초기화
                self.selected_event_data = None
                self.edit_button.disabled = True
                self.delete_button.disabled = True
                
                # 테이블 새로고침
                self.sort_and_populate()
                print("데이터 삭제 완료 및 UI 업데이트됨")
            except ValueError:
                print(f"목록에서 일정을 찾을 수 없음")
                self.show_snackbar("선택한 일정을 찾을 수 없습니다", ft.Colors.RED)
            except Exception as ex:
                print(f"삭제 중 예외 발생: {ex}")
                import traceback
                print(traceback.format_exc())
                self.show_snackbar(f"삭제 중 오류: {str(ex)}", ft.Colors.RED)
        else:
            print("선택된 일정이 없음")
            self.show_snackbar("삭제할 일정을 선택해주세요", ft.Colors.AMBER)

    # --- 테이블 관련 메서드 ---
    def handle_row_select(self, e):
        """행 선택 처리"""
        is_selected = e.data == 'true'
        row_cells = e.control.cells
        event_name = row_cells[0].content.value
        event_date = row_cells[1].content.value

        if is_selected:
            # 선택된 이벤트 데이터 찾기
            found_event = None
            for event in self.events:
                if event.get('name') == event_name and event.get('date') == event_date:
                    found_event = event
                    break
            
            self.selected_event_data = found_event
            self.delete_button.disabled = False
            self.edit_button.disabled = False
            
            # 다른 행 선택 해제 및 색상 초기화
            for row in self.events_table.rows:
                if row != e.control:
                    row.selected = False
                    self.reset_row_colors(row)
                else:
                    # 선택된 행 색상 변경
                    self.highlight_selected_row(row)
        else:
            # 선택 해제된 경우
            self.selected_event_data = None
            self.delete_button.disabled = True
            self.edit_button.disabled = True
            # 색상 초기화
            self.reset_row_colors(e.control)

        self.page.update()
        
    def highlight_selected_row(self, row):
        """선택된 행 하이라이트"""
        for cell in row.cells:
            # 셀 배경색 설정
            cell.bgcolor = ft.Colors.BLUE_50
            # 텍스트 설정
            if hasattr(cell.content, 'weight'):
                cell.content.weight = ft.FontWeight.BOLD
            if hasattr(cell.content, 'color') and not "D+" in (cell.content.value or ""):
                cell.content.color = ft.Colors.BLUE_900
    
    def reset_row_colors(self, row):
        """행 색상 초기화"""
        for cell in row.cells:
            cell.bgcolor = None
            # 텍스트 스타일 초기화
            if hasattr(cell.content, 'weight'):
                cell.content.weight = ft.FontWeight.NORMAL
            if hasattr(cell.content, 'color'):
                if "D+" in (cell.content.value or ""):
                    cell.content.color = ft.Colors.RED
                elif "날짜 오류" in (cell.content.value or ""):
                    cell.content.color = ft.Colors.RED
                else:
                    cell.content.color = ft.Colors.BLACK

    def populate_table(self):
        """테이블 데이터 채우기"""
        self.events_table.rows.clear()
        current_selection_still_exists = False
        today = datetime.date.today()
        
        for event in self.events:
            # 날짜 파싱
            try:
                event_date = datetime.datetime.strptime(event['date'], "%Y-%m-%d").date()
                # 지나간 일정 여부 확인
                is_past_event = event_date < today
                
                # 현재 표시 모드에 따라 필터링
                if (self.show_past_events and not is_past_event) or (not self.show_past_events and is_past_event):
                    continue
                
                dday_str = calculate_dday(event['date'])
                
                # D+ 표시인 경우 빨간색으로
                text_color = ft.Colors.RED if "D+" in dday_str else ft.Colors.BLACK
                
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(event['name'], size=14, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)),
                        ft.DataCell(ft.Text(event['date'], size=14, no_wrap=True)),
                        ft.DataCell(ft.Text(dday_str, size=14, color=text_color, no_wrap=True)),
                    ],
                    on_select_changed=self.handle_row_select
                )
                
                # 이전에 선택된 행이 있으면 선택 상태 유지
                if self.selected_event_data == event:
                    row.selected = True
                    current_selection_still_exists = True
                    
                self.events_table.rows.append(row)
            except ValueError:
                # 날짜 형식 오류 - 항상 표시
                dday_str = "날짜 오류"
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(event['name'], size=14, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)),
                        ft.DataCell(ft.Text(event['date'], size=14, color=ft.Colors.RED, no_wrap=True)),
                        ft.DataCell(ft.Text(dday_str, size=14, color=ft.Colors.RED, no_wrap=True)),
                    ],
                    on_select_changed=self.handle_row_select
                )
                
                if not self.show_past_events:  # 현재 일정 모드에서만 표시
                    if self.selected_event_data == event:
                        row.selected = True
                        current_selection_still_exists = True
                    self.events_table.rows.append(row)

        # 선택된 항목이 더 이상 존재하지 않으면 선택 상태 초기화
        if not current_selection_still_exists and self.selected_event_data is not None:
            self.selected_event_data = None
            self.delete_button.disabled = True
            self.edit_button.disabled = True

    def sort_and_populate(self, e=None):
        """정렬 기준에 따라 데이터 정렬 및 테이블 업데이트"""
        today = datetime.date.today()
        
        if self.show_past_events:
            # 지나간 일정 정렬 옵션
            sort_key = self.past_sort_dropdown.value
            
            if sort_key == "날짜순":
                # 날짜순 정렬 (최근 날짜가 위로)
                def get_date(event):
                    try:
                        date_str = event.get('date', '')
                        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        # 날짜 형식이 잘못된 경우 가장 오래된 날짜로 정렬
                        return datetime.date(1900, 1, 1)
                        
                self.events.sort(key=get_date, reverse=True)
            elif sort_key == "이름순":
                self.events.sort(key=lambda x: x.get('name', '').lower())
        else:
            # 현재 일정 정렬 옵션
            sort_key = self.sort_dropdown.value
            
            if sort_key == "급한 순서":
                def get_days_diff(event):
                    try:
                        date_str = event.get('date', '')
                        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                        # 과거 일정은 하단에 정렬
                        if event_date < today:
                            return float('inf')
                        return (event_date - today).days
                    except ValueError:
                        # 날짜 형식이 잘못된 경우 최하위로 정렬
                        return float('inf')
                        
                self.events.sort(key=get_days_diff)
            elif sort_key == "이름순":
                # 현재 일정만 정렬
                current_events = [e for e in self.events if try_parse_date(e.get('date', '')) >= today]
                past_events = [e for e in self.events if try_parse_date(e.get('date', '')) < today]
                
                current_events.sort(key=lambda x: x.get('name', '').lower())
                past_events.sort(key=lambda x: x.get('name', '').lower())
                
                self.events = current_events + past_events

        # 테이블 데이터 갱신
        self.populate_table()
        self.page.update()

    # --- 유틸리티 메서드 ---
    def show_snackbar(self, message, color=ft.Colors.GREEN):
        """스낵바 메시지 표시"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_date_picker(self, date_field):
        """DatePicker 표시 - 속성을 명시적으로 설정"""
        # 현재 날짜 필드 기억 
        self.current_date_field = date_field
        print(f"현재 날짜 필드 설정: {date_field}, ID: {id(date_field)}")
        
        # 날짜 선택 시 호출되는 함수
        def handle_date_change(e):
            print("================ 날짜 선택 이벤트 발생! ================")
            print(f"현재 날짜 필드: {self.current_date_field}, ID: {id(self.current_date_field) if self.current_date_field else None}")
            
            try:
                if hasattr(e, 'data') and e.data:
                    print(f"이벤트 데이터: {e.data}")
                    
                    if isinstance(e.data, str):
                        if 'T' in e.data:
                            formatted_date = e.data.split('T')[0]
                        else:
                            formatted_date = e.data
                        
                        # 직접 필드 참조 시도
                        target_field = None
                        
                        # 1. self.current_date_field 사용
                        if self.current_date_field is not None:
                            target_field = self.current_date_field
                            print(f"현재 필드 참조 사용")
                        # 2. new_event_date_str 확인
                        elif self.new_date_row.visible:
                            target_field = self.new_date_row.controls[0]
                            print(f"new_date_row 사용 (추가 폼)")
                        # 3. edit_event_date_str 확인
                        elif self.edit_date_row.visible:
                            target_field = self.edit_date_row.controls[0] 
                            print(f"edit_date_row 사용 (수정 폼)")
                        
                        if target_field:
                            print(f"타겟 필드: {target_field}, ID: {id(target_field)}")
                            target_field.value = formatted_date
                            target_field.error_text = None
                            self.page.update()
                            print(f"날짜 설정됨: {formatted_date}")
                            self.show_snackbar(f"날짜가 설정되었습니다: {formatted_date}", ft.Colors.GREEN)
                        else:
                            print("사용할 날짜 필드를 찾을 수 없습니다")
                            self.show_snackbar("날짜 필드를 찾을 수 없습니다", ft.Colors.RED)
            except Exception as ex:
                print(f"날짜 변경 처리 오류: {ex}")
                import traceback
                print(traceback.format_exc())
                self.show_snackbar(f"날짜 처리 오류: {str(ex)}", ft.Colors.RED)
        
        # 닫기 이벤트 처리 함수
        def handle_dismiss(e):
            print("DatePicker 닫힘")
            
        try:
            print("DatePicker 열기 시도")
            
            # 클로저에서 현재 필드를 안전하게 유지하기 위한 참조 복사
            _current_field = date_field
            
            date_picker = ft.DatePicker(
                on_change=handle_date_change,
                on_dismiss=handle_dismiss,
                first_date=datetime.datetime(2000, 1, 1),
                last_date=datetime.datetime(2100, 12, 31),
                help_text="날짜를 선택하세요",
                cancel_text="취소",
                confirm_text="확인"
            )
            
            # DatePicker에 필드 정보 저장
            if hasattr(date_picker, '_field_ref'):
                date_picker._field_ref = _current_field
                print(f"DatePicker에 필드 참조 저장: {id(_current_field)}")
            
            self.page.overlay.append(date_picker)
            self.page.update()
            self.page.open(date_picker)
            print("DatePicker가 열렸습니다")
            
        except Exception as e:
            print(f"DatePicker 오류: {e}")
            self.show_snackbar(f"달력 오류: {str(e)}", ft.Colors.RED)

    def create_text_field(self, label, hint_text=None, is_date=False, on_submit=None, ref=None):
        """텍스트 필드 생성 헬퍼 함수"""
        return ft.TextField(
            label=label, 
            hint_text=hint_text,
            hint_style=self.hint_style if hint_text else None,
            keyboard_type=ft.KeyboardType.DATETIME if is_date else None,
            expand=True if is_date else None,
            text_style=self.text_style,
            label_style=ft.TextStyle(color=ft.Colors.BLACK),
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
            bgcolor=ft.Colors.WHITE,
            on_submit=on_submit,
            visible=False,
            ref=ref,
            width=180 if is_date else None
        )
        
    def create_button(self, text, on_click, is_primary=True):
        """버튼 생성 헬퍼 함수"""
        if is_primary:
            return ft.ElevatedButton(
                text=text, 
                on_click=on_click, 
                visible=False,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=70
            )
        else:
            return ft.OutlinedButton(
                text=text, 
                on_click=on_click, 
                visible=False,
                style=ft.ButtonStyle(
                    color=ft.Colors.BLUE,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=70
            )
            
    def create_icon_button(self, icon, tooltip, on_click):
        """아이콘 버튼 생성 헬퍼 함수"""
        return ft.IconButton(
            icon=icon,
            tooltip=tooltip,
            visible=False,
            on_click=on_click
        )
        
    def create_form_container(self, title, fields, buttons):
        """폼 컨테이너 생성 헬퍼 함수"""
        column_items = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)]
        column_items.extend(fields)
        column_items.append(ft.Row(buttons, spacing=10, alignment=ft.MainAxisAlignment.END))
        
        return ft.Container(
            content=ft.Column(
                column_items, 
                spacing=20,
                width=220
            ),
            visible=False,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(2, ft.Colors.BLUE_300),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.GREY_700,
                offset=ft.Offset(0, 0),
            )
        )

    def toggle_past_events(self, e):
        """현재 일정과 지나간 일정 간 전환"""
        self.show_past_events = not self.show_past_events
        
        # 버튼 텍스트와 드롭다운 변경
        if self.show_past_events:
            self.toggle_past_events_btn.text = "현재 일정 보기"
            self.sort_dropdown.visible = False
            self.past_sort_dropdown.visible = True
            self.page.floating_action_button.visible = False  # 지나간 일정에서는 추가 버튼 숨김
        else:
            self.toggle_past_events_btn.text = "지나간 일정 보기"
            self.sort_dropdown.visible = True
            self.past_sort_dropdown.visible = False
            self.page.floating_action_button.visible = True  # 현재 일정에서는 추가 버튼 표시
        
        # 선택 초기화
        self.selected_event_data = None
        self.edit_button.disabled = True
        self.delete_button.disabled = True
        
        # 테이블 다시 채우기
        self.sort_and_populate()
        
        self.page.update()

    def create_year_progress_ui(self):
        """연간 진행률 UI 생성"""
        # 오늘 날짜 가져오기
        today = datetime.date.today()
        
        # 제목 텍스트
        title_text = ft.Text(
            f"오늘은 {today.year}년 {today.month}월 {today.day}일 입니다",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE
        )
        
        # 연간 진행률 계산
        current_year = today.year
        total_days = 366 if calendar.isleap(current_year) else 365
        
        year_end = datetime.date(current_year, 12, 31)
        days_remaining = (year_end - today).days
        days_passed = total_days - days_remaining
        progress = (days_passed / total_days) * 100
        
        # 진행률 텍스트
        year_label = ft.Text(
            f"당신의 {current_year}년은",
            size=24,
            color=ft.Colors.WHITE
        )
        
        progress_label = ft.Text(
            f"{progress:.1f}% 없어졌습니다",
            size=36,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.RED
        )
        
        days_label = ft.Text(
            f"{days_passed}/{total_days}일",
            size=22,
            color=ft.Colors.WHITE
        )
        
        # 남은 일수 레이블
        remaining_label = ft.Text(
            f"{days_remaining}일 남음",
            size=22,
            color=ft.Colors.BLUE
        )
        
        # 가장 가까운 D-Day 찾기
        closest_dday = None
        closest_days_left = float('inf')
        
        for event in self.events:
            try:
                event_date = datetime.datetime.strptime(event.get('date', ''), "%Y-%m-%d").date()
                days_left = (event_date - today).days
                if days_left >= 0 and days_left < closest_days_left:
                    closest_days_left = days_left
                    closest_dday = event
            except ValueError:
                continue
        
        # 가장 가까운 D-Day가 있으면 표시
        if closest_dday:
            remaining_label.value = f"{closest_dday.get('name', '')}까지 {closest_days_left}일 남음"
        
        # 프로그레스 바
        progress_bar = ft.ProgressBar(
            width=650,
            height=30,
            value=progress/100,
            color=ft.Colors.RED_400,
            bgcolor=ft.Colors.GREY_300
        )
        
        # 닫기 버튼
        close_button = ft.ElevatedButton(
            text="돌아가기",
            on_click=self.toggle_year_progress,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
        )
        
        # 컨테이너에 모든 요소 배치
        return ft.Container(
            content=ft.Column(
                [
                    title_text,
                    ft.Container(height=20),
                    year_label,
                    progress_label,
                    ft.Container(height=20),
                    progress_bar,
                    ft.Container(height=20),
                    days_label,
                    remaining_label,
                    ft.Container(height=30),
                    close_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            width=750,
            height=500,
            padding=30,
            margin=ft.margin.only(top=20),
            bgcolor=ft.Colors.BLACK,
            border_radius=10,
            alignment=ft.alignment.center
        )
    
    def toggle_year_progress(self, e=None):
        """연간 진행률 화면 전환"""
        # 화면 상태 변경
        self.show_year_progress = not self.show_year_progress
        
        # 메인 컨텐츠와 연간 진행률 화면 전환
        self.events_table.visible = not self.show_year_progress
        self.add_form.visible = False
        self.edit_form.visible = False
        
        for row in self.page.controls[0].controls[1].controls:
            row.visible = not self.show_year_progress
            
        # 버튼 상태 변경
        if self.show_year_progress:
            self.year_progress_btn.text = "일정 보기로 돌아가기"
            self.toggle_past_events_btn.visible = False
            self.sort_dropdown.visible = False
            self.past_sort_dropdown.visible = False
            self.edit_button.visible = False
            self.delete_button.visible = False
            self.page.floating_action_button.visible = False
            
            # 연간 진행률 표시 업데이트
            self.update_year_progress()
        else:
            self.year_progress_btn.text = "올해 진행률 보기"
            self.toggle_past_events_btn.visible = True
            self.sort_dropdown.visible = not self.show_past_events
            self.past_sort_dropdown.visible = self.show_past_events
            self.edit_button.visible = True
            self.delete_button.visible = True
            self.page.floating_action_button.visible = not self.show_past_events
        
        # 연간 진행률 컨테이너 표시/숨김
        self.year_progress_container.visible = self.show_year_progress
        
        self.page.update()
    
    def update_year_progress(self):
        """연간 진행률 정보 업데이트"""
        if not self.show_year_progress:
            return
            
        # 새로운 연간 진행률 UI로 교체
        new_progress_container = self.create_year_progress_ui()
        new_progress_container.visible = True
        
        # 기존 컨테이너를 새 것으로 교체
        container_index = self.page.controls[0].controls.index(self.year_progress_container)
        self.page.controls[0].controls[container_index] = new_progress_container
        self.year_progress_container = new_progress_container
        
        self.page.update()


def try_parse_date(date_str):
    """날짜 문자열을 파싱하여 date 객체로 반환, 실패시 최소 날짜 반환"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return datetime.date(1900, 1, 1)  # 최소 날짜 반환

def main(page: ft.Page):
    """앱 메인 함수"""
    # 페이지 기본 설정 - 최소한의 필수 설정만 유지
    page.title = "D-Day 관리"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # 창 크기 설정을 제거하고 반응형 레이아웃에 집중
    
    # 앱 인스턴스 생성 및 시작
    app = DDayManager(page)


# 애플리케이션 실행 - 기본 설정으로만 실행
ft.app(target=main) 