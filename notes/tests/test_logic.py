"""
Тестирование бизнес-логики приложения.

Как обрабатываются те или иные формы,
разрешено ли создание объектов с неуникальными
полями, как работает специфичная логика конкретного
приложения.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNotesCreation(TestCase):
    """Класс. Методы - это тесты, для проверки создания записи."""

    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст'
    NOTE_SLUG = 'slug_123'
    DONE_URL = '/done/'

    @classmethod
    def setUpTestData(cls):
        """
        Метод класса TestNotesCreation.

        Создаёт временные объекты классов для тестов.
        """
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Иван Фёдорович Крузенштерн')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_anonymous_user_cant_create_note(self):
        """
        Тест.

        Проверяет, что анонимный пользователь не может создавать записи.
        """
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """
        Тест.

        Проверяет, что зарегистрированный пользователь может создавать записи.
        """
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.DONE_URL)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)


class TestNoteEditDelete(TestCase):
    """
    Класс.

    Методы - это тесты, для проверки редактирования и удаления записи.
    """

    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст'
    NOTE_SLUG = 'slug_123'
    NOTE_TEXT_NEW = 'Обновлённый текст'
    DONE_URL = '/done/'

    @classmethod
    def setUpTestData(cls):
        """
        Метод класса TestNoteEditDelete.

        Создаёт временные объекты классов для тестов.
        """
        cls.author = User.objects.create(username='Автор записи')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author,
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT_NEW,
            'slug': cls.NOTE_SLUG,
        }

    def test_author_can_delete_note(self):
        """
        Тест.

        Проверяет, что зарегистрированный пользователь может удалять свои
        записи.
        """
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.DONE_URL)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """
        Тест.

        Проверяет, что пользователь, не являющийся автором записи, не может её
        удалить.
        """
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_note(self):
        """
        Тест.

        Проверяет, что зарегистрированный пользователь может редактировать свои
        записи.
        """
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.DONE_URL)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT_NEW)

    def test_user_cant_edit_note_of_another_user(self):
        """
        Тест.

        Проверяет, что пользователь, не являющийся автором записи, не может её
        редактировать.
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)


class TestNoteSlugUnique(TestCase):
    """
    Класс.

    Методы - это тесты, для проверки уникальности slug при создания записи.
    """

    NOTE_TITLE = 'Заголовок: Имперский Вояж'
    NOTE_TEXT = 'Текст'
    NOTE_SLUG_ONE = 'slug_one'
    NOTE_SLUG_TWO = 'slug_two'

    @classmethod
    def setUpTestData(cls):
        """
        Метод класса TestNoteSlugUnique.

        Создаёт временные объекты классов для тестов.
        """
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Олег Данильченко')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG_ONE,
        }
        Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG_ONE,
            author=cls.user,
        )

    def test_create_note_slug_note_is_unique(self):
        """
        Тест.

        Проверяет, что нельзя создать записи с одинаковым полем slug.
        """
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.NOTE_SLUG_ONE}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_edit_note_slug_note_is_unique(self):
        """
        Тест.

        Проверяет, что нельзя при редактирование записи изменить slug на уже
        существующий.
        """
        note_new = Note.objects.create(
            title=self.NOTE_TITLE,
            text=self.NOTE_TEXT,
            slug=self.NOTE_SLUG_TWO,
            author=self.user,
        )
        url_edit = reverse('notes:edit', args=(note_new.slug,))
        response = self.auth_client.get(url_edit)
        form = response.context['form']
        data = form.initial
        data['slug'] = self.NOTE_SLUG_ONE
        response_edit = self.auth_client.post(url_edit, data=data)
        self.assertFormError(
            response_edit,
            form='form',
            field='slug',
            errors=f'{self.NOTE_SLUG_ONE}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        note = Note.objects.get(pk=2)
        self.assertEqual(note.slug, self.NOTE_SLUG_TWO)
