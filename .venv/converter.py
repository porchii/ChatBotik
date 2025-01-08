from fnmatch import fnmatch
import re

class Converter:
    def normalize_time(self, time_string):
        def add_leading_zero(time_part):
            hours, minutes = map(int, time_part.split(':'))
            return f"{hours:02}:{minutes:02}"

        range_pattern = re.compile(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})')
        single_time_pattern = re.compile(r'с\s*(\d{1,2}:\d{2})', re.IGNORECASE)

        if range_match := range_pattern.match(time_string):
            start, end = range_match.groups()
            return f"{add_leading_zero(start)}-{add_leading_zero(end)}"

        if single_time_match := single_time_pattern.match(time_string):
            time = single_time_match.group(1)
            return add_leading_zero(time)

        return time_string

    def convert(self, matrix):
        print(matrix)
        res = []
        indxes = []

        # Регулярное выражение для формата классов "6.1", "11.2", и т.д.
        class_pattern = re.compile(r'^\d{1,2}\.\d{1}$')

        st = set()
        # Проверка на временные форматы для всех ячеек
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                if ':' in str(matrix[i][j]):  # Если ячейка содержит время
                    matrix[i][j] = self.normalize_time(str(matrix[i][j]))

                # Определение строк с номерами классов
                if class_pattern.match(str(matrix[i][j])):
                    indxes.append((i, j, matrix[i][j]))
                    st.add((i, j))

        print(indxes)
        # Обработка классов и уроков на основе индексов
        for tup in indxes:
            i, j, class_name = tup
            for row in range(i + 1, len(matrix)):
                cell_content = str(matrix[row][j])
                if cell_content.lower() != 'nan' and ':' not in cell_content:
                    cur = list(map(str, cell_content.split()))
                    if row > 0:
                        time = str(matrix[row - 1][j])
                        if class_name == '1.1':
                            print(time)
                        if ':' in time:
                            time = list(map(str, time.split('-')))
                            res.append((" ".join(cur), time[0], time[1], class_name))
                # Прерываем обработку, если ячейка содержит точку (но не номер класса)
                if (row, j) in st:
                    break

        return res
