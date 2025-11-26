import sys
import pickle
from pathlib import Path


class ArithmeticCoder:
    """Арифметическое кодирование с целочисленной арифметикой"""
    
    def __init__(self):
        self.CODE_VALUE_BITS = 32
        self.MAX_CODE = (1 << self.CODE_VALUE_BITS) - 1
        self.HALF = 1 << (self.CODE_VALUE_BITS - 1)
        self.QUARTER = 1 << (self.CODE_VALUE_BITS - 2)
        
        self.frequencies = {}
        self.cumulative_freq = {}
        self.total_freq = 0
        
    def build_frequency_table(self, data):
        """Построение таблицы частот"""
        self.frequencies = {}
        
        for symbol in data:
            self.frequencies[symbol] = self.frequencies.get(symbol, 0) + 1
        
        self.frequencies['EOF'] = 1
        
        self.cumulative_freq = {}
        cumulative = 0

        for symbol in sorted(self.frequencies.keys(), key=lambda x: (x != 'EOF', x)):
            self.cumulative_freq[symbol] = cumulative
            cumulative += self.frequencies[symbol]
        
        self.total_freq = cumulative
        
        return self.frequencies
    
    def encode(self, data):
        """Кодирование данных"""
        if not data:
            return []
        
        self.build_frequency_table(data)

        low = 0
        high = self.MAX_CODE
        pending_bits = 0
        output_bits = []
        
        def output_bit(bit):
            """Вывод бита и pending битов"""
            nonlocal pending_bits
            output_bits.append(bit)
            for _ in range(pending_bits):
                output_bits.append(1 - bit)
            pending_bits = 0
        
        for symbol in data:
            range_size = high - low + 1
            high = low + (range_size * (self.cumulative_freq[symbol] + self.frequencies[symbol])) // self.total_freq - 1
            low = low + (range_size * self.cumulative_freq[symbol]) // self.total_freq
            
            while True:
                if high < self.HALF:
                    output_bit(0)
                    low = low * 2
                    high = high * 2 + 1
                elif low >= self.HALF:
                    output_bit(1)
                    low = (low - self.HALF) * 2
                    high = (high - self.HALF) * 2 + 1
                elif low >= self.QUARTER and high < 3 * self.QUARTER:
                    pending_bits += 1
                    low = (low - self.QUARTER) * 2
                    high = (high - self.QUARTER) * 2 + 1
                else:
                    break

        symbol = 'EOF'
        range_size = high - low + 1
        high = low + (range_size * (self.cumulative_freq[symbol] + self.frequencies[symbol])) // self.total_freq - 1
        low = low + (range_size * self.cumulative_freq[symbol]) // self.total_freq
        
        while True:
            if high < self.HALF:
                output_bit(0)
                low = low * 2
                high = high * 2 + 1
            elif low >= self.HALF:
                output_bit(1)
                low = (low - self.HALF) * 2
                high = (high - self.HALF) * 2 + 1
            elif low >= self.QUARTER and high < 3 * self.QUARTER:
                pending_bits += 1
                low = (low - self.QUARTER) * 2
                high = (high - self.QUARTER) * 2 + 1
            else:
                break
        
        pending_bits += 1
        if low < self.QUARTER:
            output_bit(0)
        else:
            output_bit(1)
        
        return output_bits
    
    def decode(self, bits, length):
        """Декодирование данных"""
        if not bits or length == 0:
            return []
        
        low = 0
        high = self.MAX_CODE
        value = 0
        
        bit_index = 0
        for _ in range(min(self.CODE_VALUE_BITS, len(bits))):
            value = (value << 1) | bits[bit_index]
            bit_index += 1
        
        decoded = []
        
        while len(decoded) < length:
            range_size = high - low + 1
            scaled_value = ((value - low + 1) * self.total_freq - 1) // range_size
            
            symbol = None
            for s in sorted(self.cumulative_freq.keys(), key=lambda x: (x != 'EOF', x)):
                if self.cumulative_freq[s] <= scaled_value < self.cumulative_freq[s] + self.frequencies[s]:
                    symbol = s
                    break
            
            if symbol is None or symbol == 'EOF':
                break
            
            decoded.append(symbol)
            
            high = low + (range_size * (self.cumulative_freq[symbol] + self.frequencies[symbol])) // self.total_freq - 1
            low = low + (range_size * self.cumulative_freq[symbol]) // self.total_freq
            
            while True:
                if high < self.HALF:
                    low = low * 2
                    high = high * 2 + 1
                    value = value * 2
                    if bit_index < len(bits):
                        value += bits[bit_index]
                        bit_index += 1
                elif low >= self.HALF:
                    low = (low - self.HALF) * 2
                    high = (high - self.HALF) * 2 + 1
                    value = (value - self.HALF) * 2
                    if bit_index < len(bits):
                        value += bits[bit_index]
                        bit_index += 1
                elif low >= self.QUARTER and high < 3 * self.QUARTER:
                    low = (low - self.QUARTER) * 2
                    high = (high - self.QUARTER) * 2 + 1
                    value = (value - self.QUARTER) * 2
                    if bit_index < len(bits):
                        value += bits[bit_index]
                        bit_index += 1
                else:
                    break
                
                value &= self.MAX_CODE
        
        return decoded


def bits_to_bytes(bits):
    """Преобразование списка битов в байты"""
    padding = (8 - len(bits) % 8) % 8
    bits = bits + [0] * padding
    
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        bytes_list.append(byte)
    
    return bytes(bytes_list), padding


def bytes_to_bits(data, total_bits):
    """Преобразование байтов в список битов"""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    
    return bits[:total_bits]


def compress_file(input_path, output_path):
    """Сжатие файла"""
    print(f"Чтение {input_path}...", flush=True)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    if not text:
        print("Файл пустой!")
        return
    
    print(f"Размер: {len(text)} символов", flush=True)
    print("Построение таблицы частот...", flush=True)
    
    coder = ArithmeticCoder()
    
    print("Кодирование...", flush=True)
    
    bits = coder.encode(text)
    
    print(f"Закодировано в {len(bits)} бит", flush=True)
    print("Сохранение...", flush=True)
    
    byte_data, padding = bits_to_bytes(bits)
    
    with open(output_path, 'wb') as f:
        f.write(len(text).to_bytes(4, 'big'))
        
        f.write(len(bits).to_bytes(4, 'big'))
        
        f.write(padding.to_bytes(1, 'big'))
        
        freq_data = pickle.dumps(coder.frequencies)
        f.write(len(freq_data).to_bytes(4, 'big'))
        f.write(freq_data)
        
        cum_freq_data = pickle.dumps(coder.cumulative_freq)
        f.write(len(cum_freq_data).to_bytes(4, 'big'))
        f.write(cum_freq_data)
        
        f.write(coder.total_freq.to_bytes(4, 'big'))
        
        f.write(byte_data)
    
    original = Path(input_path).stat().st_size
    compressed = Path(output_path).stat().st_size
    ratio = (1 - compressed / original) * 100 if original > 0 else 0
    
    print(f"\n✓ Готово!")
    print(f"  Исходный: {original} байт")
    print(f"  Сжатый: {compressed} байт")
    print(f"  Сжатие: {ratio:.2f}%")
    print(f"  Бит на символ: {len(bits) / len(text):.3f}")


def decompress_file(input_path, output_path):
    """Распаковка файла"""
    print(f"Чтение {input_path}...", flush=True)
    
    with open(input_path, 'rb') as f:
        length = int.from_bytes(f.read(4), 'big')
      
        bits_count = int.from_bytes(f.read(4), 'big')
        
        padding = int.from_bytes(f.read(1), 'big')
        
        freq_len = int.from_bytes(f.read(4), 'big')
        freq_data = f.read(freq_len)
        frequencies = pickle.loads(freq_data)
        
        cum_freq_len = int.from_bytes(f.read(4), 'big')
        cum_freq_data = f.read(cum_freq_len)
        cumulative_freq = pickle.loads(cum_freq_data)
        
        total_freq = int.from_bytes(f.read(4), 'big')
        
        encoded_data = f.read()
    
    print(f"Распаковка {length} символов...", flush=True)
    print("Восстановление битов...", flush=True)
    
    bits = bytes_to_bits(encoded_data, bits_count)
    
    print("Декодирование...", flush=True)
    
    coder = ArithmeticCoder()
    coder.frequencies = frequencies
    coder.cumulative_freq = cumulative_freq
    coder.total_freq = total_freq
    
    result = coder.decode(bits, length)
    
    print(f"Запись в {output_path}...", flush=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(result))
    
    print(f"\n✓ Готово!")


if __name__ == "__main__":
    print("=== Арифметическое кодирование ===\n", flush=True)
    
    if len(sys.argv) < 4:
        print("Использование:")
        print("  python arithmetic_coding.py compress input.txt output.bin")
        print("  python arithmetic_coding.py decompress input.bin output.txt")
        sys.exit(1)
    
    mode, input_file, output_file = sys.argv[1:4]
    
    try:
        if mode == "compress":
            compress_file(input_file, output_file)
        elif mode == "decompress":
            decompress_file(input_file, output_file)
        else:
            print("Режим: compress или decompress")
    except FileNotFoundError:
        print(f"Файл '{input_file}' не найден!")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()