import datetime
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models
from django.db.models import Count


class PollManager(models.Manager):
    def published(self):
        return self.model.objects.filter(
            pub_date__lte=timezone.now()).annotate(
                num_choices=Count('choices')).filter(
                    num_choices__gte=2).distinct()


class Poll(models.Model):
    question = models.CharField(_('question field'), max_length=200)
    pub_date = models.DateTimeField(_('date published'))
    max_answers = models.IntegerField(
        default=1, help_text=_("The number of answers per poll vote"))

    objects = PollManager()

    class Meta:
        ordering = ["-pub_date", "question"]

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date < now

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = _('Published recently?')

    def __unicode__(self):
        return self.question


class Choice(models.Model):
    poll = models.ForeignKey(Poll, related_name='choices')
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    # http://toastdriven.com/blog/2011/apr/17/guide-to-testing-in-django-2/
    # if we needed to add logging when a vote is recoreded
    # then we only have to do it here
    def record_vote(self):
        self.votes += 1
        self.save()

    def __unicode__(self):
        return self.choice_text
