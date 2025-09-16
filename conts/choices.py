from django.db.models import TextChoices


class BoostTypeChoices(TextChoices):
    X2_GOLD = "x2_gold", "x2 золота"
    X2_EXP = "x2_exp", "x2 опыта"
    GOD_MODE = "god_mode", "Бессмертие"
