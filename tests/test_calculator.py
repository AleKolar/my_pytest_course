import sys
import os
import pytest

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.calculator import add, divide

@pytest.mark.smoke
def test_add():
    assert add(2, 3) == 5

@pytest.mark.regression
def test_divide():
    assert divide(10, 2) == 5

@pytest.mark.regression
def test_divide_by_zero_raises_value_error_with_message():
    with pytest.raises(ValueError) as excinfo:
        divide(10, 0)
    # Проверяем, что текст ошибки содержит нужную фразу
    assert "Нельзя делить на ноль" in str(excinfo.value)

@pytest.mark.slow
def test_very_slow_calculation():
    """Гипотетический тест, который работает очень долго."""
    # для примера просто сделаем его успешным
    assert True

@pytest.mark.skip(reason="Эта функциональность будет реализована в версии 2.0")
def test_subtraction():
    """Тест для будущей функции вычитания."""
    # assert subtract(10, 5) == 5
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Требуется Python 3.10 или выше")
def test_new_python_feature():
    """Тест, использующий синтаксис, доступный только в новых версиях Python."""
    # Пример использования match-case, который появился в 3.10
    result = 0
    match 1:
        case 1:
            result = 1
    assert result == 1

@pytest.mark.xfail(reason="Известный баг с точностью float, будет исправлен в #TICKET-123")
def test_add_floats_bug():
    # Этот тест будет падать из-за особенностей представления float в Python
    assert add(0.1, 0.2) == 0.3

# Запуск тестов по маркерам с помощью флага -m
# Синтаксис :
# pytest -m <имя_маркера>
# pytest -m smoke
# pytest -m regression
# pytest -m slow
# pytest -m skip
# pytest -m skipif
# pytest -m xfail
# pytest -m "not slow"
# pytest -m "smoke and regression"
# pytest -m "smoke or regression"