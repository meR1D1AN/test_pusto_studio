from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from tests1.models import Boost, Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """
    Админка для игроков.
    """

    list_display = (
        "id",
        "username",
        "created_at",
        "updated_at",
        "first_login",
        "last_login",
        "current_level",
        "points",
        "get_boosts",
    )
    list_filter = (
        "first_login",
        "last_login",
    )
    actions = [
        "trigger_login",
        "trigger_level",
    ]

    def trigger_login(self, request, queryset):
        """
        Экшен для совершения логина.
        """
        for player in queryset:
            player.handle_login()
        self.message_user(request, "Логин совершён.")

    trigger_login.short_description = "Совершить логин"

    def trigger_level(self, request, queryset):
        successes = []
        errors = []
        for player in queryset:
            try:
                player.complete_level()
                if player.current_level == 3:
                    successes.append(f"Игрок {player.username} повышен до максимального 3 уровня.")
                else:
                    successes.append(f"Уровень игрока {player.username} повышен до {player.current_level}.")
            except ValueError as e:
                errors.append(f"Ошибка для игрока {player.username}: {str(e)}.")
        message = ""
        if successes:
            message += " ".join(successes)
        if errors:
            message += " " + " ".join(errors)
        if message:
            level = messages.ERROR if errors else messages.SUCCESS
            self.message_user(request, message.strip(), level=level)
        else:
            self.message_user(request, "Ничего не изменено.", level=messages.WARNING)

    trigger_level.short_description = "Повысить уровень"

    def get_boosts(self, obj):
        """
        Метод отображения нескольких бустов.
        """
        boosts = obj.boosts.all().prefetch_related("player")
        if not boosts:
            return "Бустов нет"
        return format_html(
            "<br>".join(
                [
                    f"{boost.get_boost_type_display()} "
                    f"начислено: {timezone.localtime(boost.awarded_at).strftime('%d.%m.%Y %H:%M')}"
                    for boost in boosts
                ]
            )
        )

    get_boosts.short_description = "Бусты"


@admin.register(Boost)
class BoostAdmin(admin.ModelAdmin):
    """
    Админка для бустов.
    """

    list_display = (
        "id",
        "player",
        "boost_type",
        "awarded_at",
        "is_active",
    )
