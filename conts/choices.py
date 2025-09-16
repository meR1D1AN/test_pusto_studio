from django.db.models import TextChoices


class BoostChoices(TextChoices):
    DOUBLE_XP_1_HOUR = "double_xp_1_hour", "Опыт х2 на 1 час"
    DOUBLE_XP_2_HOUR = "double_xp_2_hour", "Опыт х2 на 2 часа"
    DOUBLE_XP_4_HOUR = "double_xp_4_hour", "Опыт х2 на 4 часа"
    DOUBLE_MONEY_1_HOUR = "double_money_1_hour", "Деньги х2 на 1 час"
    DOUBLE_MONEY_2_HOUR = "double_money_1_hour", "Деньги х2 на 2 часа"
    DOUBLE_MONEY_4_HOUR = "double_money_1_hour", "Деньги х2 на 4 часа"
