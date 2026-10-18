from datetime import date, time, timedelta

import pytest

from pawpal_system import (Frequency, Owner, Pet, Preferences, Priority,
                           Scheduler, Task, TaskType)


def make_task(frequency: Frequency = Frequency.ONCE) -> Task:
    return Task("Morning walk", "Walk around the park", 30,
                Priority.HIGH, TaskType.WALK, frequency, time(8, 0))


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Goldie", 2, "Golden Retriever")
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1


def test_completing_daily_task_creates_next_day_task():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.DAILY)
    pet.add_task(task)

    nxt = task.mark_complete()

    assert task.completed is True
    assert nxt is not None and nxt is not task
    assert nxt.due_date == date.today() + timedelta(days=1)
    assert nxt.completed is False
    assert (nxt.name, nxt.start_time, nxt.frequency) == (task.name, task.start_time, task.frequency)
    assert nxt.pet is pet and nxt in pet.tasks and len(pet.tasks) == 2


def test_completing_weekly_task_creates_task_seven_days_out():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.WEEKLY)
    pet.add_task(task)

    nxt = task.mark_complete()

    assert nxt.due_date == date.today() + timedelta(days=7)


def test_completing_one_off_task_creates_nothing():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task()
    pet.add_task(task)

    assert task.mark_complete() is None
    assert len(pet.tasks) == 1


def test_completing_twice_does_not_duplicate():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.DAILY)
    pet.add_task(task)

    task.mark_complete()
    assert task.mark_complete() is None
    assert len(pet.tasks) == 2


def test_future_occurrence_not_in_todays_schedule():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.DAILY)
    pet.add_task(task)
    scheduler = Scheduler(Owner("Jo", [pet]), time_available=120)

    task.mark_complete()

    assert scheduler.schedule().tasks == []


def make_scheduler():
    goldie = Pet("Goldie", 2, "Golden Retriever")
    buddy = Pet("Buddy", 1, "German Shepherd")
    return Scheduler(Owner("Jo", [goldie, buddy]), time_available=300), goldie, buddy


def timed(name, start, minutes):
    return Task(name, "", minutes, Priority.MEDIUM, TaskType.OTHER, start_time=start)


def test_same_time_tasks_for_same_pet_warn():
    scheduler, goldie, _ = make_scheduler()
    assert scheduler.add_task(goldie, timed("Walk", time(8, 0), 30)) == []

    warnings = scheduler.add_task(goldie, timed("Bath", time(8, 0), 20))

    assert len(warnings) == 1 and "same pet" in warnings[0]
    assert len(goldie.tasks) == 2  # still added; a conflict is only a warning


def test_overlap_across_pets_warns():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8, 0), 30))
    scheduler.add_task(buddy, timed("Meds", time(8, 15), 5))

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1 and "different pets" in warnings[0]
    assert "Goldie" in warnings[0] and "Buddy" in warnings[0]


def test_back_to_back_tasks_do_not_conflict():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8, 0), 30))
    scheduler.add_task(buddy, timed("Meds", time(8, 30), 5))

    assert scheduler.find_conflicts() == []


def test_conflicts_ignore_completed_untimed_and_other_days():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8, 0), 30))
    done = timed("Done", time(8, 0), 30)
    done.completed = True
    scheduler.add_task(buddy, done)
    scheduler.add_task(buddy, Task("Untimed", "", 30, Priority.LOW, TaskType.OTHER))
    tomorrow = timed("Tomorrow", time(8, 0), 30)
    tomorrow.due_date = date.today() + timedelta(days=1)
    scheduler.add_task(buddy, tomorrow)

    assert scheduler.find_conflicts() == []


def test_long_task_conflicts_with_several_later_tasks():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Hike", time(9, 0), 120))
    scheduler.add_task(buddy, timed("A", time(9, 30), 10))
    scheduler.add_task(buddy, timed("B", time(10, 0), 10))
    scheduler.add_task(buddy, timed("C", time(10, 50), 10))

    assert len(scheduler.find_conflicts()) == 3


# ---------------------------------------------------------------- helpers

def task(name="T", start=None, minutes=30, priority=Priority.MEDIUM,
         task_type=TaskType.OTHER, **kw):
    return Task(name, "", minutes, priority, task_type, start_time=start, **kw)


def names(tasks):
    return [t.name for t in tasks]


# ---------------------------------------------------------------- sorting

def test_time_sort_returns_chronological_order():
    scheduler, goldie, _ = make_scheduler()
    for n, h, m in [("late", 14, 0), ("early", 8, 0), ("mid", 11, 30)]:
        goldie.add_task(task(n, time(h, m)))

    result = scheduler.sort_tasks(scheduler.get_tasks(), "time")

    assert names(result) == ["early", "mid", "late"]


def test_midnight_task_sorts_first_not_treated_as_unset():
    scheduler, _, _ = make_scheduler()
    tasks = [task("none"), task("noon", time(12)), task("midnight", time(0, 0))]

    assert names(scheduler.sort_tasks(tasks, "time")) == ["midnight", "noon", "none"]


def test_priority_sort_high_first():
    scheduler, _, _ = make_scheduler()
    tasks = [task("l", priority=Priority.LOW), task("h", priority=Priority.HIGH),
             task("m", priority=Priority.MEDIUM)]

    assert names(scheduler.sort_tasks(tasks, "priority")) == ["h", "m", "l"]


def test_duration_sort_shortest_first():
    scheduler, _, _ = make_scheduler()
    tasks = [task("a", minutes=45), task("b", minutes=5), task("c", minutes=20)]

    assert names(scheduler.sort_tasks(tasks, "duration")) == ["b", "c", "a"]


def test_untimed_tasks_sort_last():
    scheduler, _, _ = make_scheduler()
    tasks = [task("none", priority=Priority.HIGH), task("timed", time(9))]

    assert names(scheduler.sort_tasks(tasks, "time")) == ["timed", "none"]
    tasks = [task("none"), task("timed", time(9))]
    assert names(scheduler.sort_tasks(tasks, "priority")) == ["timed", "none"]


def test_sort_ties_keep_input_order():
    scheduler, _, _ = make_scheduler()
    tasks = [task("first", time(8)), task("second", time(8)), task("third", time(8))]

    assert names(scheduler.sort_tasks(tasks, "time")) == ["first", "second", "third"]
    assert names(scheduler.sort_tasks(tasks, "priority")) == ["first", "second", "third"]


def test_sort_empty_list_and_no_mutation():
    scheduler, _, _ = make_scheduler()
    assert scheduler.sort_tasks([], "time") == []

    original = [task("b", time(9)), task("a", time(8))]
    scheduler.sort_tasks(original, "time")
    assert names(original) == ["b", "a"]


def test_unknown_sort_key_raises():
    scheduler, _, _ = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.sort_tasks([], "color")


def test_schedule_output_is_in_clock_order_with_untimed_last():
    scheduler, goldie, _ = make_scheduler()
    goldie.add_task(task("untimed", priority=Priority.HIGH))
    goldie.add_task(task("pm", time(15), priority=Priority.HIGH))
    goldie.add_task(task("am", time(7), priority=Priority.LOW))

    assert names(scheduler.schedule().tasks) == ["am", "pm", "untimed"]


# ------------------------------------------------------------- recurrence

def test_next_occurrence_is_fresh_copy():
    original = make_task(Frequency.DAILY)
    nxt = original.next_occurrence()

    assert nxt.id != original.id and nxt.completed is False and nxt.pet is None
    assert (nxt.duration, nxt.priority, nxt.task_type) == (
        original.duration, original.priority, original.task_type)


def test_overdue_daily_task_recurs_from_today_not_due_date():
    pet = Pet("Goldie", 2, "Golden Retriever")
    old = make_task(Frequency.DAILY)
    old.due_date = date.today() - timedelta(days=3)
    pet.add_task(old)

    nxt = old.mark_complete()

    assert nxt.due_date == date.today() + timedelta(days=1)


def test_recurring_task_without_pet_returns_next_but_attaches_nowhere():
    orphan = make_task(Frequency.DAILY)

    nxt = orphan.mark_complete()

    assert orphan.completed is True
    assert nxt is not None and nxt.pet is None


def test_chain_of_completions_adds_exactly_one_task_each_time():
    pet = Pet("Goldie", 2, "Golden Retriever")
    current = make_task(Frequency.DAILY)
    pet.add_task(current)

    for expected in (2, 3, 4):
        current = current.mark_complete()
        assert len(pet.tasks) == expected
        assert current.completed is False


def test_one_off_next_occurrence_is_none():
    assert make_task().next_occurrence() is None


def test_recurring_copy_does_not_conflict_with_original():
    scheduler, goldie, _ = make_scheduler()
    t = make_task(Frequency.DAILY)
    scheduler.add_task(goldie, t)

    t.mark_complete()

    assert scheduler.find_conflicts() == []


# --------------------------------------------------------------- conflicts

def test_identical_start_and_duration_conflict_once():
    scheduler, goldie, _ = make_scheduler()
    scheduler.add_task(goldie, timed("A", time(8), 30))
    warnings = scheduler.add_task(goldie, timed("B", time(8), 30))

    assert len(warnings) == 1
    assert len(scheduler.find_conflicts()) == 1  # reported once, not twice


def test_same_time_across_pets_is_flagged():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8), 30))
    scheduler.add_task(buddy, timed("Walk", time(8), 30))

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1 and "different pets" in warnings[0]


def test_three_tasks_at_same_time_give_three_pairs():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("A", time(8), 30))
    scheduler.add_task(goldie, timed("B", time(8), 30))
    scheduler.add_task(buddy, timed("C", time(8), 30))

    assert len(scheduler.find_conflicts()) == 3


def test_short_task_inside_long_task_conflicts():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Hike", time(9), 120))
    scheduler.add_task(buddy, timed("Meds", time(10), 5))

    assert len(scheduler.find_conflicts()) == 1


def test_no_conflicts_with_no_tasks():
    scheduler, _, _ = make_scheduler()
    assert scheduler.find_conflicts() == []
    assert Scheduler(Owner("Empty"), 60).find_conflicts() == []


def test_task_wrapping_past_midnight_has_end_time_and_no_crash():
    late = timed("Late", time(23, 30), 60)

    assert late.end_time == time(0, 30)
    scheduler, goldie, _ = make_scheduler()
    scheduler.add_task(goldie, late)
    assert scheduler.find_conflicts() == []


def test_add_task_to_unowned_pet_raises():
    scheduler, _, _ = make_scheduler()
    stranger = Pet("Stray", 3, "Mutt")

    with pytest.raises(ValueError):
        scheduler.add_task(stranger, timed("Walk", time(8), 30))


# -------------------------------------------------------------- scheduling

def test_empty_owner_and_empty_pet_give_empty_schedule():
    assert Scheduler(Owner("Empty"), 60).schedule().tasks == []
    scheduler, _, _ = make_scheduler()
    result = scheduler.schedule()
    assert result.tasks == [] and result.total_duration == 0


def test_zero_time_available_schedules_nothing():
    scheduler, goldie, _ = make_scheduler()
    scheduler.time_available = 0
    goldie.add_task(task("A", time(8), 10))

    assert scheduler.schedule().tasks == []


def test_task_exactly_filling_budget_is_included():
    scheduler, goldie, _ = make_scheduler()
    scheduler.time_available = 30
    goldie.add_task(task("Exact", time(8), 30))

    assert names(scheduler.schedule().tasks) == ["Exact"]


def test_too_long_task_skipped_but_smaller_later_ones_still_fit():
    scheduler, goldie, _ = make_scheduler()
    scheduler.time_available = 30
    goldie.add_task(task("Big", time(8), 60, priority=Priority.HIGH))
    goldie.add_task(task("Small", time(9), 20, priority=Priority.LOW))

    assert names(scheduler.schedule().tasks) == ["Small"]


def test_high_priority_wins_when_only_one_fits():
    scheduler, goldie, _ = make_scheduler()
    scheduler.time_available = 30
    goldie.add_task(task("Low", time(8), 30, priority=Priority.LOW))
    goldie.add_task(task("High", time(9), 30, priority=Priority.HIGH))

    assert names(scheduler.schedule().tasks) == ["High"]


def test_schedule_excludes_completed_and_future_tasks():
    scheduler, goldie, _ = make_scheduler()
    done = task("Done", time(8))
    done.completed = True
    goldie.add_task(done)
    goldie.add_task(task("Future", time(9), due_date=date.today() + timedelta(days=1)))
    goldie.add_task(task("Today", time(10)))

    assert names(scheduler.schedule().tasks) == ["Today"]


def test_next_up_includes_task_starting_exactly_now():
    scheduler, goldie, _ = make_scheduler()
    goldie.add_task(task("Before", time(7)))
    goldie.add_task(task("Now", time(9)))
    goldie.add_task(task("After", time(10)))

    assert scheduler.next_up(now=time(9)).name == "Now"


def test_next_up_none_when_nothing_left():
    scheduler, goldie, _ = make_scheduler()
    assert scheduler.next_up(now=time(9)) is None
    goldie.add_task(task("Early", time(7)))
    assert scheduler.next_up(now=time(9)) is None
    done = task("Done", time(10))
    done.completed = True
    goldie.add_task(done)
    assert scheduler.next_up(now=time(9)) is None


def test_daily_plan_for_pet_with_no_tasks_is_header_only():
    scheduler, goldie, _ = make_scheduler()

    assert scheduler.daily_plan(goldie) == "Daily plan for Goldie (Golden Retriever):"


# --------------------------------------------------------------- filtering

def test_filter_with_no_arguments_returns_everything():
    scheduler, goldie, buddy = make_scheduler()
    goldie.add_task(task("A"))
    buddy.add_task(task("B"))

    assert names(scheduler.filter_tasks()) == ["A", "B"]


def test_filter_combines_criteria_with_and():
    scheduler, goldie, buddy = make_scheduler()
    goldie.add_task(task("Walk", task_type=TaskType.WALK, priority=Priority.HIGH))
    goldie.add_task(task("Feed", task_type=TaskType.FEED, priority=Priority.HIGH))
    buddy.add_task(task("Walk2", task_type=TaskType.WALK, priority=Priority.HIGH))

    result = scheduler.filter_tasks(pet=goldie, task_type=TaskType.WALK,
                                    priority=Priority.HIGH, completed=False)

    assert names(result) == ["Walk"]


def test_filter_matches_pet_by_id_not_name():
    scheduler, goldie, _ = make_scheduler()
    goldie.add_task(task("A"))
    lookalike = Pet("Goldie", 2, "Golden Retriever")  # same name, different id

    assert scheduler.filter_tasks(pet=lookalike) == []


# ------------------------------------------------------------ preferences

def test_no_preferences_behaves_as_before():
    scheduler, goldie, _ = make_scheduler()
    assert scheduler.owner.preferences is None
    goldie.add_task(task("A", time(6)))

    assert names(scheduler.schedule().tasks) == ["A"]


def test_max_daily_minutes_caps_schedule_below_time_available():
    scheduler, goldie, _ = make_scheduler()
    scheduler.owner.preferences = Preferences(max_daily_minutes=40)
    goldie.add_task(task("A", time(8), 30, priority=Priority.HIGH))
    goldie.add_task(task("B", time(9), 30))

    assert names(scheduler.schedule().tasks) == ["A"]


def test_available_hours_boundaries():
    scheduler, goldie, _ = make_scheduler()
    scheduler.owner.preferences = Preferences(earliest=time(8), latest=time(12))
    goldie.add_task(task("AtEarliest", time(8), 30))
    goldie.add_task(task("EndsAtLatest", time(11), 60))
    goldie.add_task(task("TooEarly", time(7, 59), 10))
    goldie.add_task(task("OneMinutePast", time(11), 61))
    goldie.add_task(task("Untimed"))

    assert names(scheduler.schedule().tasks) == ["AtEarliest", "EndsAtLatest", "Untimed"]


# --------------------------------------------------------- pet/owner basics

def test_adding_same_task_twice_does_not_duplicate():
    pet = Pet("Goldie", 2, "Golden Retriever")
    t = make_task()
    pet.add_task(t)
    pet.add_task(t)

    assert len(pet.tasks) == 1


def test_remove_missing_task_raises_and_remove_detaches():
    pet = Pet("Goldie", 2, "Golden Retriever")
    t = make_task()
    with pytest.raises(ValueError):
        pet.remove_task(t)

    pet.add_task(t)
    pet.remove_task(t)
    assert pet.tasks == [] and t.pet is None


def test_edit_pet_repoints_tasks_to_replacement():
    owner = Owner("Jo")
    original = Pet("Goldie", 2, "Golden Retriever")
    owner.add_pet(original)
    replacement = Pet("Goldie", 3, "Golden Retriever", id=original.id)
    t = make_task()
    replacement.add_task(t)

    owner.edit_pet(replacement)

    assert owner.pets == [replacement] and t.pet is replacement


def test_duplicate_pet_and_missing_pet_raise():
    owner = Owner("Jo")
    pet = Pet("Goldie", 2, "Golden Retriever")
    owner.add_pet(pet)

    with pytest.raises(ValueError):
        owner.add_pet(pet)
    with pytest.raises(ValueError):
        owner.remove_pet(Pet("Ghost", 1, "Mutt"))
