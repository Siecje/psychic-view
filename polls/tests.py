import datetime
from django.utils import timezone
from django.test import TestCase
from django.core.urlresolvers import reverse
from polls.models import Poll, Choice
from polls.forms import PollForm
from django import forms
# selenium tests
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def create_poll(question, days):
    """
    Creates a poll with the given `question` published the given number of
    `days` offset to now (negative for polls published in the past,
    positive for polls that have yet to be published).
    """
    return Poll.objects.create(question=question,
        pub_date=timezone.now() + datetime.timedelta(days=days))


def assign_two_choices(poll):
    """
    Creates two choices for the given poll
    A poll needs at least two choices to be valid
    """
    choice1 = Choice.objects.create(choice_text="choice one", poll=poll)
    choice2 = Choice.objects.create(choice_text="choice two", poll=poll)


class PollMethodTests(TestCase):

    def test_was_published_recently_with_future_poll(self):
        """
        was_published_recently() should return False for polls whose
        pub_date is in the future
        """
        future_poll = Poll(
            pub_date=timezone.now() + datetime.timedelta(days=30))
        self.assertEqual(future_poll.was_published_recently(), False)

    def test_was_published_recently_with_old_poll(self):
        """
        was_published_recently() should return False for polls whose pub_date
        is older than 1 day
        """
        old_poll = Poll(pub_date=timezone.now() - datetime.timedelta(days=30))
        self.assertEqual(old_poll.was_published_recently(), False)

    def test_was_published_recently_with_recent_poll(self):
        """
        was_published_recently() should return True for polls whose pub_date
        is within the last day
        """
        recent_poll = Poll(
            pub_date=timezone.now() - datetime.timedelta(hours=1))
        self.assertEqual(recent_poll.was_published_recently(), True)

    def test_published_with_invalid_poll(self):
        """
        Test that a poll with one option
        is not in Poll.objects.published()
        """
        invalid_poll = Poll.objects.create(
            question="invalid poll", pub_date=timezone.now())
        choice1 = Choice.objects.create(
            choice_text="only option", poll=invalid_poll)
        self.assertEqual(Poll.objects.published().count(), 0)

    def test_unicode(self):
        """
        str(Poll) or unicode(Poll) should be the question
        """
        poll = create_poll(question="Testing unicode", days=0)
        self.assertEqual(str(poll), poll.question)
        self.assertEqual(unicode(poll), poll.question)
        self.assertEqual(str(poll), unicode(poll))


class ChoiceMethodTests(TestCase):
    def test_unicode(self):
        """
        str(Choice) or unicode(Choice) should be the choice_text
        """
        poll = create_poll(question="Testing unicode", days=0)
        choice = Choice(poll=poll, choice_text="Testing is fun!")
        choice.save()
        self.assertEqual(str(choice), choice.choice_text)
        self.assertEqual(unicode(choice), choice.choice_text)
        self.assertEqual(str(choice), unicode(choice))

    def test_record_vote(self):
        """
        Testing that record_vote() increments votes properly
        """
        poll = create_poll(question="not important", days=-1)
        choice_1 = Choice.objects.create(choice_text="choice 1", poll=poll)
        choice_2 = Choice.objects.create(choice_text="choice 2", poll=poll)
        #use db lookup to test if it is getting saved
        #and not hardcode id so that we can add fixtures later
        choice_1_id = choice_1.id
        choice_2_id = choice_2.id
        self.assertEqual(Choice.objects.get(id=choice_1_id).votes, 0)
        self.assertEqual(Choice.objects.get(id=choice_2_id).votes, 0)
        choice_1.record_vote()
        self.assertEqual(Choice.objects.get(id=choice_1_id).votes, 1)
        self.assertEqual(Choice.objects.get(id=choice_2_id).votes, 0)
        choice_2.record_vote()
        self.assertEqual(Choice.objects.get(id=choice_1_id).votes, 1)
        self.assertEqual(Choice.objects.get(id=choice_2_id).votes, 1)
        choice_1.record_vote()
        self.assertEqual(Choice.objects.get(id=choice_1_id).votes, 2)
        self.assertEqual(Choice.objects.get(id=choice_2_id).votes, 1)


class PollIndexTests(TestCase):
    def test_index_view_with_no_polls(self):
        """
        If no polls exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_poll_list'], [])

    def test_index_view_with_a_past_poll(self):
        """
        Polls with a pub_date in the past should be displayed on the index page.
        """
        poll = create_poll(question="Past poll.", days=-30)
        assign_two_choices(poll)
        response = self.client.get(reverse('polls:index'))
        self.assertTrue('latest_poll_list' in response.context)
        self.assertEqual([p.id for p in response.context['latest_poll_list']],
            [poll.id])
        #self.assertQuerysetEqual(
        #    response.context['latest_poll_list'],
            #repr(Poll.objects.filter(question="Past poll."))
        #    ['<Poll: Past poll.>']
        #)

    def test_index_view_with_a_future_poll(self):
        """
        Polls with a pub_date in the future should not be displayed on the
        index page.
        """
        create_poll(question="Future poll.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(
            response, "No polls are available.", status_code=200)
        self.assertQuerysetEqual(response.context['latest_poll_list'], [])

    def test_index_view_with_future_poll_and_past_poll(self):
        """
        Even if both past and future polls exist, only past polls should be
        displayed.
        """
        past_poll = create_poll(question="Past poll.", days=-30)
        assign_two_choices(past_poll)
        future_poll = create_poll(question="Future poll.", days=30)
        assign_two_choices(future_poll)
        response = self.client.get(reverse('polls:index'))
        self.assertEqual([p.id for p in response.context['latest_poll_list']],
            [past_poll.id])
        #self.assertQuerysetEqual(
        #    response.context['latest_poll_list'],
        #    ['<Poll: Past poll.>']
        #)

    def test_index_view_with_two_past_polls(self):
        """
        The polls index page may display multiple polls.
        """
        poll1 = create_poll(question="Past poll 1.", days=-30)
        assign_two_choices(poll1)
        poll2 = create_poll(question="Past poll 2.", days=-5)
        assign_two_choices(poll2)
        response = self.client.get(reverse('polls:index'))
        self.assertEqual([p.id for p in response.context['latest_poll_list']],
            [poll2.id, poll1.id])
        #self.assertQuerysetEqual(
        #    response.context['latest_poll_list'],
        #     ['<Poll: Past poll 2.>', '<Poll: Past poll 1.>']
        #)

    def test_index_with_with_invalid_poll(self):
        """
        Test that a poll with one option does not show up on the index page
        """
        invalid_poll = create_poll(question="poll with no choices", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertEqual([p.id for p in response.context['latest_poll_list']],
            [])
        poll_with_one_choice = create_poll(
            question="poll with one choice", days=-3)
        choice1 = Choice.objects.create(
            choice_text="test", poll=poll_with_one_choice)
        self.assertEqual([p.id for p in response.context['latest_poll_list']],
            [])

    def test_index_with_valid_and_invalid_poll(self):
        """
        Test that a poll with one option does not show up on the index page
        but a valid poll still does
        """
        valid_poll = create_poll(question="Past poll 1.", days=-30)
        assign_two_choices(valid_poll)
        invalid_poll1 = create_poll(question="poll with no choices", days=-30)
        invalid_poll2 = create_poll(question="another invalid", days=-10)
        choice1 = Choice.objects.create(
            choice_text="choice one", poll=invalid_poll2)
        response = self.client.get(reverse('polls:index'))
        self.assertEqual([p.id for p in response.context['latest_poll_list']],
            [valid_poll.id])


class PollDetailViewTests(TestCase):
    def test_detail_view_with_a_future_poll(self):
        """
        The detail view of a valid poll with a pub_date in the future should
        return a 404 not found.
        """
        future_poll = create_poll(question='Future poll.', days=5)
        assign_two_choices(future_poll)
        response = self.client.get(
            reverse('polls:detail', args=(future_poll.id,)))
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_poll(self):
        """
        The detail view of a poll with a pub_date in the past should display
        the poll's question.
        """
        past_poll = create_poll(question='Past Poll.', days=-5)
        assign_two_choices(past_poll)
        response = self.client.get(
            reverse('polls:detail', args=(past_poll.id,)))
        self.assertContains(response, past_poll.question, status_code=200)

    def test_no_choices_poll_response(self):
        """
        Given a poll without choices it should 404
        """
        invalid_poll = create_poll(question="This poll has no choices", days=0)
        response = self.client.get(
            reverse('polls:detail', args=(invalid_poll.id,)))
        self.assertEqual(response.status_code, 404)

    def test_no_poll(self):
        """
        Trying to view detail with a poll that doesn't exist is a 404
        """
        response = self.client.get(reverse('polls:detail', args=(1,)))
        self.assertEqual(response.status_code, 404)


class PollVoteViewTests(TestCase):
    def setUp(self):
        #TODO: why do you need this?
        #TODO: and why does it contain the name?
        #TODO: why can't it just be super and copy and paste friendly
        super(PollVoteViewTests, self).setUp()  # don't forget this
        self.multi_answer_poll = Poll.objects.create(
            question="Can you submit more than one answer",
            pub_date=timezone.now(),
            max_answers=2)
        self.choice_31 = Choice.objects.create(
            choice_text="One", poll=self.multi_answer_poll)
        self.choice_32 = Choice.objects.create(
            choice_text="Two", poll=self.multi_answer_poll)
        self.choice_33 = Choice.objects.create(
            choice_text="Three", poll=self.multi_answer_poll)

    def test_vote_on_valid_poll(self):
        """
        Test that submitting the form with a valid poll
        and valid choice from a real page,
        increments the votes for the given choice, and not other choices
        """
        valid_poll = Poll.objects.create(
            question="Test questions", pub_date=timezone.now(), max_answers=1)
        choice1 = Choice.objects.create(
            choice_text="choice one", poll=valid_poll)
        choice2 = Choice.objects.create(
            choice_text="choice two", poll=valid_poll)
        choice3 = Choice.objects.create(
            choice_text="test", poll=valid_poll)
        response = self.client.get(
            reverse('polls:detail', args=(valid_poll.id,)))
        form = response.context['form']
        data = form.initial
        data['choice'] = choice3.id
        response = self.client.post(
            reverse('polls:detail', args=(valid_poll.id,)), data)
        #have to get the choice object again
        #when do you have to do that?
        choice1 = Choice.objects.get(choice_text="choice one")
        self.assertEqual(choice1.votes, 0)
        choice2 = Choice.objects.get(choice_text="choice two")
        self.assertEqual(choice2.votes, 0)
        choice3 = Choice.objects.get(choice_text="test")
        self.assertEqual(choice3.votes, 1)

    def test_vote_on_valid_poll_invalid_choice(self):
        """
        Test that sumbitting with a valid poll
        but a choice that is not in the form
        """
        valid_poll = Poll.objects.create(
            question="Test questions", pub_date=timezone.now(), max_answers=1)
        choice1 = Choice.objects.create(choice_text="choice one", poll=valid_poll)
        choice2 = Choice.objects.create(
            choice_text="choice two", poll=valid_poll)
        choice3 = Choice.objects.create(choice_text="test", poll=valid_poll)
        invalid_poll = Poll.objects.create(
            question="invalid poll", pub_date=timezone.now(), max_answers=1)
        choice4 = Choice.objects.create(
            choice_text="invalid", poll=invalid_poll)
        response = self.client.get(
            reverse('polls:detail', args=(valid_poll.id,)))
        form = response.context['form']
        data = form.initial
        data['choice'] = choice4.id
        response = self.client.post(
            reverse('polls:detail', args=(valid_poll.id,)), data)
        choice1 = Choice.objects.get(choice_text="choice one")
        self.assertEqual(choice1.votes, 0)
        choice2 = Choice.objects.get(choice_text="choice two")
        self.assertEqual(choice2.votes, 0)
        choice3 = Choice.objects.get(choice_text="test")
        self.assertEqual(choice3.votes, 0)

    def test_no_choice_on_valid_poll(self):
        """
        Test that submitting the form with no choice displays an error message
        """
        valid_poll = create_poll(question='Past Poll.', days=-5)
        assign_two_choices(valid_poll)
        choice = Choice.objects.create(
            choice_text="test", poll=valid_poll)
        response = self.client.get(
            reverse('polls:detail', args=(valid_poll.id,)))
        form = response.context['form']
        data = form.initial
        #had to add follow=True to get messages
        response = self.client.post(
            reverse('polls:detail', args=(valid_poll.id,)), data, follow=True)
        self.assertContains(response, "required")

    def test_multiple_valid_post(self):
        """
        Test that you can submit with 2 options
        for a poll that has max_answers=2
        """
        self.assertEqual(self.choice_31.votes, 0)
        self.assertEqual(self.choice_32.votes, 0)
        self.assertEqual(self.choice_33.votes, 0)
        response = self.client.get(
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        form = response.context['form']
        data = form.initial
        data['choice'] = [self.choice_31.id, self.choice_32.id]
        response = self.client.post(
            reverse('polls:detail', args=(self.multi_answer_poll.id,)), data)
        choice1 = Choice.objects.get(id=self.choice_31.id)
        choice2 = Choice.objects.get(id=self.choice_32.id)
        choice3 = Choice.objects.get(id=self.choice_33.id)
        self.assertEqual(choice1.votes, 1)
        self.assertEqual(choice2.votes, 1)
        self.assertEqual(choice3.votes, 0)

    def test_radio_field(self):
        """
        Test that when max_answers=1 that a radio field is used
        """
        valid_poll = create_poll(question='Past Poll.', days=-5)
        assign_two_choices(valid_poll)
        response = self.client.get(
            reverse('polls:detail', args=(valid_poll.id,)))

        self.assertContains(response, 'type="radio"')
        #self.assertFalse(self.assertContains(response, 'type="checkbox"'))
        #TODO: would be nice to test a form 's values incase the page has
        #TODO: multiple forms
        #form = response.context['form']
        #self.assertContains(form, "radio")
        #self.assertFalse(self.assertContains(form, "checkbox"))

    def test_checkbox_field(self):
        """
        Test that when max_answer > 1 then a checkbox field is used
        """
        response = self.client.get(
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        self.assertContains(response, 'type="checkbox"')
        #form = response.context['form']
        #self.assertContains(form, "checkbox")
        #self.assertFalse(self.assertContains(form, "radio"))

    def test_too_many_answers(self):
        """
        Test that submitting more options that max_answers will not work
        and display an error message
        """
        response = self.client.get(
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        form = response.context['form']
        data = form.initial
        data['choice'] = [
            self.choice_31.id, self.choice_32.id, self.choice_33.id]
        #had to add follow=True to get messages
        response = self.client.post(
            reverse('polls:detail', args=(
                self.multi_answer_poll.id,)), data, follow=True)
        self.assertContains(response, "Too many")

    def test_one_answer_with_many_answers(self):
        """
        Test that you can still select just one option even though
        the max is 2
        """
        self.assertEqual(self.choice_31.votes, 0)
        self.assertEqual(self.choice_32.votes, 0)
        self.assertEqual(self.choice_33.votes, 0)
        response = self.client.get(
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        form = response.context['form']
        data = form.initial
        data['choice'] = [self.choice_31.id]
        #had to add follow=True to get messages
        response = self.client.post(
            reverse('polls:detail', args=(self.multi_answer_poll.id,)), data)
        choice1 = Choice.objects.get(id=self.choice_31.id)
        choice2 = Choice.objects.get(id=self.choice_32.id)
        choice3 = Choice.objects.get(id=self.choice_33.id)
        self.assertEqual(choice1.votes, 1)
        self.assertEqual(choice2.votes, 0)
        self.assertEqual(choice3.votes, 0)

    #TODO: test that required is red?

class PollResultsViewTests(TestCase):
    def test_no_poll(self):
        """
        Test that no poll will be a 404
        """
        response = self.client.get(reverse('polls:results', args=(1,)))
        self.assertEqual(response.status_code, 404)

    def test_valid_poll(self):
        """
        Test that the page works with a valid poll
        """
        poll = create_poll(question="Valid Poll", days=-1)
        assign_two_choices(poll)
        response = self.client.get(reverse('polls:results', args=(poll.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['poll'].id, poll.id)
        self.assertEqual(response.context['poll'].question, "Valid Poll")

    def test_invalid_poll(self):
        """
        Test that an invalid poll gives a 404 page
        """
        invalid_poll1 = create_poll(question="invalid1", days=-1)
        response = self.client.get(
            reverse('polls:results', args=(invalid_poll1.id,)))
        self.assertEqual(response.status_code, 404)
        invalid_poll2 = create_poll(question="invalid2", days=-2)
        choice1 = Choice.objects.create(
            choice_text="choice1", poll=invalid_poll2)
        response = self.client.get(
            reverse('polls:results', args=(invalid_poll2.id,)))
        self.assertEqual(response.status_code, 404)

#test status_code == 302 when valid form
class PollFormTests(TestCase):
    def setUp(self):
        super(PollFormTests, self).setUp()
        self.poll_1 = create_poll(question="First Poll", days=-1)
        self.choice_11 = Choice.objects.create(choice_text="Yes", poll=self.poll_1)
        self.choice_12 = Choice.objects.create(choice_text="No", poll=self.poll_1)
        self.poll_2 = create_poll(question="Second Poll", days=-1)
        self.multi_answer_poll = Poll.objects.create(
            question="Can you submit more than one answer",
            pub_date=timezone.now(),
            max_answers=2)
        self.choice_31 = Choice.objects.create(
            choice_text="One", poll=self.multi_answer_poll)
        self.choice_32 = Choice.objects.create(
            choice_text="Two", poll=self.multi_answer_poll)
        self.choice_33 = Choice.objects.create(
            choice_text="Three", poll=self.multi_answer_poll)

    def test_form_without_data(self):
        """
        Test that PollForm is working without data (post)
        """
        form = PollForm(instance=self.poll_1)
        self.assertTrue(isinstance(form.instance, Poll))
        self.assertEqual(form.instance.pk, self.poll_1.pk)
        self.assertEqual([c for c in form.fields['choice'].choices],
            [(self.choice_11.id, self.choice_11.choice_text),
                (self.choice_12.id, self.choice_12.choice_text)])

    def test_form_with_data(self):
        """
        Test that a form has the correct options when it is passed data (post)
        """
        form = PollForm({'choice': self.choice_11.id}, instance=self.poll_1)
        self.assertTrue(isinstance(form.instance, Poll))
        self.assertEqual(form.instance.pk, self.poll_1.pk)
        self.assertEqual([c for c in form.fields['choice'].choices],
            [(self.choice_11.id, self.choice_11.choice_text),
                (self.choice_12.id, self.choice_12.choice_text)])

    def test_invalid_poll(self):
        """
        Test that PollForm raises exceptions with invalid polls
        """
        self.assertRaises(KeyError, PollForm)
        self.assertRaises(KeyError, PollForm, {})

    def test_save(self):
        """
        Test that saving with max_answer=1 works
        """
        self.assertEqual(self.poll_1.choices.get(id=1).votes, 0)
        self.assertEqual(self.poll_1.choices.get(id=2).votes, 0)
        form = PollForm({'choice': self.choice_11.id}, instance=self.poll_1)
        form.save()
        self.assertEqual(self.poll_1.choices.get(id=1).votes, 1)
        self.assertEqual(self.poll_1.choices.get(id=2).votes, 0)

    def test_form_with_multiple_answers_without_data(self):
        """
        Test that a PollForm is valid with a poll that has
        max_answer=2
        and that the form has the choices of that poll
        """
        form = PollForm(instance=self.multi_answer_poll)
        self.assertTrue(isinstance(form.instance, Poll))
        self.assertEqual(form.instance.pk, self.multi_answer_poll.pk)
        self.assertEqual([c for c in form.fields['choice'].choices],
            [(self.choice_31.id, self.choice_31.choice_text),
                (self.choice_32.id, self.choice_32.choice_text),
                (self.choice_33.id, self.choice_33.choice_text)])

    def test_form_with_multiple_answers_with_data(self):
        """
        Test that saving a form with 2 answers works
        with a poll that has max_answers=2
        """
        form = PollForm({'choice': [self.choice_31.id, self.choice_32.id]},
            instance=self.multi_answer_poll)
        self.assertTrue(isinstance(form.instance, Poll))
        self.assertEqual(form.instance.pk, self.multi_answer_poll.pk)
        self.assertEqual([c for c in form.fields['choice'].choices],
            [(self.choice_31.id, self.choice_31.choice_text),
                (self.choice_32.id, self.choice_32.choice_text),
                (self.choice_33.id, self.choice_33.choice_text)])

    def test_form_valid_with_invalid_data(self):
        """
        Test that a form with data for 3 choices
        will not be valid if max_answers=2
        """
        form = PollForm({'choice': [1, 2, 3]}, instance=self.multi_answer_poll)
        self.assertFalse(form.is_valid())

    def test_save_with_multiple_answers(self):
        """
        Test saving two answers is valid when max_answers=2
        """
        self.assertEqual(self.choice_31.votes, 0)
        self.assertEqual(self.choice_32.votes, 0)
        self.assertEqual(self.choice_33.votes, 0)
        form = PollForm(
            {'choice': [self.choice_31.id, self.choice_32.id]},
            instance=self.multi_answer_poll)
        form.save()
        choice1 = Choice.objects.get(id=self.choice_31.id)
        choice2 = Choice.objects.get(id=self.choice_32.id)
        choice3 = Choice.objects.get(id=self.choice_33.id)
        self.assertEqual(choice1.votes, 1)
        self.assertEqual(choice2.votes, 1)
        self.assertEqual(choice3.votes, 0)

    def test_save_with_one_answer_for_multi_answer_poll(self):
        """
        Test that you can still save with data for 1 choice when max_answers=2
        """
        self.assertEqual(self.choice_31.votes, 0)
        self.assertEqual(self.choice_32.votes, 0)
        self.assertEqual(self.choice_33.votes, 0)
        form = PollForm(
            {'choice': [self.choice_31.id]}, instance=self.multi_answer_poll)
        form.save()
        choice1 = Choice.objects.get(id=self.choice_31.id)
        choice2 = Choice.objects.get(id=self.choice_32.id)
        choice3 = Choice.objects.get(id=self.choice_33.id)
        self.assertEqual(choice1.votes, 1)
        self.assertEqual(choice2.votes, 0)
        self.assertEqual(choice3.votes, 0)

    def test_is_valid_with_too_many_answers(self):
        """
        Test that a form with data for 3 choices when max_answers =2
        is not valid
        """
        self.assertEqual(self.choice_31.votes, 0)
        self.assertEqual(self.choice_32.votes, 0)
        self.assertEqual(self.choice_33.votes, 0)
        form = PollForm(
            {'choice':
                [self.choice_31.id, self.choice_32.id, self.choice_33.id]},
            instance=self.multi_answer_poll)
        self.assertRaises(form.is_valid())
        choice1 = Choice.objects.get(id=self.choice_31.id)
        choice2 = Choice.objects.get(id=self.choice_32.id)
        choice3 = Choice.objects.get(id=self.choice_33.id)
        self.assertEqual(choice1.votes, 0)
        self.assertEqual(choice2.votes, 0)
        self.assertEqual(choice3.votes, 0)

    def test_save_too_many_answers(self):
        """
        Try to save a form with data for 3 choices when max_answers =2
        """
        self.assertEqual(self.choice_31.votes, 0)
        self.assertEqual(self.choice_32.votes, 0)
        self.assertEqual(self.choice_33.votes, 0)
        form = PollForm(
            {'choice':
                [self.choice_31.id, self.choice_32.id, self.choice_33.id]},
            instance=self.multi_answer_poll)
        with self.assertRaises(forms.ValidationError):
            form.save()
        choice1 = Choice.objects.get(id=self.choice_31.id)
        choice2 = Choice.objects.get(id=self.choice_32.id)
        choice3 = Choice.objects.get(id=self.choice_33.id)
        self.assertEqual(choice1.votes, 0)
        self.assertEqual(choice2.votes, 0)
        self.assertEqual(choice3.votes, 0)

'''
class BrowserPollFormTests(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)

        #create a poll so that we can go to DetailView
        self.multi_answer_poll = Poll.objects.create(
            question="Can you submit more than one answer",
            pub_date=timezone.now(),
            max_answers=2)
        self.choice1 = Choice.objects.create(
            choice_text="One", poll=self.multi_answer_poll)
        self.choice2 = Choice.objects.create(
            choice_text="Two", poll=self.multi_answer_poll)
        self.choice3 = Choice.objects.create(
            choice_text="Three", poll=self.multi_answer_poll)

    def tearDown(self):
        self.browser.quit()

    def test_submit_poll_form(self):
        """
        Test that the choices for a poll show up on the detail page
        and that clicking a checkbox and submitting the form
        increments the choice's votes
        """
        self.browser.get(self.live_server_url +
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn(self.multi_answer_poll.question, body.text)
        #get all checkboxes
        checkboxes = self.browser.find_elements_by_name('choice')
        self.assertEquals(
            len(checkboxes), self.multi_answer_poll.choices.count())
        choice_labels = self.browser.find_elements_by_tag_name('label')
        #TODO: exclude the "Choice:" label above the field
        choices_text = [c.text for c in choice_labels[1:]]
        self.assertEquals(
            choices_text,
            [c.choice_text for c in self.multi_answer_poll.choices.all()])

        #click the first option
        for checkbox in checkboxes:
            checkbox.click()
            break
        self.browser.find_element_by_css_selector(
            "input[type='submit']").click()
        choice1 = Choice.objects.get(id=self.choice1.id)
        self.assertEqual(choice1.votes, 1)

    def test_submit_with_no_choice(self):
        """
        Test clicking submit without clicking a selection displays "required"
        """
        self.browser.get(self.live_server_url +
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        self.browser.find_element_by_css_selector(
            "input[type='submit']").click()
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn("required", body.text)

    #TODO: this will fail with new javascript
    #the other test is sending the data which people can still do so it is good to keep it
    #but this won't work
    #and in fact if you watch it you see that
    def test_submit_with_too_many_choices(self):
        """
        Test clicking more choices than max_answers
        that "Too many" is displayed
        """
        self.browser.get(self.live_server_url +
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        checkboxes = self.browser.find_elements_by_name('choice')
        for checkbox in checkboxes:
            checkbox.click()
        self.browser.find_element_by_css_selector(
            "input[type='submit']").click()
        body = self.browser.find_element_by_tag_name('body')
        #self.assertIn("Too many", body.text)

    #so we know the javascript code is working
    #let's test one more thing if you can use the keyboard to submit the form
    #TODO: why does onclick work?
    #so I guess I say now let's check if our onchange is working for people
    #who use their keyboard to submit forms
    #so we need another include

    def test_keyboard_submit_form(self):
        self.browser.get(self.live_server_url +
            reverse('polls:detail', args=(self.multi_answer_poll.id,)))
        body = self.browser.find_element_by_tag_name('body')
        # Press Tab Space to select first choice then tab to submit
        #and hit enter space
        body.send_keys('\t' + Keys.SPACE + '\t\t\t' + Keys.SPACE)
        choice1 = Choice.objects.get(id=self.choice1.id)
        self.assertEqual(choice1.votes, 1)
'''