import tkinter as tk  # Импорт основного модуля для создания оконных приложений
from tkinter import ttk  # Импорт улучшенных графических компонентов (виджетов)
import subprocess  # Модуль для запуска системных команд (PowerShell)
import webbrowser  # Модуль для открытия ссылок в браузере
import sys  # Модуль для работы с параметрами системы и выхода из программы
import ctypes  # Модуль для вызова функций Windows API (нужен для прав админа)

# Константа Windows, которая говорит системе НЕ открывать черное окно консоли при запуске команд
CREATE_NO_WINDOW = 0x08000000

# --- АВТО-ЗАПРОС ПРАВ АДМИНИСТРАТОРА ---
#Надо включать флаг --uac-admin в Auto-py-to-exe
def is_admin():
    try:
        # Проверяем, запущен ли скрипт от имени администратора
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        # Если возникла ошибка при проверке, считаем, что прав нет
        return False

if not is_admin():
    # Если прав нет, вызываем системное окно UAC для перезапуска приложения с правами админа
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit() # Закрываем текущую копию программы без прав

# Данные о DNS серверах: имя, список IP, описание и ссылка на сайт
DNS_DATA = [
    {"name": "GeoHide DNS", "ips": ["45.155.204.190", "95.182.120.241"], "desc": "DNS для обхода геоблокировок, не проксирует заблокированные РКН ресурсы.", "url": "https://dns.geohide.ru:8443/"},
    {"name": "DNS MAFIA", "ips": ["103.27.157.38", "103.27.157.100"], "desc": "DNS для восстановления доступа к зарубежным ресурсам и сервисам. Свободный интернет без ограничений.", "url": "https://freedom.mafioznik.xyz/"},
    {"name": "ASTRACAT DNS", "ips": ["77.239.113.0", "108.165.164.224"], "desc": "Актуальные конфигурации DNS.", "url": "https://astracat.ru/"},
    {"name": "malw DNS", "ips": ["84.21.189.133", "193.23.209.189"], "desc": "Разблокирует недоступные сайты, блокирует мусор.", "url": "https://info.dns.malw.link/"},
    {"name": "COMSS DNS", "ips": ["83.220.169.155", "212.109.195.93"], "desc": "Доступ к ИИ, блокировка рекламы, счетчиков, вредоносных сайтов и фишинга.", "url": "https://www.comss.ru/"},
    {"name": "Xbox DNS", "ips": ["111.88.96.50", "111.88.96.51"], "desc": "Стабильный доступ к сервисам без границ.", "url": "https://xbox-dns.ru/"},
    {"name": "Cloudflare DNS", "ips": ["1.1.1.1", "1.0.0.1"], "desc": "Самый быстрый DNS.", "url": "https://1.1.1.1"}
]

def get_adapters():
    """Функция получения списка активных сетевых адаптеров через PowerShell"""
    try:
        # Команда получает имена всех адаптеров, статус которых 'Up' (включены)
        cmd = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -ExpandProperty Name"
        # Запуск команды с подавлением окна консоли и чтением вывода в UTF-8
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, encoding="utf-8", creationflags=CREATE_NO_WINDOW)
        # Разбиваем текст по строкам и убираем пустые элементы
        return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    except: return [] # В случае неудачи возвращаем пустой список

def get_current_dns(adapter_name):
    """Функция проверки текущих DNS адресов выбранного адаптера"""
    if not adapter_name: return "Нет сети"
    try:
        # Запрашиваем адреса DNS серверов для протокола IPv4 по имени адаптера
        cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; (Get-DnsClientServerAddress -InterfaceAlias '{adapter_name}' -AddressFamily IPv4).ServerAddresses"
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, encoding="utf-8", creationflags=CREATE_NO_WINDOW)
        dns_list = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        # Если список пуст или содержит только IP роутера — значит DNS получается автоматически
        if not dns_list or "192.168.0.1" in dns_list or "192.168.1.1" in dns_list:
            return "Автоматические (DHCP)"
            
        return "\n".join(dns_list) # Склеиваем IP адреса через перенос строки
    except: return "Ошибка чтения"

def update_ui_status():
    """Обновляет надпись с текущим DNS в интерфейсе"""
    adapter = combo.get() # Берем название адаптера из выпадающего списка
    if adapter:
        # Вызываем проверку DNS и красим текст в неоновый голубой
        status_label.config(text=get_current_dns(adapter), fg=COLOR_CYAN)

def on_adapter_change(event):
    """Событие при выборе другого адаптера в списке"""
    combo.selection_clear()  # ВАЖНО: снимает программное выделение текста, убирая синий фон
    status_label.config(text="Проверка...", fg=COLOR_DIM) # Временно пишем 'Проверка...' серым цветом
    root.update() # Принудительно обновляем окно, чтобы пользователь увидел надпись
    update_ui_status() # Запускаем получение данных

def change_dns(dns_list):
    """Функция установки новых DNS через PowerShell"""
    adapter = combo.get()
    if not adapter: return
    try:
        status_label.config(text="Применение...", fg=COLOR_DIM)
        root.update()
        if dns_list:
            # Формируем список IP для команды PowerShell (в кавычках через запятую)
            formatted = ",".join([f"'{d}'" for d in dns_list])
            cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Set-DnsClientServerAddress -InterfaceAlias '{adapter}' -ServerAddresses ({formatted})"
        else:
            # Если список пуст — сбрасываем настройки на автоматические
            cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Set-DnsClientServerAddress -InterfaceAlias '{adapter}' -ResetServerAddresses"
        
        # Выполняем команду
        subprocess.run(["powershell", "-Command", cmd], check=True, encoding="utf-8", creationflags=CREATE_NO_WINDOW)
        update_ui_status() # Обновляем статус в интерфейсе после завершения
    except:
        status_label.config(text="Ошибка доступа", fg=COLOR_PINK) # Красим в розовый при ошибке

def open_url(url):
    """Открывает переданную ссылку в браузере по умолчанию"""
    webbrowser.open_new(url)

# --- ЦВЕТОВАЯ ПАЛИТРА ---
COLOR_BG_MAIN = "#0a0a0f"      # Основной фон приложения (почти черный)
COLOR_BG_PANEL = "#151720"     # Фон панелей, вкладок и карточек (темно-серый)
COLOR_FG_MAIN = "#e0e6ed"      # Цвет основного текста (светло-серый)
COLOR_DIM = "#6b7280"          # Цвет второстепенного текста (тускло-серый)
COLOR_CYAN = "#00f0ff"         # Акцентный цвет: неоновый голубой
COLOR_PINK = "#ff003c"         # Цвет для критических действий: неоновый розовый
COLOR_BTN = "#1e212f"          # Стандартный фон кнопок
COLOR_BTN_HOVER = "#2a2d3e"    # Фон кнопок при наведении мыши

# --- Интерфейс ---
root = tk.Tk() # Создание главного окна
root.title("Community DNS") # Заголовок окна
root.geometry("450x700") # Размеры окна по умолчанию
root.configure(bg=COLOR_BG_MAIN) # Установка цвета фона окна

# --- ГЛУБОКАЯ НАСТРОЙКА СТИЛЕЙ TTK (ДЛЯ СОВРЕМЕННОГО ВИДА) ---
style = ttk.Style()
style.theme_use('default') # Используем базовую тему для полной кастомизации

# Настройка стиля контейнера вкладок
style.configure("TNotebook", background=COLOR_BG_MAIN, borderwidth=0)
# Настройка самих "корешков" вкладок
style.configure("TNotebook.Tab", 
                background=COLOR_BG_PANEL, # Фон неактивной вкладки
                foreground=COLOR_FG_MAIN, # Цвет текста неактивной вкладки
                padding=[20, 10], # Внутренние отступы (делает вкладку крупнее)
                font=("Segoe UI", 10, "bold"), # Шрифт заголовка
                borderwidth=0, # Убираем рамки
                focuscolor=COLOR_BG_MAIN) # Убираем пунктир при нажатии

# Динамические изменения вкладок (при выборе)
style.map("TNotebook.Tab", 
          background=[("selected", COLOR_BTN_HOVER)], # Фон активной вкладки, выделенная вкладка становится светлее (как кнопка)
          foreground=[("selected", COLOR_CYAN)],      # Цвет текста активной вкладки, текст выделенной вкладки светится циановым
          expand=[("selected", [0, 0, 0, 0])])        # Запрет изменения размера при активации, фиксит дергание вкладок при клике

# Настройка выпадающего списка (Combobox)
style.configure("TCombobox", 
                fieldbackground=COLOR_BG_PANEL, # Фон текстового поля
                background=COLOR_BG_PANEL, # Фон кнопки со стрелкой
                foreground=COLOR_CYAN, # Цвет текста внутри поля, текст выбранного адаптера циановый
                borderwidth=1, # Толщина рамки
                bordercolor=COLOR_DIM, # Цвет рамки, рамка вокруг выпадающего списка
                arrowcolor=COLOR_CYAN) # Цвет стрелочки

# Стили для разных состояний выпадающего списка 
style.map("TCombobox", 
          fieldbackground=[("readonly", COLOR_BG_PANEL)],
          selectbackground=[("readonly", COLOR_BG_PANEL)], # Запрет на смену фона при выделении текста
          selectforeground=[("readonly", COLOR_CYAN)], # Запрет изменения цвета текста при клике
          bordercolor=[("focus", COLOR_CYAN), ("active", COLOR_CYAN)]) # Подсветка рамки при наведении

# Настройка стиля выпадающего меню (которое раскрывается вниз)
root.option_add('*TCombobox*Listbox.background', COLOR_BG_PANEL)
root.option_add('*TCombobox*Listbox.foreground', COLOR_FG_MAIN)
root.option_add('*TCombobox*Listbox.selectBackground', COLOR_BTN_HOVER)
root.option_add('*TCombobox*Listbox.selectForeground', COLOR_CYAN)
root.option_add('*TCombobox*Listbox.font', ("Segoe UI", 11))
root.option_add('*TCombobox*Listbox.borderwidth', 0)

# Создание виджета вкладок
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Размещаем на всё окно с отступами

# Создаем два фрейма (контейнера) для каждой вкладки
tab1 = tk.Frame(notebook, bg=COLOR_BG_MAIN)
tab2 = tk.Frame(notebook, bg=COLOR_BG_MAIN)

# Добавляем их в Notebook с названиями
notebook.add(tab1, text=" УПРАВЛЕНИЕ ")
notebook.add(tab2, text=" СЕРВЕРЫ ")

# === ВКЛАДКА 1: УПРАВЛЕНИЕ (ВЕРХНЯЯ ПАНЕЛЬ С АДАПТЕРОМ) ===
top_inf = tk.Frame(tab1, bg=COLOR_BG_PANEL, bd=0)
top_inf.pack(fill=tk.X, padx=10, pady=15)

# Текст-подсказка "СЕТЕВОЙ АДАПТЕР //"
tk.Label(top_inf, text="СЕТЕВОЙ АДАПТЕР //", bg=COLOR_BG_PANEL, fg=COLOR_DIM, font=("Segoe UI", 8, "bold")).pack(padx=15, pady=(15, 0), anchor="w")
adapters = get_adapters() # Получаем список адаптеров при старте
combo = ttk.Combobox(top_inf, values=adapters, state="readonly", font=("Segoe UI", 11))
combo.pack(fill=tk.X, padx=15, pady=8)
combo.bind("<<ComboboxSelected>>", on_adapter_change) # Привязываем функцию к выбору в списке

# Текст-подсказка "ТЕКУЩИЙ DNS //"
tk.Label(top_inf, text="ТЕКУЩИЙ DNS //", bg=COLOR_BG_PANEL, fg=COLOR_DIM, font=("Segoe UI", 8, "bold")).pack(padx=15, pady=(10, 0), anchor="w")
# Лейбл, который показывает текущие IP адреса (или Ошибку/Загрузку)
status_label = tk.Label(top_inf, text="Загрузка...", font=("Consolas", 14, "bold"), bg=COLOR_BG_PANEL, fg=COLOR_CYAN)
status_label.pack(padx=15, pady=(0, 15), anchor="w")

# Инициализация первого адаптера при запуске
if adapters: 
    combo.current(0) # Выбираем первый адаптер из списка
    combo.selection_clear() # Сразу убираем системное выделение
    update_ui_status() # Показываем его текущий DNS

# Контейнер для кнопок выбора DNS
btn_container = tk.Frame(tab1, bg=COLOR_BG_MAIN)
btn_container.pack(fill=tk.BOTH, expand=True, padx=10)

# Вспомогательные функции для анимации кнопок (подсветка при наведении)
def on_enter(e, color): e.widget['background'] = color
def on_leave(e, color): e.widget['background'] = color

# Цикл по данным DNS_DATA для создания кнопок
for item in DNS_DATA:
    btn = tk.Button(btn_container, text=f"> {item['name'].upper()}", command=lambda d=item["ips"]: change_dns(d),
                    bg=COLOR_BTN, fg=COLOR_FG_MAIN, font=("Segoe UI", 10, "bold"), 
                    activebackground=COLOR_CYAN, activeforeground="#000000",
                    relief="flat", cursor="hand2", pady=8, anchor="w", padx=20)
    btn.pack(fill=tk.X, pady=4)
    # Привязываем эффекты наведения мыши
    btn.bind("<Enter>", lambda e: on_enter(e, COLOR_BTN_HOVER))
    btn.bind("<Leave>", lambda e: on_leave(e, COLOR_BTN))

# Небольшой пустой блок для визуального отступа
tk.Frame(btn_container, bg=COLOR_BG_MAIN, height=15).pack()

# Кнопка сброса настроек (отличается цветом и текстом)
btn_reset = tk.Button(btn_container, text="[ СБРОСИТЬ НА DHCP ]", command=lambda: change_dns(None),
          bg=COLOR_BG_PANEL, fg=COLOR_PINK, font=("Segoe UI", 10, "bold"), 
          activebackground=COLOR_PINK, activeforeground="#000000",
          relief="flat", cursor="hand2", pady=10)
btn_reset.pack(fill=tk.X, pady=(0, 15))
btn_reset.bind("<Enter>", lambda e: on_enter(e, "#30121a")) # Подсветка темно-бордовым
btn_reset.bind("<Leave>", lambda e: on_leave(e, COLOR_BG_PANEL))


# === ВКЛАДКА 2: СЕРВЕРЫ (ОПИСАНИЕ И СКРОЛЛ) ===
# Настройка вертикального скроллбара в темном стиле
style.configure("Vertical.TScrollbar", background=COLOR_BG_PANEL, bordercolor=COLOR_BG_MAIN, arrowcolor=COLOR_CYAN)

# Создаем холст (Canvas), который позволяет прокручивать содержимое
canvas = tk.Canvas(tab2, bg=COLOR_BG_MAIN, highlightthickness=0)
scrollbar = ttk.Scrollbar(tab2, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
scroll_frame = tk.Frame(canvas, bg=COLOR_BG_MAIN) # Фрейм ВНУТРИ холста, где лежат карточки

# Автоматический пересчет области прокрутки при добавлении контента
scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Размещаем фрейм на холсте
canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
desc_labels = [] # Список для хранения текстовых меток (нужен для ресайза)

def on_canvas_configure(event):
    """Обеспечивает растягивание содержимого по ширине при изменении окна"""
    canvas.itemconfig(canvas_window, width=event.width)
    for lbl in desc_labels:
        # Устанавливаем ширину переноса текста за вычетом отступов
        lbl.config(wraplength=event.width - 40)

# Привязываем событие изменения размера холста к функции ресайза
canvas.bind("<Configure>", on_canvas_configure)

canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
scrollbar.pack(side="right", fill="y", pady=10)

# Генерируем карточки для каждого DNS-сервера
for item in DNS_DATA:
    card = tk.Frame(scroll_frame, bg=COLOR_BG_PANEL, bd=0)
    card.pack(fill=tk.X, pady=6, padx=5)
    
    # Название сервера (Заглавными буквами)
    tk.Label(card, text=item["name"].upper(), font=("Segoe UI", 11, "bold"), bg=COLOR_BG_PANEL, fg=COLOR_CYAN).pack(anchor="w", padx=15, pady=(15, 0))
    # IP адреса серверов шрифтом Consolas (как в коде)
    tk.Label(card, text=f"IP: {', '.join(item['ips'])}", font=("Consolas", 9), bg=COLOR_BG_PANEL, fg=COLOR_FG_MAIN).pack(anchor="w", padx=15, pady=(2, 5))
    
    # Описание сервера с автоматическим переносом строк
    desc_lbl = tk.Label(card, text=item["desc"], font=("Segoe UI", 9), bg=COLOR_BG_PANEL, fg=COLOR_DIM, justify="left")
    desc_lbl.pack(anchor="w", padx=15, pady=0)
    desc_labels.append(desc_lbl) # Сохраняем в список для обработки ширины текста
    
    # Интерактивная ссылка на сайт
    link = tk.Label(card, text="[ ОТКРЫТЬ САЙТ ]", font=("Segoe UI", 8, "bold"), bg=COLOR_BG_PANEL, fg=COLOR_CYAN, cursor="hand2")
    link.pack(anchor="w", padx=15, pady=(10, 15))
    link.bind("<Button-1>", lambda e, u=item["url"]: open_url(u)) # Переход по ссылке при клике

def _on_mousewheel(event):
    """Добавляет поддержку прокрутки колесиком мыши"""
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Запуск бесконечного цикла обработки событий окна
root.mainloop()