from django.db import models

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
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    upload_link = models.TextField(null=True, blank=True)
    download_link = models.TextField(null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Links for ticket {self.ticket.ticket_id}"
    
    class Meta:
        db_table = 'seafile_links'

