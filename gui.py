import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from arithmetic_coding import ArithmeticCoder, compress_file, decompress_file, bits_to_bytes


class ArithmeticGUI:
    """Графический интерфейс для арифметического кодирования"""
    
    def __init__(self, root):
        self.root = root
        self.root.title('Арифметическое кодирование')
        self.root.geometry('1000x700')
        
        self.coder = ArithmeticCoder()
        self.current_text = ''
        self.encoded_bits = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Создание интерфейса"""
        main_container = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Верхняя часть - текст и управление
        top_frame = ttk.Frame(main_container)
        main_container.add(top_frame, weight=1)
        
        # Разделяем на левую и правую часть
        content_paned = ttk.PanedWindow(top_frame, orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - текст
        left_frame = ttk.Frame(content_paned)
        content_paned.add(left_frame, weight=2)
        
        # Заголовок текста
        ttk.Label(
            left_frame,
            text='📄 Исходный текст',
            font=('Arial', 12, 'bold')
        ).pack(pady=5)
        
        # Текстовое поле
        text_frame = ttk.Frame(left_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            font=('Courier', 10),
            wrap=tk.WORD,
            height=15
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки для текста
        text_buttons = ttk.Frame(left_frame)
        text_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            text_buttons,
            text='📂 Загрузить из файла',
            command=self.load_text
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            text_buttons,
            text='🗑️ Очистить',
            command=lambda: self.text_widget.delete('1.0', tk.END)
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            text_buttons,
            text='⚙️ Кодировать',
            command=self.encode_text
        ).pack(side=tk.RIGHT, padx=2)
        
        # Правая панель - управление и статистика
        right_frame = ttk.Frame(content_paned)
        content_paned.add(right_frame, weight=1)
        
        # Панель управления файлами
        control_frame = ttk.LabelFrame(right_frame, text='Операции с файлами', padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text='📦 Сжать файл',
            command=self.compress
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            control_frame,
            text='📂 Распаковать файл',
            command=self.decompress
        ).pack(fill=tk.X, pady=2)
        
        # Статистика
        stats_frame = ttk.LabelFrame(right_frame, text='Статистика', padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_text = tk.Text(
            stats_frame,
            font=('Courier', 9),
            wrap=tk.WORD,
            height=10
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Нижняя часть - таблицы
        bottom_frame = ttk.Frame(main_container)
        main_container.add(bottom_frame, weight=1)
        
        # Notebook для вкладок
        notebook = ttk.Notebook(bottom_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка 1: Таблица частот
        freq_frame = ttk.Frame(notebook)
        notebook.add(freq_frame, text='📊 Частоты символов')
        
        # Создаем таблицу частот
        freq_columns = ('char', 'freq', 'probability', 'cumulative')
        self.freq_table = ttk.Treeview(
            freq_frame,
            columns=freq_columns,
            show='headings',
            height=10
        )
        
        self.freq_table.heading('char', text='Символ')
        self.freq_table.heading('freq', text='Частота')
        self.freq_table.heading('probability', text='Вероятность')
        self.freq_table.heading('cumulative', text='Кумулятивная')
        
        self.freq_table.column('char', width=80, anchor=tk.CENTER)
        self.freq_table.column('freq', width=80, anchor=tk.CENTER)
        self.freq_table.column('probability', width=120, anchor=tk.CENTER)
        self.freq_table.column('cumulative', width=120, anchor=tk.CENTER)
        
        freq_scrollbar = ttk.Scrollbar(freq_frame, orient=tk.VERTICAL, command=self.freq_table.yview)
        self.freq_table.configure(yscrollcommand=freq_scrollbar.set)
        
        self.freq_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        freq_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Вкладка 2: Закодированные биты
        bits_frame = ttk.Frame(notebook)
        notebook.add(bits_frame, text='🔢 Закодированные биты')
        
        self.bits_text = scrolledtext.ScrolledText(
            bits_frame,
            font=('Courier', 9),
            wrap=tk.CHAR
        )
        self.bits_text.pack(fill=tk.BOTH, expand=True)
        
    def load_text(self):
        """Загрузка текста из файла"""
        filename = filedialog.askopenfilename(
            title='Выберите текстовый файл',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
            
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert('1.0', text)
            
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось загрузить файл:\n{e}')
    
    def encode_text(self):
        """Кодирование текста"""
        text = self.text_widget.get('1.0', tk.END).strip()
        
        if not text:
            messagebox.showwarning('Предупреждение', 'Введите текст для кодирования!')
            return
        
        try:
            self.current_text = text
            
            # Кодируем
            self.encoded_bits = self.coder.encode(text)
            
            # Обновляем таблицу частот
            self.update_frequency_table()
            
            # Обновляем биты
            self.update_bits_display()
            
            # Обновляем статистику
            self.update_statistics()
            
            messagebox.showinfo('Успех', f'Текст закодирован!\nИспользовано {len(self.encoded_bits)} бит')
            
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось закодировать:\n{e}')
            import traceback
            traceback.print_exc()
    
    def update_frequency_table(self):
        """Обновление таблицы частот"""
        # Очищаем таблицу
        for item in self.freq_table.get_children():
            self.freq_table.delete(item)
        
        if not self.coder.frequencies:
            return
        
        # Заполняем таблицу
        for symbol in sorted(self.coder.frequencies.keys(), key=lambda x: (x == 'EOF', -self.coder.frequencies[x], x)):
            freq = self.coder.frequencies[symbol]
            prob = freq / self.coder.total_freq
            cumulative = self.coder.cumulative_freq[symbol]
            
            # Форматируем символ
            if symbol == 'EOF':
                display_char = 'EOF'
            elif symbol == ' ':
                display_char = '␣ (пробел)'
            elif symbol == '\n':
                display_char = '↵ (новая строка)'
            elif symbol == '\t':
                display_char = '⇥ (таб)'
            else:
                display_char = repr(symbol)[1:-1]
            
            self.freq_table.insert('', tk.END, values=(
                display_char,
                freq,
                f'{prob:.6f}',
                cumulative
            ))
    
    def update_bits_display(self):
        """Обновление отображения битов"""
        self.bits_text.delete('1.0', tk.END)
        
        if not self.encoded_bits:
            return
        
        # Форматируем биты группами по 8
        bits_str = ''.join(str(b) for b in self.encoded_bits)
        
        formatted = ''
        for i in range(0, len(bits_str), 64):
            line = bits_str[i:i+64]
            # Разбиваем на группы по 8
            groups = [line[j:j+8] for j in range(0, len(line), 8)]
            formatted += ' '.join(groups) + '\n'
        
        self.bits_text.insert('1.0', formatted)
    
    def update_statistics(self):
        """Обновление статистики"""
        self.stats_text.delete('1.0', tk.END)
        
        if not self.current_text or not self.encoded_bits:
            return
        
        total_chars = len(self.current_text)
        unique_chars = len(self.coder.frequencies) - 1  # -1 для EOF
        
        # Вычисляем размеры
        original_bits = total_chars * 8
        encoded_bits = len(self.encoded_bits)
        
        # Добавляем размер метаданных (приблизительно)
        import pickle
        freq_size = len(pickle.dumps(self.coder.frequencies))
        cum_freq_size = len(pickle.dumps(self.coder.cumulative_freq))
        metadata_bits = (freq_size + cum_freq_size + 4 + 4 + 1 + 4) * 8
        
        total_bits = encoded_bits + metadata_bits
        
        compression_ratio = (1 - total_bits / (original_bits * 8)) * 100 if original_bits > 0 else 0
        
        # Средняя длина на символ
        avg_bits_per_char = encoded_bits / total_chars if total_chars > 0 else 0
        
        # Вычисляем энтропию
        entropy = 0
        for symbol, freq in self.coder.frequencies.items():
            if symbol != 'EOF':
                prob = freq / self.coder.total_freq
                if prob > 0:
                    import math
                    entropy -= prob * math.log2(prob)
        
        byte_data, padding = bits_to_bytes(self.encoded_bits)
        
        stats = f"""Символов: {total_chars}
Уникальных: {unique_chars}

Исходный размер: {original_bits} бит ({original_bits // 8} байт)
Закодировано: {encoded_bits} бит ({len(byte_data)} байт)
Метаданные: ~{metadata_bits // 8} байт
Итого: ~{(total_bits // 8)} байт

Сжатие: {compression_ratio:.2f}%
Бит на символ: {avg_bits_per_char:.3f}
Энтропия: {entropy:.3f} бит/символ
Эффективность: {(entropy / avg_bits_per_char * 100):.1f}%"""
        
        self.stats_text.insert('1.0', stats)
    
    def compress(self):
        """Сжатие файла"""
        input_file = filedialog.askopenfilename(
            title='Выберите файл для сжатия',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if not input_file:
            return
        
        output_file = filedialog.asksaveasfilename(
            title='Сохранить как',
            defaultextension='.bin',
            filetypes=[('Binary files', '*.bin'), ('All files', '*.*')]
        )
        
        if not output_file:
            return
        
        try:
            compress_file(input_file, output_file)
            messagebox.showinfo('Успех', 'Файл успешно сжат!')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось сжать файл:\n{e}')
    
    def decompress(self):
        """Распаковка файла"""
        input_file = filedialog.askopenfilename(
            title='Выберите файл для распаковки',
            filetypes=[('Binary files', '*.bin'), ('All files', '*.*')]
        )
        
        if not input_file:
            return
        
        output_file = filedialog.asksaveasfilename(
            title='Сохранить как',
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if not output_file:
            return
        
        try:
            decompress_file(input_file, output_file)
            messagebox.showinfo('Успех', 'Файл успешно распакован!')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось распаковать файл:\n{e}')


def main():
    root = tk.Tk()
    app = ArithmeticGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()