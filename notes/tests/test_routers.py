"""
Тесты.

Доступность конкретных конечных точек, проверка
переадресаций, кодов ответа, которые возвращают
страницы, тестирование доступа для авторизованных
или анонимных пользователей.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Класс. Методы - это тесты, для проверки путей."""

    @classmethod
    def setUpTestData(cls):
        """
        Метод класса TestRoutes.

        Создаёт временные объекты классов для тестов.
        """
        cls.author = User.objects.create(username='Кун Цю')
        cls.reader = User.objects.create(username='Вася')
        cls.note = Note.objects.create(
            title='Загаловок',
            text='Произвольный текст, наполняющий поле text.',
            slug='slug_12356789',  # без 4
            author=cls.author,
        )

    def test_pages_availability(self):
        """
        Тест.

        Проверяет страницы на доступность.
        Неавторизированный пользователь имеет право зайти на:
        -> главную страницу;
        -> страницу регистрации;
        -> страницу входа в учётную запись;
        -> страницу выхода из учётной записи.
        """
        urls_namespace = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls_namespace:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        Тест.

        Проверяет переадресацию на авторизацию.
        Неавторизированного пользователя должно перекинуть на страницу
        авторизации, если он попытается войти на страницу:
        -> добавления записи;
        -> отдельной записи;
        -> списка записей;
        -> редактирования записи;
        -> удаления записи;
        -> успешного выполнения операции.
        """
        urls_namespace = (
            ('notes:add', None),
            ('notes:detail', ('any',)),
            ('notes:list', None),
            ('notes:edit', ('any',)),
            ('notes:delete', ('any',)),
            ('notes:success', None),
        )
        login_url = reverse('users:login')
        for name, args in urls_namespace:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_availability_for_note_detail_edit_delete(self):
        """
        Тест.

        Проверяет доступ к редактированию и удалению заметок, а так же к
        странице детального отображения заметки.
        Доступно только автору заметок.
        Другие авторизированных пользователей должны получать ошибку 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls_namespace = (
            'notes:detail',
            'notes:edit',
            'notes:delete',
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls_namespace:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
