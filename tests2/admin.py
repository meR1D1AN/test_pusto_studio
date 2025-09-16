import csv

from django.contrib.admin import ModelAdmin, register
from django.db.models import Prefetch
from django.http import StreamingHttpResponse

from tests2.models import Level, LevelPrize, Player, PlayerLevel, PlayerPrize, Prize


@register(Player)
class PlayerAdmin(ModelAdmin):
    list_display = ("player_id",)
    search_fields = ("player_id",)


@register(Level)
class LevelAdmin(ModelAdmin):
    list_display = (
        "title",
        "order",
    )


@register(Prize)
class PrizeAdmin(ModelAdmin):
    list_display = ("title",)


class Echo:
    """
    Фейковые файлы объекта для csv.writter
    """

    def write(self, value):
        return value


@register(PlayerLevel)
class PlayerLevelAdmin(ModelAdmin):
    list_display = (
        "player",
        "level",
        "completed",
        "is_completed",
        "score",
    )
    list_filter = ("is_completed",)

    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        """
        Экспорт выбранные записи в CSV файл.
        """
        qs = (
            queryset.select_related("player", "level")
            .prefetch_related(
                Prefetch(
                    "player__playerprize_set",
                    queryset=PlayerPrize.objects.select_related("prize", "level"),
                    to_attr="all_prizes",
                )
            )
            .iterator(chunk_size=5000)
        )

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        def row_generator():
            # Заголовок
            yield writer.writerow(["player_id", "level_title", "is_completed", "prizes"])
            for pl in qs:
                prizes = [pp.prize.title for pp in getattr(pl.player, "all_prizes", []) if pp.level_id == pl.level_id]
                yield writer.writerow(
                    [
                        pl.player.player_id,
                        pl.level.title,
                        "Да" if pl.is_completed else "Нет",
                        ", ".join(prizes) if prizes else "",
                    ]
                )

        response = StreamingHttpResponse(row_generator(), content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="player_levels.csv"'
        return response

    export_as_csv.short_description = "Выгрузить выбранные записи в CSV"


@register(LevelPrize)
class LevelPrizeAdmin(ModelAdmin):
    list_display = (
        "level",
        "prize",
    )


@register(PlayerPrize)
class PlayerPrizeAdmin(ModelAdmin):
    list_display = (
        "player",
        "prize",
        "level",
        "received",
    )
