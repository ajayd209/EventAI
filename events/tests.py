from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from events.models import Event, EventTimeline
from datetime import date

class EventAuthAndPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        self.event1 = Event.objects.create(
            created_by=self.user1,
            event_name='User 1 Event',
            event_type='Conference',
            location='NY',
            event_date=date(2027, 10, 10),
            expected_crowd=100
        )

    def test_unauthenticated_access_blocked(self):
        """Ensure logged-out users cannot access the workspace"""
        response = self.client.get(reverse('events:workspace', args=[self.event1.id]))
        # Should redirect to login
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/events/workspace/{self.event1.id}/")

    def test_authenticated_access_allowed(self):
        """Ensure owner can access their own workspace"""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('events:workspace', args=[self.event1.id]))
        self.assertEqual(response.status_code, 200)

    def test_cross_user_access_blocked(self):
        """Ensure User 2 gets 403 Forbidden when trying to access User 1's event"""
        self.client.login(username='user2', password='password123')
        response = self.client.get(reverse('events:workspace', args=[self.event1.id]))
        self.assertEqual(response.status_code, 403)

    def test_task_status_update_permission(self):
        """Ensure User 2 cannot update User 1's task"""
        task = EventTimeline.objects.create(
            event=self.event1, title='Test Task', days_before_event=5, due_date=date(2027, 10, 5)
        )
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('events:update_task_status', args=[task.id]), {'status': 'Completed'})
        self.assertEqual(response.status_code, 403)
