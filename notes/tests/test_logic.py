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
    """
    Класс TestNotesCreation.

    Методы - это тесты, для проверки создания записи.
    """

    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст'
    NOTE_SLUG = 'slug_one'
    NOTE_SLUG_TWO = 'slug_two'

    @classmethod
    def setUpTestData(cls):
        """
        Метод класса TestRoutes.

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
        self.assertRedirects(response, '/done/')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_create_note_slug_note_is_unique(self):
        """
        Тест.

        Проверяет, что нельзя создать записи с одинаковым полем slug.
        """
        Note.objects.create(
             title='Заголовок',
             text='Текст',
             slug=self.NOTE_SLUG,
             author=self.user,
        )
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.NOTE_SLUG}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_edit_note_slug_note_is_unique(self):
        """
        Тест.

        Проверяет, что нельзя при редактирование записи изменить slug на уже
        существующий.
        """
        Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug=self.NOTE_SLUG,
            author=self.user,
        )
        note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug=self.NOTE_SLUG_TWO,
            author=self.user,
        )
        url_edit = reverse('notes:edit', args=(note.slug,))
        response = self.auth_client.get(url_edit)
        form = response.context['form']
        data = form.initial
        data['slug'] = self.NOTE_SLUG
        response_edit = self.auth_client.post(url_edit, data=data)
        self.assertFormError(
            response_edit,
            form='form',
            field='slug',
            errors=f'{self.NOTE_SLUG}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        result = response_edit.context['form'].initial['slug']
        self.assertEqual(result, self.NOTE_SLUG_TWO)
