# easycompiller

Удобный инструмент для компиляции скрипта python в "исполняемый" файл.


Поскольку язык python является скриптовым языком программирования, вопрос о компиляции скрипта в "исполнимый" (.exe) файл возникает лишь тогда, когда нужно чтобы вашим скриптом могли воспользоваться люди без предустановленного интерпретатора. Но это возникает очень редко (по крайней мере,  у меня), поэтому и было принято решение создать небольшой инструмент для облегчения создания исполняемого файла.
Так почему же "исполнимый"? Все дело в том, что компиляции в бинарный хайл (как в C++, C#) не происходит. Библиотеки Pyinstaller и py2exe всего лишь создают zip архив,  в который добаляет сам интерпретатор, ваш скрипт и дополнительные библиотеки. Поэтому скомпилированный файл занимает много места на диске (5 МБ и больше), даже если в скрипте всего лишь одна строчка. Также с этого выплывает тот факт, что запуск программы не будет моментальный(так как требуется время на распаковку архива)
Основными преимуществами использования данного инструмента являются:
-Поддержка разных версий python
-Автоматическое обновление pip, установка pyinstaller, py2exe, colorama, приятный интерфейс, справка
-Возможность передать путь к скрипту и иконке аргументами при запуске
-Не нужно помнить команды pyinstaller и py2exe, вам просто нужно ответить на заданные вопросы.
-Возможность сразу же пересобрать проект после внесения мелких правок командой again/--a.
-Автоматическое сохранение конфигураций по имени проекта, если вы скомпилировали скрипт, и через некоторое время его доработали и нужно снова компилировать, easycompiller найдет в файле configs.bin конфигурацию и предложит скомпилировать проект со старыми настройками.






