def calculate_sum(arr):
    s = 0
    for i in range(len(arr)):  # Исправленная версия
        s += arr[i]
    return s
