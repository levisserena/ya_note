"""
Тесты, касающиеся отображения контента.

Какие данные на каких страницах отображаются,
какие при этом используются шаблоны, как работает пагинатор.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    """Класс. Методы - тесты, для проверки отображения контента."""

    @classmethod
    def setUpTestData(cls):
        """
        Метод класса TestContent.

        Создаёт временные объекты классов для тестов.
        """
        cls.notes_add = reverse('notes:add')
        cls.author = User.objects.create(username='Морихэй Уэсиба')

    def test_anonymous_client_has_no_form(self):
        """
        Тест.

        Проверяет, что при запросе анонимного пользователя на страницу
        с формой выходит ошибка 302.
        """
        response = self.client.get(self.notes_add)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_client_has_form(self):
        """
        Тест.

        Проверяет, что при запросе авторизованного пользователя форма
        передаётся в словаре контекста.
        """
        self.client.force_login(self.author)
        response = self.client.get(self.notes_add)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
