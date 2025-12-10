from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BotUser(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        OPERATOR = 'operator', 'Оператор'
        VIEWER = 'viewer', 'Наблюдатель'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bot_profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'Пользователь бота'
        verbose_name_plural = 'Пользователи бота'

class Ticket(models.Model):
    ticket_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Ticket {self.ticket_id}"
    
    class Meta:
        db_table = 'tickets'

class Log(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Log for ticket {self.ticket.ticket_id}"
    
    class Meta:
        db_table = 'logs'

class SeafileLink(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        AVAILABLE = 'available', 'Доступна'
        FAILED = 'failed', 'Ошибка'

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    upload_link = models.TextField(null=True, blank=True)
    download_link = models.TextField(null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Links for ticket {self.ticket.ticket_id}"
    
    class Meta:
        db_table = 'seafile_links'


class IntegrationSettings(models.Model):
    name = models.CharField(max_length=100, unique=True)
    api_url = models.URLField()
    api_token = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Настройка интеграции'
        verbose_name_plural = 'Настройки интеграций'


class IntraServiceSettings(models.Model):
    base_url = models.URLField()
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    default_queue = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"IntraService {self.base_url}"


class SeafileSettings(models.Model):
    server_url = models.URLField()
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    library_id = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Seafile {self.server_url}"


class TelegramSettings(models.Model):
    bot_token = models.CharField(max_length=255)
    chat_id = models.CharField(max_length=255)
    webhook_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Telegram настройки"


class LogFilter(models.Model):
    name = models.CharField(max_length=150, unique=True)
    pattern = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CategoryMapping(models.Model):
    source_category = models.CharField(max_length=150)
    target_category = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_category', 'target_category')

    def __str__(self):
        return f"{self.source_category} -> {self.target_category}"


class ProcessingHistory(models.Model):
    ticket = models.ForeignKey(Ticket, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.status} at {self.created_at}"

