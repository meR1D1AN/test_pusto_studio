from django.db.models.signals import post_save
from django.dispatch import receiver

from tests2.models import PlayerLevel
from tests2.services import assign_prizes_for_level


@receiver(post_save, sender=PlayerLevel)
def give_prizes_on_completion(sender, instance, created, **kwargs):
    if instance.completed:
        assign_prizes_for_level(instance.player, instance.level)
