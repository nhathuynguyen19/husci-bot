from tabulate import *

class StudySection():
    date = {
        'day' : 0,
        'month' : 0,
        'year' : 0
    }
    time = {
        'hour' : 0,
        'minute' : 0
    }
    date_time = {
        'date' : date,
        'time' : time
    }
    id_study_section = ''
    name_outline = ''
    credits_number = 0
    approval_date = date_time
    id_teacher = ''
    def __init__(self, id_study_section, name_outline, credits_number, approval_date, id_teacher) -> None:
        self.id_study_section = id_study_section
        self.name_outline = name_outline
        self.credits_number = credits_number
        self.approval_date = approval_date
        self.id_teacher = id_teacher
    def __str__(self) -> str:
        if self.approval_date != '':
            return f'Mã học phần là {self.id_study_section}, Tên đề cương là {self.name_outline}, Số tín chỉ là {self.credits_number}, Ngày duyệt là {self.approval_date['date']['day']:02d}/{self.approval_date['date']['month']:02d}/{self.approval_date['date']['year']:02d} {self.approval_date['time']['hour']:02d}:{self.approval_date['time']['minute']:02d}, Mã giảng viên là {self.id_teacher}'
        else:
            return f'Mã học phần là {self.id_study_section}, Tên đề cương là {self.name_outline}, Số tín chỉ là {self.credits_number}, Ngày duyệt là "", Mã giảng viên là {self.id_teacher}'

class Teacher():
    id_teacher = ''
    full_name_teacher = ''
    def __init__(self, id_teacher, full_name_teacher) -> None:
        self.id_teacher = id_teacher
        self.full_name_teacher = full_name_teacher
    def __str__(self) -> str:
        return f'Mã giảng viên là {self.id_teacher}, Họ tên giảng viên là {self.full_name_teacher}'

class Unit():
    id_unit = ''
    name_unit = ''
    def __init__(self, id_unit, name_unit) -> None:
        self.id_unit = id_unit
        self.name_unit = name_unit
    def __str__(self) -> str:
        return f'Mã đơn vị là {self.id_unit}, Tên đơn vị là {self.name_unit}'

class ManageStudySection():
    __list_study_section = []
    def __init__(self, list_study_section) -> None:
        self.__list_study_section = list_study_section
    def display(self):
        # Phần này là tạo bảng đây
        table = []
        headers = ['Mã học phần', 'Tên đề cương', 'Số tín chỉ', 'Ngày duyệt', 'Mã giảng viên']

        for study_section in self.__list_study_section:
            if study_section.approval_date != '':
                approval_date = (f'{study_section.approval_date['date']['day']:02d}/{study_section.approval_date['date']['month']:02d}/{study_section.approval_date['date']['year']} {study_section.approval_date['time']['hour']:02d}:{study_section.approval_date['time']['minute']:02d}')
            else:
                approval_date = ''
            table.append([study_section.id_study_section, study_section.name_outline, study_section.credits_number, approval_date, study_section.id_teacher])
        print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

class ManageTeacher():
    __list_teacher = []
    def __init__(self, list_teacher) -> None:
        self.__list_teacher = list_teacher
    def display(self):
        table = []
        headers = ['Mã giảng viên', 'Họ tên giảng viên']
        
        for teacher in self.__list_teacher:
            table.append([teacher.id_teacher, teacher.full_name_teacher])
        print(tabulate(table, headers=headers, tablefmt='fancy_grid'))
        

class ManageUnit():
    __list_unit = []
    def __init__(self, list_unit) -> None:
        self.__list_unit = list_unit
    def display(self):
        table = []
        headers = ['Mã đơn vị', 'Tên đơn vị']
        for unit in self.__list_unit:
            table.append([unit.id_unit, unit.name_unit])
        print(tabulate(table, headers=headers, tablefmt='fancy_grid'))


class Manage():
    __list_study_section = []
    __list_teacher = []
    __list_unit = []
    def __init__(self, list_study_section, list_teacher, list_unit) -> None:
        self.__list_study_section = list_study_section
        self.__list_teacher = list_teacher
        self.__list_unit = list_unit
    def display(self):
        table = []
        headers = ['Mã học phần', 'Tên đề cương', 'Số tín chỉ', 'Đơn vị phụ trách', 'Người biên soạn', 'Ngày duyệt']
        
        for study_section in self.__list_study_section:
            for teacher in self.__list_teacher:
                for unit in self.__list_unit:
                    if study_section.id_teacher == teacher.id_teacher and teacher.id_teacher.startswith(unit.id_unit) and study_section.id_teacher.startswith(unit.id_unit):
                        if study_section.approval_date != '':
                            approval_date = (f'{study_section.approval_date['date']['day']:02d}/{study_section.approval_date['date']['month']:02d}/{study_section.approval_date['date']['year']} {study_section.approval_date['time']['hour']:02d}:{study_section.approval_date['time']['minute']:02d}')
                        else:
                            approval_date = ''
                        table.append([study_section.id_study_section, study_section.name_outline, study_section.credits_number, unit.name_unit, teacher.full_name_teacher, approval_date])
        print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

    def find_study_section(self, key_word):
        result = []
        for study_section in self.__list_study_section:
            if key_word.lower() in study_section.name_outline.lower():
                result.append(study_section.id_study_section)
        size = len(result)
        return ' | '.join(result), size
    
    def statistics_approved_study_section_number(self):
        result = 0
        for study_section in self.__list_study_section:
            if study_section.approval_date != '':
                result += 1
        return result
    
    def statistics_approved_study_section_number_by_unit(self):
        unit_statistics = {}
        for unit in self.__list_unit:
            approved_sections = [
                study_section for study_section in self.__list_study_section if study_section.id_teacher.startswith(unit.id_unit) and study_section.approval_date != ''
            ]
            unit_statistics[unit.name_unit] = len(approved_sections)
        table = []
        headers = ['Đơn vị', 'Số lượng']
        for key, value in unit_statistics.items():
            table.append([key, value])
        print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

    def teacher_charge_most_syllabi(self):
        result = []
        teacher_statistics = {}
        for study_section in self.__list_study_section:
            if study_section.id_teacher in teacher_statistics:
                teacher_statistics[study_section.id_teacher] += 1
            else:
                teacher_statistics[study_section.id_teacher] = 1

        max_charge = max(teacher_statistics.values())
        for teacher in self.__list_teacher:    
            for key, value in teacher_statistics.items():
                if teacher.id_teacher == key and value == max_charge:
                    result.append(teacher.full_name_teacher)
        size = len(result)
        return ' | '.join(result), size

    def export_completed_units(self):
        unit_statistics = {}
        for unit in self.__list_unit:
            approved_sections = [
                study_section for study_section in self.__list_study_section if study_section.id_teacher.startswith(unit.id_unit) and study_section.approval_date != ''
            ]
            unit_statistics[unit.name_unit] = len(approved_sections)
        completed_units = []

        for unit in self.__list_unit:
            completed = True
            if unit_statistics[unit.name_unit] == 0:
                completed = False
                break
            else:
                for study_section in self.__list_study_section:
                    if study_section.id_teacher.startswith(unit.id_unit):
                        approval_date = study_section.approval_date
                        if approval_date == '':
                            completed = False
                            break
            if completed:
                completed_units.append(unit)

        with open('DonViHoanThanh.txt', 'w', encoding='utf-8') as file_out:
            for unit in completed_units:
               file_out.write(str(unit) + '\n')
        print("Đã xuất thông tin các đơn vị hoàn thành vào file DonViHoanThanh.txt")

list_study_section = []
list_teacher = []
list_unit = []

with open('data.txt', 'r', encoding = 'UTF-8') as file_in:
    lines = file_in.readlines()
    current_line = ''
    for line in lines:
        if line == 'HỌC PHẦN\n':
            current_line = 'StudySection'
        elif line == 'GIẢNG VIÊN\n':
            current_line = 'Teacher'
        elif line == 'ĐƠN VỊ\n':
            current_line = 'Unit'
        elif line:
            if current_line == 'StudySection':
                info = line.split(';')
                id_study_section = info[0]
                name_outline = info[1]
                credits_number = int(info[2])
                if info[3] != '':
                    date_time_list = info[3].split()
                    date_list = date_time_list[0].split('/')
                    time_list = date_time_list[1].split(':')
                    date = {
                        'day' : int(date_list[0]),
                        'month' : int(date_list[1]),
                        'year' : int(date_list[2])
                    }
                    time = {
                        'hour' : int(time_list[0]),
                        'minute' : int(time_list[1])
                    }
                    approval_date = {
                        'date' : date,
                        'time' : time
                    }
                else:
                    approval_date = ''
                id_teacher = info[4].replace('\n', '')
                study_section = StudySection(id_study_section, name_outline, credits_number, approval_date, id_teacher)
                list_study_section.append(study_section)

            if current_line == 'Teacher':
                info = line.split(';')
                id_teacher = info[0]
                full_name_teacher = info[1].replace('\n', '')
                teacher = Teacher(id_teacher, full_name_teacher)
                list_teacher.append(teacher)

            if current_line == 'Unit':
                info = line.split(';')
                id_unit = info[0]
                name_unit = info[1].replace('\n', '')
                unit = Unit(id_unit, name_unit)
                list_unit.append(unit)
                
if __name__ == '__main__':
    manage_study_section = ManageStudySection(list_study_section)
    print('HỌC PHẦN')
    manage_study_section.display()
    print()
    manage_teacher = ManageTeacher(list_teacher)
    print('GIẢNG VIÊN')
    manage_teacher.display()
    print()
    manage_unit = ManageUnit(list_unit)
    print('ĐƠN VỊ')
    manage_unit.display()

if __name__ == '__main__':
    print('QUẢN LÝ')       
    manage = Manage(list_study_section, list_teacher, list_unit)
    manage.display()
    print()

    key_word = input('Nhập từ khoá: ')
    study_section_found, size = manage.find_study_section(key_word)
    if size == 1:
        print(f'Mã học phần có từ khoá "{key_word}" xuất hiện trong tên học phần là ', end='')
        print(study_section_found)
    elif size > 1:
        print(f'Danh sách các mã học phần có từ khoá "{key_word}" xuất hiện trong tên học phần là')
        print(study_section_found)
    else:
        print(f'Không tồn tại danh sách các mã học phần có từ khoá "{key_word}" xuất hiện trong tên học phần')
    print()

    print('Số lượng học phần đã được duyệt là', manage.statistics_approved_study_section_number())
    print()

    print('Số lượng học phần mà mỗi đơn vị đã duyệt')
    manage.statistics_approved_study_section_number_by_unit()
    print()

    teacher_charge_most_found, size = manage.teacher_charge_most_syllabi()
    if size == 1:
        print('Giảng viên phụ trách nhiều đề cương nhất là ', end='')
    else:
        print('Các giảng viên phụ trách nhiều đề cương nhất là')
    print(teacher_charge_most_found)
    print()

    manage.export_completed_units()