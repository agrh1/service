from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    BotUser,
    Ticket,
    Log,
    SeafileLink,
    IntegrationSettings,
    IntraServiceSettings,
    SeafileSettings,
    TelegramSettings,
    LogFilter,
    CategoryMapping,
    ProcessingHistory,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff', 'is_active')


class BotUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = BotUser
        fields = ('id', 'user', 'role', 'is_active', 'created_at')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user, _ = User.objects.get_or_create(username=user_data['username'], defaults=user_data)
        return BotUser.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save()
        return super().update(instance, validated_data)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_id', 'status', 'created_at', 'updated_at']


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ['id', 'ticket', 'message', 'created_at']


class SeafileLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeafileLink
        fields = ['id', 'ticket', 'upload_link', 'download_link', 'password', 'status', 'created_at']


class IntegrationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationSettings
        fields = '__all__'


class IntraServiceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntraServiceSettings
        fields = '__all__'


class SeafileSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeafileSettings
        fields = '__all__'


class TelegramSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramSettings
        fields = '__all__'


class LogFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogFilter
        fields = '__all__'


class CategoryMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryMapping
        fields = '__all__'


class ProcessingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingHistory
        fields = '__all__'
