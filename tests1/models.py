from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    Model,
    PositiveIntegerField,
    TextChoices,
)
from django.utils import timezone

from conts.models import NULLABLE


class Player(Model):
    """
    Модель игрока.
    """

    username = CharField(
        max_length=100,
        verbose_name="Username пользователя",
        help_text="Введите username пользователя",
        unique=True,
    )
    created_at = DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )
    updated_at = DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True,
    )
    first_login = DateTimeField(
        verbose_name="Дата первого входа",
        **NULLABLE,
    )
    last_login = DateTimeField(
        verbose_name="Дата последнего входа",
        **NULLABLE,
    )
    points = PositiveIntegerField(
        verbose_name="Количество очков",
        default=0,
    )
    current_level = PositiveIntegerField(
        default=0,
        verbose_name="Текущий уровень",
        help_text="Выберите текущий уровень",
        validators=[
            MinValueValidator(0),
            MaxValueValidator(3),
        ],
    )

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"

    def __str__(self):
        return self.username

    def handle_login(self):
        now = timezone.now()
        if self.first_login is None:
            self.first_login = now
        if not self.last_login or (now.date() > self.last_login.date()):
            self.points += 10
        self.last_login = now
        self.save()

    def award_boost(self, boost_type):
        # Удаляем существующий буст с тем же boost_type
        self.boosts.filter(boost_type=boost_type).delete()
        # Создаём новый буст
        Boost.objects.create(
            player=self,
            boost_type=boost_type,
            is_active=True,
        )

    def complete_level(self):
        if self.last_login is None:
            raise ValueError("Игроку нельзя повысить уровоень, так как он не заходил в игру.")
        if self.current_level >= 3:
            raise ValueError("Игрок достиг максимального уровня.")
        self.current_level += 1
        boosts_map = {
            1: BoostTypeChoices.X2_GOLD,
            2: BoostTypeChoices.X2_EXP,
            3: BoostTypeChoices.GOD_MODE,
        }
        boost_type = boosts_map.get(self.current_level)
        if boost_type:
            self.award_boost(boost_type)
        if self.current_level == 3:
            self.points += 100
        self.save()
        return True


class BoostTypeChoices(TextChoices):
    X2_GOLD = "x2_gold", "x2 золота"
    X2_EXP = "x2_exp", "x2 опыта"
    GOD_MODE = "god_mode", "Бессмертие"


class Boost(Model):
    """
    Модель буста.
    """

    player = ForeignKey(
        Player,
        on_delete=CASCADE,
        verbose_name="Игрок",
        help_text="Выберите игрока",
        related_name="boosts",
    )
    boost_type = CharField(
        max_length=100,
        choices=BoostTypeChoices.choices,
        verbose_name="Тип буста",
        help_text="Выберите тип буста",
    )
    awarded_at = DateTimeField(
        verbose_name="Дата выдачи",
        auto_now_add=True,
    )
    is_active = BooleanField(
        default=True,
        verbose_name="Статус буста",
        help_text="Выберите статус буста",
    )

    class Meta:
        verbose_name = "Буст"
        verbose_name_plural = "Бусты"
        unique_together = ["player", "boost_type"]

    def __str__(self):
        return f"У {self.player.username} - {self.get_boost_type_display()}"
