import uuid

from django.core.management import BaseCommand
from django.db import transaction
from faker import Faker
from tqdm import tqdm

from tests2.models import Level, LevelPrize, Player, PlayerLevel, PlayerPrize, Prize


class Command(BaseCommand):
    help = "Команда для создания тестовых данных для второй части задания."

    def handle(self, *args, **kwargs):
        self.fake = Faker("ru_RU")
        self.count_size = 100000
        self.batch_size = 5000

        with transaction.atomic():
            self.base_bulk_all_models_create()
            self.create_level_prizes()
            self.create_player_levels()

    def base_bulk_all_models_create(self):
        tasks = [
            (Player, "игроков", self._create_players),
            (Level, "уровней", self._create_levels),
            (Prize, "призов", self._create_prizes),
        ]

        for model_class, desc, create_func in tasks:
            instances = [create_func() for _ in tqdm(range(self.count_size), desc=f"Создание {desc}")]
            created_count = len(instances)
            model_class.objects.bulk_create(instances, batch_size=self.batch_size)
            self.stdout.write(self.style.SUCCESS(f"Создано {created_count} новых {desc}"))

    def _create_players(self):
        return Player(player_id=f"{self.fake.user_name()} {uuid.uuid4()}")

    def _create_levels(self):
        return Level(
            title=f"{self.fake.sentence(nb_words=3, variable_nb_words=True)}",
            order=self.fake.random_int(min=1, max=99),
        )

    def _create_prizes(self):
        return Prize(title=f"{self.fake.sentence(nb_words=3, variable_nb_words=True)}")

    def _create_level_prize(self, levels_ids, prizes_ids):
        level_id = self.fake.random_element(levels_ids)
        prize_id = self.fake.random_element(prizes_ids)
        return LevelPrize(level_id=level_id, prize_id=prize_id)

    def create_level_prizes(self):
        levels_ids = list(Level.objects.values_list("id", flat=True))
        prizes_ids = list(Prize.objects.values_list("id", flat=True))

        instances = [
            self._create_level_prize(levels_ids, prizes_ids)
            for _ in tqdm(range(self.count_size), desc="Создание связей уровень-приз")
        ]

        # Убираем дубли
        seen = set()
        unique_instances = []
        for obj in instances:
            pair = (obj.level_id, obj.prize_id)
            if pair not in seen:
                seen.add(pair)
                unique_instances.append(obj)

        created_count = len(unique_instances)
        LevelPrize.objects.bulk_create(unique_instances, batch_size=self.batch_size)
        self.stdout.write(self.style.SUCCESS(f"Создано {created_count} новых связей уровень-приз"))

    def create_player_levels(self):
        """Создаёт связи игрок-уровень и массово выдаёт призы за завершённые уровни."""
        players_ids = list(Player.objects.values_list("id", flat=True))
        levels_ids = list(Level.objects.values_list("id", flat=True))

        if not players_ids or not levels_ids:
            self.stdout.write(self.style.WARNING("Нет игроков или уровней для связывания!"))
            return

        count = self.count_size

        # Подготавливаем объекты PlayerLevel
        instances = []
        completed_pairs = []

        for _ in tqdm(
            range(count),
            desc="Создание прогресса игроков по уровням",
        ):
            player_id = self.fake.random_element(players_ids)
            level_id = self.fake.random_element(levels_ids)

            is_completed = self.fake.boolean(chance_of_getting_true=50)
            completed = self.fake.date_time_this_year() if is_completed else None

            instance = PlayerLevel(
                player_id=player_id,
                level_id=level_id,
                is_completed=is_completed,
                completed=completed,
            )
            instances.append(instance)

            if is_completed:
                completed_pairs.append((player_id, level_id))

        # Убираем дубли по (player_id, level_id)
        seen = set()
        unique_instances = []
        for obj in instances:
            pair = (obj.player_id, obj.level_id)
            if pair not in seen:
                seen.add(pair)
                unique_instances.append(obj)

        # Создаём PlayerLevel
        created_objs = PlayerLevel.objects.bulk_create(
            unique_instances,
            batch_size=self.batch_size,
            ignore_conflicts=True,
        )
        created_count = len(created_objs)
        self.stdout.write(self.style.SUCCESS(f"Создано {created_count} записей прогресса игроков"))

        if completed_pairs:
            self.stdout.write("Массовая выдача призов за завершённые уровни...")

            # Шаг 1: получить все призы, привязанные к этим уровням
            level_ids_from_pairs = {level_id for _, level_id in completed_pairs}
            level_prizes = LevelPrize.objects.filter(level_id__in=level_ids_from_pairs).select_related("prize")

            prizes_by_level = {}
            for level_prize in level_prizes:
                prizes_by_level.setdefault(level_prize.level_id, []).append(level_prize.prize)

            # Шаг 2: создаём PlayerPrize объекты для всех (player, prize, level)
            player_prize_instances = []
            for player_id, level_id in tqdm(
                completed_pairs,
                desc="Подготовка призов",
            ):
                if level_id not in prizes_by_level:
                    continue
                for prize in prizes_by_level[level_id]:
                    player_prize_instances.append(
                        PlayerPrize(
                            player_id=player_id,
                            prize=prize,
                            level_id=level_id,
                            received=self.fake.date_time_this_year(),
                        )
                    )

            # Шаг 3: массовое создание с игнорированием дублей
            if player_prize_instances:
                created_prizes = PlayerPrize.objects.bulk_create(
                    player_prize_instances,
                    batch_size=self.batch_size,
                    ignore_conflicts=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Выдано {len(created_prizes)} призов игрокам"))
            else:
                self.stdout.write(self.style.WARNING("Нет призов для выдачи"))
