import shutil
import tempfile
import re
import sys
import os

from subprocess  import Popen, PIPE

UNSUPPORTED_VERSIONS_FROM_PYINSTALLER = [(3,0), (3,1), (3,2), (3,3), (3,8)]
UNSUPPORTED_VERSIONS_FROM_PY2EXE = [(3,8)]

_PYTHON_VERSION = sys.version_info[0:2]

COMPILLERS = []

RED = ''
CYAN = ''
GREEN = ''
YELLOW = ''
MAGENTA = ''

CONFIG = {'project_file': None} # Поточный чистый конфиг

CONFIGS = {'None': {}} # Здесь хранятся все конфиги которые использовалить. В роли ключа выступает имя скрипта для компиляции

PATH = os.path.dirname(sys.argv[0])
CONFIGS_FILE = 'configs.bin'

# Проверка интернет-соединения. Нужно чтобы не ждать ответ на запрос об версии pip, поскольку нета нет!
def _check_network():
	#-n количество пакетов
	#-l размер пакета
	cmd = ['ping', '-n', '1', '-l', '64', 'www.google.com.ua']
	_ping = Popen(cmd, stdout = PIPE, stderr = PIPE)	 

	stdout, stderr = _ping.communicate()
	if 'Пакетов: отправлено = 1, получено = 1, потеряно = 0' in stdout.decode('cp866'):
		return True
	else: 
		return False

# Получение имени файла
def _get_file_name(path):
	return os.path.basename(path)

# функция проверки корректности полученой директории
def _test_path(path):
	path = path.replace('"', '')
	if os.path.exists(path):
		return path
	elif path in ('--e', 'exit'):
		return None
	else:
		print(YELLOW + '[!] Неверный путь!')

# Проверка корректности полученого имени
def _test_name(name):
	name = name.strip()
	if len(name) > 1:
		return name
	elif name.lower() in ('--e', 'exit'):
		return None
	else:
		print('[!] Введите имя файла')

# Получение ответа от пользователя 
def _get_answer(question):
	print(YELLOW + '[?] %s?' % question)
	while True:
		answer = input('[?] (y/n) ').strip().lower()
		if answer in ('y', 'yes'):
			return True
		elif answer in ('--e', 'exit'):
			return None
		elif answer in ('n', 'no'):
			return False
		else:
			print('[!] Зделайте свой выбор')

# Получение нового имя для перейменования после компиляции
def _get_name(question, function = _test_name):
	print(YELLOW + '[>] %s' % question)
	while True:
		answer = input('[<] ').strip().lower()
		if function:
			result = function(answer)
			if result:
				return result 
		elif answer in ('--e', 'exit'):
			return None

# Получение дополнительной команды
def _get_commands(question):
	print(YELLOW + '[>] %s' % question)
	while True:
		answer = input('[<] ').strip()
		if set(('--e', 'exit')) & set(answer.split(' ')):
			return None
		else:
			return answer

# Получение пути к файлу для комписяции
def _get_path(question, function = _test_path):
	print(YELLOW + '[>] %s' % question)
	while True:
		answer = input('[<] ').strip().lower()
		if function:
			result = function(answer)
			if result:
				return result 
		elif answer in ('--e', 'exit'):
			return None

# Загрузка сохраненных конфигов
def load_configs():
	with open(os.path.join(PATH, CONFIGS_FILE), mode = 'rb') as file:
		if _PYTHON_VERSION <= (3, 4):
			return load(file)
		else:
			return pickle.load(file)

# Перезапись конфига в файл
def save_configs():
	with open(os.path.join(PATH, CONFIGS_FILE), mode = 'wb') as file:
		if _PYTHON_VERSION <= (3, 4):
			return dump(CONFIGS, file)
		else:
			return pickle.dump(CONFIGS, file)

# Выбор компилятора при возможности выбирать с двух
def select_compiller():
	while True:
		result = input('[?] Выберите компилятор 1 - pyinstaller, 2 - py2exe: ').strip().lower()
		if result == '1':
			CONFIG.update({'compiller': 'pyinstaller'})
			break
		elif result == '2':
			CONFIG.update({'compiller': 'py2exe'})
			break
		else:
			print('[!] Сделайте свой выбор')

# Проверка версии pip
def check_pip_update():
	process  = Popen('python -m pip install --upgrade pip', stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = True)
	out, err = process.communicate()
	if out:
		output = out.decode('cp866')
		if 'Requirement already up-to-date: pip' in output:
			pip_version()
		else:
			return True

# Проверка версии pip
def pip_version():
	process  = Popen('python -m pip --version', stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = True)
	out, err = process.communicate()
	if out:
		output = out.decode('cp866')
		# Получение версии в виде строки, отбор первой части с номером версии
		# Разбиваем на список, конвертируем строки в числа и пакуем их в кортеж
		version = tuple(map(int, output.split(' ')[1].split('.') ))
		print('[i] Версия pip: %i.%i.%i' % version)

# Предустановка модуля colorama, pyinstaller и обновление 'pip'
def pre_install(command):
	process = Popen('python -m pip install %s' % command, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
	out,err = process.communicate()

	if err:
		error = err.decode('cp866')
		if 'ERROR: Package \'%s\' requires a different Python' % command in error:
			print(CYAN + '[!] Ошибка: ' + YELLOW + 'Модуль \'%s\' не установливается для данной версии python' % command, file = sys.stderr)
		else:
			print('[!] Ошибка: Возникла ошибка при установки модуля: \'%s\' ' % command, file = sys.stderr)

	if out:
		output = out.decode('cp866')
		if 'Requirement already satisfied: %s'  % command in output:
			print('[i] Модуль: %s уже был установлен!' % command, file = sys.stdout)

		elif 'Successfully installed: %s' % command in output:
			if command == 'py2exe':
				print('[i] Модуль \'py2exe\' успешно установлен!')
			
			elif command == 'colorama':
				print('[i] Модуль \'colorama\' успешно установлен!')
			
			elif command == 'pyinstaller':
				print('[i] Модуль \'pyinstaller\' успешно установлен!')
			
			elif command == '--upgrade pip':
				print('[i] Пакетный менеджер \'pip\' успешно обновлен!')

			return True

# 
def start():
	if len(sys.argv) > 1:
		for arg in sys.argv[1:]:
			# Проверка получена ли иконка
			if re.findall('\\w+\.ico', arg):
				if os.path.exists( os.path.abspath(arg) ):
					print(MAGENTA + '[>] icon: %s' % arg)
					CONFIG.update({'icon': arg})
			# Проверка получен ли файл для компиляции
			if re.findall('\\w+\.py', arg):
				if os.path.exists( os.path.abspath(arg) ):
					print(MAGENTA + '[>] file: %s' % arg)
					CONFIG.update({'project_file': arg})

	# Формирование команды и запись в словарь CONFIG
	if get_params():
		# Начало компиляции
		convert()

# Проверяет скомпилирован ли уже скрипт
def is_compiled(project_file, output_directory):
	if not os.path.exists(output_directory):
		os.makedirs(output_directory)
		return False
	no_extension = os.path.basename(project_file).split('.')[0]
	if no_extension + '.exe' in os.listdir(output_directory):
		return True
	else:
		return False

# 
def convert():
	if CONFIG['compiller'] == 'pyinstaller':
		convert_from_pyinstaller()
	if CONFIG['compiller'] == 'py2exe':
		convert_from_py2exe()

# 
def convert_from_pyinstaller():
	# Получаем комманду для pyinstaller
	command = create_command_from_pyinstaller(**CONFIG)
	# Временная папка для компиляции проэкта
	temporary_directory = tempfile.mkdtemp()
	# Папка в которую будет помещен проэкт после компиляции
	output_directory = CONFIG['output_directory']
	# Имя скрипта для копиляции
	project_file = CONFIG['project_file']

	dist_path  = os.path.join(temporary_directory, 'application')
	build_path = os.path.join(temporary_directory, 'build')
	extra_args = ' --distpath %s --workpath %s --specpath %s' % (dist_path, build_path, temporary_directory)

	print(YELLOW + '[>] command: %s' % command)
	# Если файл уже существует
	if is_compiled(project_file, output_directory):
		print(MAGENTA + '[!] Файл уже существует!')
		open_directory(output_directory)

	else:
		print(YELLOW + '[i] Начало компиляции...')
		process = Popen(command + extra_args, stderr = PIPE, stdout = PIPE)
		err,out = process.communicate()

		if out:
			output = out.decode('cp866')
			if 'completed successfully' in output:
				print(MAGENTA + '[i] Программа успешно скомпилирована!')
			else:
				print(YELLOW + '[!] Произошла ошибка!')
				print(YELLOW + output)
		if err:
			print(err.decode('cp866'))

		print(YELLOW + '[i] Перемещение проекта в: %s ' % output_directory )
		try:
			move_project(dist_path, output_directory)
		except:
			print(YELLOW + '[!] Ошибка перемещения файла с %s в %s' % (dist_path, output_directory) )
		else:
			print(MAGENTA + '[i] Проект успешно перемещён!')
			remove_temp_dir(temporary_directory)
			open_directory(output_directory)
			# Добавление нового конфига 
			CONFIGS.update({_get_file_name(project_file): CONFIG})
			# Сохраняем конфиги
			save_configs()
			return True

#
def convert_from_py2exe():
	# Получаем комманду для py2exe
	command = create_command_from_py2exe(CONFIG)
	# Папка в которую будет помещен проэкт после компиляции
	output_directory = CONFIG['output_directory']
	# Имя скрипта для копиляции
	project_file = CONFIG['project_file']

	print(YELLOW + '[>] command: %s' % command)
	# Если файл уже существует
	if is_compiled(project_file, output_directory):
		print(MAGENTA + '[!] Файл уже существует!')
		open_directory(output_directory)

	else:
		print(YELLOW + '[i] Начало компиляции...')
		process = Popen(command, stderr = PIPE, stdout = PIPE)
		out,err = process.communicate()
		if out:
			output = out.decode('cp866')
			if 'Building' in output:
				print(MAGENTA + '[i] Программа успешно скомпилирована!')
				open_directory(output_directory)
				# Добавление нового конфига 
				CONFIGS.update({_get_file_name(project_file): CONFIG})
				# Сохраняем конфиги
				save_configs()
				return True
			else:
				print(YELLOW + '[!] Произошла ошибка!')
				print(YELLOW + output)
		if err:
			print(err.decode('cp866'))

# Перемещение программы с временной папки в указаную конечную
def move_project(src, dst):
	# Если конечная папка не существует, создает ее
	if not os.path.exists(dst):
		os.makedirs(dst)
	# Перемещает все файлы с временной папки в концевую
	for file_or_folder in os.listdir(src):
		_dst = os.path.join(dst, file_or_folder)
		# Если файл или папка существует, удаляет для дальнейшей перезаписи
		if os.path.exists(_dst):
			if os.path.isfile(_dst):
				os.remove(_dst)
			else:
				shutil.rmtree(_dst)
		# Перемещает файл
		shutil.move(os.path.join(src, file_or_folder), dst)

# Удаляет временную директорию в которой находятся все файлы которые были созданы при компиляции проекта
def remove_temp_dir(temporary_directory):
    shutil.rmtree(temporary_directory)
    print(MAGENTA + '[>] Временная папка успешно удалена!')

#Открывает папку с проэктом
def open_directory(output_directory):
	print(YELLOW + '[>] Открытие папки...')
	os.system('start %s' % output_directory)

# Возвращает склееную комманду для PyInstaller
def create_command_from_pyinstaller(compiller, one_file, console, upx, icon, name, added_commands, project_file, output_directory):
	command = 'python -m PyInstaller -y '
	command += '' if one_file == False else ' -F'
	command += '' if console == True else ' -w'
	command += '' if upx == True else ' --noupx'
	command += ' -i"%s"' % icon if icon else ''
	command += ' -n"%s"' % name if name else ''
	command += ' %s' % added_commands if added_commands else ''  
	command += ' "%s"' % project_file if project_file else ''
	return command

# Возвращает склееную комманду для py2exe
def create_command_from_py2exe(config):
	#python -m  py2exe.build_exe  D:\data\Libinstaller\libinstaller.py --dest D:\data\Libinstaller --summary  -c --bundle-files 0
	optimize = config.get('optimize', False)
	include_dll = config.get('include_dll', False)

	command = 'python -m'
	command += ' py2exe.build_exe %s' % config['project_file'] if config['project_file'] else ''
	command += ' --dest %s' % config['output_directory'] if config['output_directory'] else ''
	if config['one_file']:
		if include_dll:
			command += ' --bundle-files 1'
		else:
			command += ' --bundle-files 0'
	else:
		if include_dll:
			command += ' --bundle-files 2'
		else:
			command += ' --bundle-files 3'
	command += ' --optimize' if optimize else ''
	return command

# Формирование комманды
def get_params():
	global CONFIG

	while True:
		if not CONFIG['project_file']:
			project_file = _get_path('Введите путь к файлу для компиляции в .exe')
			if project_file:
				CONFIG['project_file'] = project_file
			else:
				break
		else:
			project_file = CONFIG['project_file'] # Если путь к скрипту был получен аргументоом при запуске

		config = CONFIGS.get(_get_file_name(project_file), None) # Поик конфигурации по имени проэкта
		if config:
			if config['compiller'] == 'pyinstaller':
				question =  '[?] Использовать прошлые настройки: %s' % create_command_from_pyinstaller(**config)
			elif config['compiller'] == 'py2exe':
				question =  '[?] Использовать прошлые настройки: %s' % create_command_from_py2exe(config)
			result = _get_answer(YELLOW + question)
			if result:
				CONFIG = config # Приминение старой конфигурации к текущему проэкту
				return True

		if len(COMPILLERS) == 2:
			select_compiller() # Выбор компилятора
		elif len(COMPILLERS) == 1:
			CONFIG.update({'compiller': COMPILLERS[0]}) # Если для компиляции доступен только один компилятор, автоматически выбирает его
		# настройка конфигурации в соотвецтвии с выбраным компилятором
		reset_config()

		one_file = _get_answer('Скомпилоровать одним файлом')
		if one_file is None:
			break
		if CONFIG['compiller'] == 'pyinstaller':
			console = _get_answer('Скрыть консоль')
			if console is None:
				break
			upx = _get_answer('Добавить "UPX" модуль')
			if upx is None:
				break
			if not CONFIG['icon']:
				add_icon = _get_answer('Добавить иконку')
				if add_icon:
					icon = _get_path('Введите путь к иконке')
				else:
					icon = None
			edit_name = _get_answer('Изменить имя cкомпилорованого файла')
			if edit_name:
				name = _get_name('Введите новое имя для cкомпилорованого файла')
			else:
				name = None

			add_commands = _get_answer('Добавить дополнительные комманды')
			if add_commands:
				added_commands = _get_commands('Введите дополнительные команды')
			else:
				added_commands = None
			# Обновление параметров
			CONFIG.update({
				'console': console,
				'upx': upx,
				'icon': icon,
				'name': name,
				'added_commands': added_commands
				})
		else:
			optimize = _get_answer('Сжать код')
			if optimize is None:
				break
			include_dll = _get_answer('Подключить дополнительные библиотеки')
			if include_dll is None:
				break
			# Обновление параметров
			CONFIG.update({
				'optimize': optimize,
				'include_dll': include_dll,
				})
		CONFIG.update({'one_file': one_file})

		CONFIG.update({	
			'project_file': project_file,
			'output_directory': os.path.join(os.path.dirname(sys.argv[0]), os.path.basename(project_file).split('.')[0].replace(' ', '_') )
			})
		return True

# Сброс параметров для компиляции
def reset_config():
	global CONFIG

	if CONFIG.get('compiller', None):
		if CONFIG['compiller'] == 'pyinstaller':
			CONFIG.update({
				'one_file':  True,
				'console':  False,
				'upx':  False,
				'icon':  None,
				'name':  None,
				'added_commands': None,
				'project_file': None,
				'output_directory': None
				})

		if CONFIG['compiller'] == 'py2exe':
			CONFIG.update({
				'one_file':  True,
				'optimize':  True,
				'include_dll':  True,
				'project_file': None,
				'output_directory': None
				})
		print(MAGENTA + '[>] Настройки сброшены!')
	else:
		print(YELLOW + '[>] Конфигурация не найдена!')	

# Удаляет папку с проектом и компилирует его заного
def again():
	output_directory = CONFIG.get('output_directory', None)
	if output_directory:
		try:
			shutil.rmtree(output_directory)
		except:
			print(YELLOW + '[!] Ошибка при удалении папки: %s' % output_directory)
		else:
			print(MAGENTA + '[i] Проект успешно удален!')
		finally:
			convert()
	else:
		print(YELLOW + '[!] Для начала скомпилируйте проэкт')

# Справка
def help():
	# табы будут удаляться при выводе в консоль
	text = '''Список доступных комманд:
	  --s / start - запуск компиляции
	  --h / help  - подсказка
	  --c / compiler - смена компилятора (при возможности
	  --r / reset - Обнуляет заданые настройки
	  --a / again - Удаляет проект и компилирует его заново
	  --e / exit  - выход с программы

	Для компиляции доступны pyinstaller и py2exe. Рекомендуется использовать pyinstaller, поскольку он обладает такими 
	преимуществами как:
	- меньший размер исходного файла,
	- возможность установить иконку для приложения
	- большей стабильностью при сборке проэкта

	Py2exe имеет три параметра для компиляции, но возможны проблемы с \'--bundle-files\'. Для решения данной проблемы нужно подключить/отключить
	дополнительные библиотеки или скомпилировать в файл/папку.

	Py2exe не поддерживает изменение иконки!
	Но есть возможность открыть \'исполняймый\' файл и подчистить ненужные библиотеки и модули

	Для запуска компиляции проекта в исполняймый файл можно перетащить скрипт и иконку на ярлык easycompiller, 
	после чего он запустится, запросит дополнительные данные и скомпилирует проект.
	Также можно скомпидировать проект запустив easycompiller и используя комманду --s / start и указать дополнительные параметры для компиляции. 

	После успешной компиляции, конфигурация будет сохранена, и в дальнейшем при попытке скомпилировать файл с таким же именем
	скрипт придложит применить старую конфигурацию.

	ВНИМАНИЕ! В пункте \'Добавить дополнительные комманды\' используются ниже перечисленые комманды. 
	Введение неверной комманды может призвести к ошибке компиляции!

	Комманды для PyInstaller
	[-h] [-v] [-D] [-F] 
	[--add-data <SRC;DEST or SRC:DEST>]
	[--add-binary <SRC;DEST or SRC:DEST>] [-p DIR]
	[--hidden-import MODULENAME]
	[--additional-hooks-dir HOOKSPATH]
	[--runtime-hook RUNTIME_HOOKS] [--exclude-module EXCLUDES]
	[--key KEY] [-d [{all,imports,bootloader,noarchive}]] [-s]
	[-c] [-w]
	[--version-file FILE] [-m <FILE or XML>] [-r RESOURCE]
	[--uac-admin] [--uac-uiaccess] [--win-private-assemblies]
	[--win-no-prefer-redirects]
	[--osx-bundle-identifier BUNDLE_IDENTIFIER]
	[--runtime-tmpdir PATH] [--bootloader-ignore-signals]
	[--upx-dir UPX_DIR] [-a] [--clean] [--log-level LEVEL]

	Комманды для Py2exe
	[-i modname, --include modname]     module to include
	[-x modname, --exclude modname]     module to exclude
	[-p package_name, --package package_name]     module to exclude
	[-s, --summary]	   print a single line listing how many modules were found and how many modules are missing
	[-r, --report]	   print a detailed report listing all found modules, the missing modules, and which module imported them.
	[-f modname, --from modname]	 print where the module <modname> is imported.
	[-v]	verbose output
	[-l LIBNAME, --library LIBNAME]		relative pathname of the python archive
	'''

	for line in text.replace('\t', '').split('\n'):
		print(MAGENTA + '[i] %s' % line)

# 
if __name__ == '__main__':
	print('[i] Вас привецтвует easycompiller 1.0.0')

	if _PYTHON_VERSION < (3, 0):
		print(YELLOW + '[!] Установите \'Python\' версии 3.0 и выше.')
	else:
		print(GREEN + '[i] Ваша версия Python %i.%i.%i' % sys.version_info[0:3])

	# Если доступно интернет-соединение
	if _check_network():
		# Запуск проверки версии pip #19.3.1 последняя
		if check_pip_update():
			pre_install('--upgrade pip')
	else:
		print(RED + '[!] Отсуцтвует интернет-соединение')


	if _PYTHON_VERSION <= (3, 4):
		from pickle import dump, load
	else:
		import pickle

	try:
		from colorama import Fore, init
		init(autoreset = True)
		RED = Fore.RED
		CYAN = Fore.CYAN
		GREEN = Fore.GREEN
		YELLOW = Fore.YELLOW
		MAGENTA = Fore.MAGENTA
	except ImportError:
		print('[!] Модуль \'colorama\' не установлен!')
		if _PYTHON_VERSION != (3, 4):
			if _check_network():
				if pre_install('colorama'):
					restart() #! Костыль. Перезапуск скрипта для импорта модуля 'colorama'
			else:
				print(RED + '[!] Отсуцтвует интернет-соединение')
		else:
			print(CYAN + '[!] Ошибка: ' + YELLOW + 'Модуль \'colorama\' не установливается для данной версии python')


	if _PYTHON_VERSION not in UNSUPPORTED_VERSIONS_FROM_PYINSTALLER:
		try:
			import PyInstaller
			COMPILLERS.append('pyinstaller')
		except ImportError:
			print('[!] Модуль \'PyInstaller\' не установлен!')
			if _check_network():
				if pre_install('PyInstaller'):
					COMPILLERS.append('pyinstaller')
			else:
				print(RED + '[!] Отсуцтвует интернет-соединение')

	else:
		print(YELLOW + '[!] Данная версия Python %i.%i не поддерживается PyInstaller' % _PYTHON_VERSION)
		# Изменяет компилятор на py2exe если pyinstaller не поддерживается
		CONFIG.update({'compiller': 'py2exe'})

	if _PYTHON_VERSION not in UNSUPPORTED_VERSIONS_FROM_PY2EXE:
		try:
			COMPILLERS.append('py2exe')
			import py2exe
		except ImportError:
			print('[!] Модуль \'py2exe\' не установлен!')
			if _check_network():
				if pre_install('py2exe'):
					COMPILLERS.append('py2exe')
			else:
				print(RED + '[!] Отсуцтвует интернет-соединение')
		except:
			pass
	else:
		print(YELLOW + '[!] Данная версия Python %i.%i не поддерживается py2exe' % _PYTHON_VERSION)

	# Загрузка конфигураций
	if os.path.exists(os.path.join(PATH, CONFIGS_FILE)):
		CONFIGS = load_configs()
	else:
		save_configs() # Запись чистой конфигурации в файл

	if len(COMPILLERS) == 0:
		print(RED + '[!] Компиляция невозможна')

	# Проверяет получены ли нужные файлы для компиляции
	if len(sys.argv) > 1 and sys.argv[1] != 'py2exe':
		start()

	while True:
		user_input = input('[>] Введите комманду: ').lower().strip()

		if user_input in ('--s', 'start'):
			start()
		elif user_input in ('--c', 'compiller'):
			select_compiller()
		elif user_input in ('--r', 'reset'):
			reset_config()
		elif user_input in ('--a', 'again'):
			again()
		elif user_input in ('--h', 'help'):
			help()
		elif user_input in ('--e', 'exit'):
			exit()
		else:
			print(RED + '[!] Не удалось распознать комманду: \'%s\'' % user_input)
