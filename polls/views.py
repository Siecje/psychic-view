import logging
logger = logging.getLogger('mysite.log')
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from polls.models import Poll
from polls.forms import PollForm


class PublishedPollMixin(object):
    def get_queryset(self):
        #super(PublishedPollMixin, self).get_queryset()
        return self.model.objects.published()


class PollFormMixin(SingleObjectMixin):
    """
    puts form and "view results link" in context
    and validates and saves the form
    """
    model = Poll

    def get_context_data(self, **kwargs):
        context = super(PollFormMixin, self).get_context_data(**kwargs)
        form = PollForm(instance=self.get_object())
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        form = PollForm(request.POST, instance=self.get_object())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(self.success_url)
        else:
            return render(request, self.template_name,
                {'form': form, 'poll': self.get_object()})


class IndexView(PublishedPollMixin, ListView):
    """
    List of links to DetailView of all published polls
    """

    model = Poll
    template_name = 'polls/index.html'
    context_object_name = 'latest_poll_list'

    def get_queryset(self):
        """
        Return the last five published polls
        (not including those with one choice or set to be
        published in the future).
        """
        qs = super(IndexView, self).get_queryset()
        return qs[:5]
        #return Poll.objects.published()[:5]


class DetailView(PublishedPollMixin, PollFormMixin, DetailView):
    """
    Vote on a poll
    """
    model = Poll
    template_name = 'polls/detail.html'

    @property
    def success_url(self):
        return reverse(
            'polls:results', args=(self.get_object().id,))


class ResultsView(DetailView):
    model = Poll
    template_name = 'polls/results.html'
