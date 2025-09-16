import os
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from conts.choices import BoostTypeChoices
from tests1.models import Player


class Command(BaseCommand):
    help = "Команда для создания тестовых данных для первой части задания. А так же создание админа."

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            # Создание админа
            self.create_admin()
            # # Создание игроков с бустами
            self.create_players_with_boosts()

    def create_admin(self):
        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
            )
            user.set_password(password)
            user.save()

            self.stdout.write(self.style.SUCCESS(f"Админ {username} создан успешно."))
        else:
            self.stdout.write(self.style.WARNING(f"Админ {username} уже существует."))

    def create_players_with_boosts(self):
        fake = Faker()
        players_to_create = 10
        created_count = 0
        attempts = 0
        max_attempts = 50

        while created_count < players_to_create and attempts < max_attempts:
            username = fake.user_name()

            if Player.objects.filter(username=username).exists():
                attempts += 1
                continue

            # Генерируем наивную дату для created_at и преобразуем в осведомлённую
            naive_datetime = fake.date_time_this_year()
            aware_datetime = timezone.make_aware(naive_datetime)

            # Генерируем дату для first_login: created_at + 1, 2 или 3 дня
            days_to_add = random.randint(1, 3)
            first_login = aware_datetime + timedelta(days=days_to_add)

            # Генерируем last_login: случайная дата между first_login и текущей датой
            last_login = timezone.make_aware(
                fake.date_time_between(start_date=first_login + timedelta(days=1), end_date="now")
            )

            # Создаём игрока без указания created_at, first_login и last_login
            player = Player.objects.create(
                username=username,
            )
            # Устанавливаем created_at, first_login и начисляем очки за первый вход
            player.created_at = aware_datetime
            player.first_login = first_login
            player.last_login = first_login
            player.points += 10  # Начисляем 10 очков за первый вход
            player.login_days_count += 1  # Увеличиваем счётчик дней логина
            player.save()

            # Имитация случайных входов для начисления очков
            login_count = random.randint(0, 20)
            current_date = first_login + timedelta(days=1)
            for _ in range(login_count):
                # Генерируем случайную дату входа между current_date и last_login
                login_date = timezone.make_aware(fake.date_time_between(start_date=current_date, end_date=last_login))
                # Устанавливаем временную дату для last_login и вызываем handle_login
                player.last_login = login_date
                player.handle_login()
                current_date = login_date + timedelta(days=1)  # Переходим к следующему дню

            # Начисление случайного количества уровней
            level_count = random.randint(0, 3)  # Случайное количество уровней (0–3)
            for _ in range(level_count):
                try:
                    player.complete_level()
                except ValueError as e:
                    self.stdout.write(self.style.WARNING(f"Ошибка для {username}: {str(e)}"))
                    break

            # Случайный вызов complete_level для игроков с уровнем 1
            if player.current_level == 1 and random.choice([True, False]):
                try:
                    player.complete_level()
                    self.stdout.write(
                        self.style.SUCCESS(f"Уровень для {username} повышен до 2 (случайное повышение).")
                    )
                except ValueError as e:
                    self.stdout.write(
                        self.style.WARNING(f"Ошибка при случайном повышении уровня для {username}: {str(e)}")
                    )

            # Начисление случайного буста для игроков с уровнем 0
            if player.current_level == 0:
                random_boost_type = random.choice([choice[0] for choice in BoostTypeChoices.choices])
                player.award_boost(random_boost_type)

            # Восстанавливаем last_login
            player.last_login = last_login
            player.save()

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Игрок {username} создан успешно с датой создания "
                    f"{player.created_at.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"первым входом {player.first_login.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"последним входом {player.last_login.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"очками {player.points}, уровнем {player.current_level}, "
                    f"бустами {player.boosts.count()}, днями логина {player.login_days_count} "
                    f"(входы: {login_count + 1})."
                )
            )
            attempts = 0

        if created_count < players_to_create:
            self.stdout.write(
                self.style.WARNING(f"Создано только {created_count} игроков из-за проблем с уникальностью имён.")
            )
