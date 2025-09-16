from django.db import transaction
from django.utils import timezone

from tests2.models import LevelPrize, PlayerLevel, PlayerPrize


def assign_prizes_for_level(player, level):
    """
    Выдать игроку все призы за указанный уровень, если он завершён.
    Возвращает список новых PlayerPrize.
    """

    player_level = PlayerLevel.objects.get(player=player, level=level)
    if not player_level.is_completed:
        raise ValueError("Уровень не завершён — призы недоступны.")

    prizes = LevelPrize.objects.filter(level=level).select_related("prize")

    created_prizes = []
    with transaction.atomic():
        for level_prize in prizes:
            player_prize, created = PlayerPrize.objects.get_or_create(
                player=player,
                prize=level_prize.prize,
                level=level,
                defaults={"received": timezone.now()},
            )
            if created:
                created_prizes.append(player_prize)

    return created_prizes
