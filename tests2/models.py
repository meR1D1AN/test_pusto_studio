from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    Model,
    PositiveIntegerField,
)
from django.utils import timezone

from conts.models import NULLABLE


class Player(Model):
    player_id = CharField(
        verbose_name="ID игрока",
        help_text="ID игрока в системе",
        max_length=100,
    )

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"

    def __str__(self):
        return self.player_id


class Level(Model):
    title = CharField(
        max_length=100,
        verbose_name="Название уровня",
        help_text="Введите название уровня",
    )
    order = IntegerField(
        verbose_name="Порядок",
        help_text="Введите порядок уровня",
        default=0,
    )

    class Meta:
        verbose_name = "Уровень"
        verbose_name_plural = "Уровни"

    def __str__(self):
        return f"№ {self.order} - {self.title}"


class Prize(Model):
    title = CharField(
        max_length=100,
        verbose_name="Название приза",
        help_text="Введите название приза",
    )

    class Meta:
        verbose_name = "Приз"
        verbose_name_plural = "Призы"

    def __str__(self):
        return self.title


class PlayerLevel(Model):
    player = ForeignKey(
        Player,
        verbose_name="Игрок",
        help_text="Выберите игрока",
        on_delete=CASCADE,
    )
    level = ForeignKey(
        Level,
        verbose_name="Уровень",
        help_text="Выберите уровень",
        on_delete=CASCADE,
    )
    completed = DateField(
        verbose_name="Дата завершения",
        help_text="Выберите дату завершения",
        **NULLABLE,
    )
    is_completed = BooleanField(
        verbose_name="Завершен",
        help_text="Да/Нет",
        default=False,
    )
    score = PositiveIntegerField(
        verbose_name="Счет",
        help_text="Введите счет",
        default=0,
    )

    class Meta:
        verbose_name = "Уровень игрока"
        verbose_name_plural = "Уровни игроков"
        unique_together = (
            "player",
            "level",
        )

    def __str__(self):
        return f"{self.player} - {self.level}"

    def save(self, *args, **kwargs):
        # Если поставили is_completed=True, а дату не ставили - ставим текущую дату
        if self.is_completed and self.completed is None:
            self.completed = timezone.now()

        # Если поставили дату завершения, а галочку не ставили - ставим is_completed=True
        if self.completed and not self.is_completed:
            self.is_completed = True

        super().save(*args, **kwargs)


class LevelPrize(Model):
    level = ForeignKey(
        Level,
        verbose_name="Уровень",
        help_text="Выберите уровень",
        on_delete=CASCADE,
    )
    prize = ForeignKey(
        Prize,
        verbose_name="Приз",
        on_delete=CASCADE,
    )

    class Meta:
        verbose_name = "Приз уровня"
        verbose_name_plural = "Призы уровней"

    def __str__(self):
        return f"{self.level} - {self.prize}"


class PlayerPrize(Model):
    player = ForeignKey(
        Player,
        verbose_name="Игрок",
        help_text="Выберите игрока",
        on_delete=CASCADE,
    )
    prize = ForeignKey(
        Prize,
        verbose_name="Приз",
        help_text="Выберите приз",
        on_delete=CASCADE,
    )
    level = ForeignKey(
        Level,
        verbose_name="Уровень",
        help_text="Выберите уровень",
        on_delete=CASCADE,
    )
    received = DateTimeField(
        verbose_name="Дата получения",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Приз игрока"
        verbose_name_plural = "Призы игроков"
        unique_together = ("player", "prize", "level")

    def __str__(self):
        return (
            f"{self.player.player_id.upper()} получил '{self.prize}' за прохождение уровня '{self.level}'. "
            f"Дата получения приза {self.received.strftime('%Y-%m-%d %H:%M:%S')}"
        )
