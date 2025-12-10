from django.test import TestCase
from django.contrib.auth import get_user_model
from api.models import BotUser, Ticket, SeafileLink, LogFilter, CategoryMapping


class ModelCreationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username='tester')

    def test_bot_user_creation(self):
        bot_user = BotUser.objects.create(user=self.user, role=BotUser.Role.ADMIN)
        self.assertEqual(bot_user.role, BotUser.Role.ADMIN)

    def test_ticket_and_link(self):
        ticket = Ticket.objects.create(ticket_id=123)
        link = SeafileLink.objects.create(ticket=ticket)
        self.assertEqual(link.status, SeafileLink.Status.PENDING)

    def test_mapping_unique(self):
        CategoryMapping.objects.create(source_category='raw', target_category='clean')
        with self.assertRaises(Exception):
            CategoryMapping.objects.create(source_category='raw', target_category='clean')

    def test_log_filter_active_default(self):
        log_filter = LogFilter.objects.create(name='errors', pattern='ERROR')
        self.assertTrue(log_filter.is_active)
