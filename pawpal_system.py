from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import List, Optional
from uuid import uuid4


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class TaskType(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    GROOM = "groom"
    OTHER = "other"


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Preferences:
    """Placeholder for owner preferences (e.g. preferred times, limits)."""


@dataclass
class Task:
    """A single activity for one pet."""
    name: str
    description: str
    duration: int  # minutes
    priority: Priority
    task_type: TaskType
    frequency: Frequency = Frequency.ONCE
    start_time: Optional[time] = None  # time of day, e.g. time(8, 0)
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def end_time(self) -> Optional[time]:
        """Time the task finishes (wraps past midnight), or None if unscheduled."""
        if self.start_time is None:
            return None
        start = datetime.combine(date.today(), self.start_time)
        return (start + timedelta(minutes=self.duration)).time()

    @property
    def start_minutes(self) -> Optional[int]:
        """Start as minutes since midnight, or None if unscheduled."""
        if self.start_time is None:
            return None
        return self.start_time.hour * 60 + self.start_time.minute

    def overlaps(self, other: "Task") -> bool:
        """True if both tasks are timed, incomplete, due the same day and overlap.

        Tasks that merely touch (one ends as the other starts) don't overlap.
        Like the rest of the conflict check, this stays within a single day.
        """
        if self.start_time is None or other.start_time is None:
            return False
        if self.completed or other.completed or self.due_date != other.due_date:
            return False
        return (self.start_minutes < other.start_minutes + other.duration
                and other.start_minutes < self.start_minutes + self.duration)

    def next_occurrence(self) -> Optional["Task"]:
        """Build the next occurrence of a recurring task, or None for a one-off.

        The copy keeps every field of this task but is incomplete, unattached
        to any pet, has a new id, and is due date.today() plus a timedelta of
        1 day (DAILY) or 7 days (WEEKLY). The offset is counted from today,
        not from this task's own due date. The caller attaches it to a pet;
        mark_complete() does so automatically.
        """
        step = {Frequency.DAILY: timedelta(days=1), Frequency.WEEKLY: timedelta(weeks=1)}
        if self.frequency not in step:
            return None
        return replace(
            self,
            completed=False,
            due_date=date.today() + step[self.frequency],
            pet=None,
            id=uuid4().hex,
        )

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as done.

        A daily/weekly task attached to a pet also gets its next occurrence
        added to that pet, which is returned (otherwise None). Completing a
        task that is already complete does nothing.
        """
        if self.completed:
            return None
        self.completed = True
        nxt = self.next_occurrence()
        if nxt is not None and self.pet is not None:
            self.pet.add_task(nxt)
        return nxt


@dataclass
class Pet:
    name: str
    age: int
    breed: str
    tasks: List[Task] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet (no-op if already attached)."""
        if task not in self.tasks:
            self.tasks.append(task)
        task.pet = self

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet. Raises ValueError if not found."""
        if task not in self.tasks:
            raise ValueError(f"Task '{task.name}' not found for pet '{self.name}'")
        self.tasks.remove(task)
        task.pet = None


@dataclass
class Schedule:
    """The result of scheduling: the tasks that fit, in order."""
    tasks: List[Task] = field(default_factory=list)

    @property
    def total_duration(self) -> int:
        """Return the combined duration of all scheduled tasks, in minutes."""
        return sum(t.duration for t in self.tasks)


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)
    preferences: Optional[Preferences] = None

    def add_pet(self, pet: Pet) -> None:
        """Add a pet. Raises ValueError if a pet with the same id exists."""
        if any(p.id == pet.id for p in self.pets):
            raise ValueError(f"Pet '{pet.name}' is already owned")
        self.pets.append(pet)

    def edit_pet(self, pet: Pet) -> None:
        """Replace the owned pet that has the same id with the given pet."""
        for i, existing in enumerate(self.pets):
            if existing.id == pet.id:
                self.pets[i] = pet
                for task in pet.tasks:
                    task.pet = pet  # keep tasks pointing at the replacement pet
                return
        raise ValueError(f"Pet '{pet.name}' not found")

    def remove_pet(self, pet: Pet) -> None:
        """Remove the pet with the same id. Raises ValueError if not found."""
        for i, existing in enumerate(self.pets):
            if existing.id == pet.id:
                del self.pets[i]
                return
        raise ValueError(f"Pet '{pet.name}' not found")

    def get_number_of_pets(self) -> int:
        """Return how many pets this owner has."""
        return len(self.pets)

    def get_all_tasks(self) -> List[Task]:
        """Return every pet's tasks combined into one list."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """The brain: retrieves, organizes and manages tasks across all pets.

    All reads go through owner.get_all_tasks(), never a single pet.
    """
    owner: Owner
    time_available: int  # minutes

    def get_tasks(self) -> List[Task]:
        """Retrieve all tasks via owner.get_all_tasks()."""
        return self.owner.get_all_tasks()

    def sort_tasks(self, tasks: List[Task], sort_by: str = "priority") -> List[Task]:
        """Order tasks by "priority", "time" or "duration".

        - "priority": high first, then start time (unset last), then shorter first.
        - "time": start time (unset last), then high priority first.
        - "duration": shortest first, then high priority first.
        Raises ValueError for any other sort_by.
        """
        def by_time(t: Task):
            return (t.start_time is None, t.start_time or time.min)

        keys = {
            "priority": lambda t: (-t.priority.value, *by_time(t), t.duration),
            "time": lambda t: (*by_time(t), -t.priority.value),
            "duration": lambda t: (t.duration, -t.priority.value, *by_time(t)),
        }
        if sort_by not in keys:
            raise ValueError(f"Unknown sort_by '{sort_by}'; use one of {list(keys)}")
        return sorted(tasks, key=keys[sort_by])

    def filter_tasks(
        self,
        pet: Optional[Pet] = None,
        completed: Optional[bool] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[Priority] = None,
    ) -> List[Task]:
        """Return the owner's tasks that match every given criterion.

        Works as an AND filter: each argument left as None is ignored, so
        calling with no arguments returns all tasks. `pet` is matched by id,
        not by name or object identity. Preserves the original task order;
        combine with sort_tasks() to order the result.
        """
        tasks = self.get_tasks()
        if pet is not None:
            tasks = [t for t in tasks if t.pet is not None and t.pet.id == pet.id]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        return tasks

    def next_up(self, now: Optional[time] = None) -> Optional[Task]:
        """Return the earliest incomplete task starting at or after `now`.

        Filters to incomplete tasks that have a start time at or after `now`,
        then picks the first in time order. `now` defaults to the current time
        of day. Ignores the due date, and returns None if nothing is left.
        """
        now = now or datetime.now().time()
        upcoming = [
            t for t in self.filter_tasks(completed=False)
            if t.start_time is not None and t.start_time >= now
        ]
        return self.sort_tasks(upcoming, sort_by="time")[0] if upcoming else None

    def schedule(self) -> Schedule:
        """Build a Schedule from get_tasks() that fits time_available.

        Greedy selection: consider incomplete tasks due today or earlier in
        sort_tasks() order (priority first), keep each one whose duration still
        fits in the remaining minutes, and skip any that doesn't while still
        trying the smaller ones after it. The chosen tasks are then re-sorted
        into clock order (tasks without a start time last).

        Only the total duration is checked: overlapping tasks are not removed
        (see find_conflicts()), and the result isn't guaranteed to be the
        best possible fit.
        """
        remaining = self.time_available
        chosen: List[Task] = []
        today = date.today()
        pending = [t for t in self.get_tasks() if not t.completed and t.due_date <= today]
        for task in self.sort_tasks(pending):
            if task.duration <= remaining:
                chosen.append(task)
                remaining -= task.duration
        chosen.sort(key=lambda t: (t.start_time is None, t.start_time or time.min))
        return Schedule(tasks=chosen)

    def daily_plan(self, pet: Pet) -> str:
        """Format a pet's incomplete tasks as a timed daily plan, e.g.

        Daily plan for Biscuit (Golden Retriever):
        08:00 — Morning walk (30 min) [priority: high]
        """
        self._require_owned(pet)
        tasks = sorted(
            (t for t in pet.tasks if not t.completed and t.due_date <= date.today()),
            key=lambda t: (t.start_time is None, t.start_time or time.min),
        )
        lines = [f"Daily plan for {pet.name} ({pet.breed}):"]
        for t in tasks:
            when = t.start_time.strftime("%H:%M") if t.start_time else "--:--"
            lines.append(
                f"{when} — {t.name} ({t.duration} min) [priority: {t.priority.name.lower()}]"
            )
        return "\n".join(lines)

    def find_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Return a warning message for each pair of overlapping tasks.

        Lightweight check: only incomplete tasks with a start time on the same
        due date are compared, whether they belong to the same pet or not. Tasks
        that merely touch (one ends as the next starts) don't conflict. Never
        raises; an empty list means no conflicts. Defaults to all of the owner's
        tasks.
        """
        return [self._describe_conflict(a, b) for a, b in self._conflict_pairs(tasks)]

    def _conflict_pairs(self, tasks: Optional[List[Task]] = None) -> List[tuple]:
        """Return every overlapping (earlier, later) pair using a sorted sweep.

        Keeps only incomplete tasks with a start time and sorts them by
        (due date, start minute). Each task is then compared with the tasks
        after it, stopping at the first one that doesn't overlap: since the
        list is sorted, no later task can overlap it either. That costs
        O(n log n) for the sort plus one step per conflict found, instead of
        comparing every possible pair. Each pair lists the earlier-starting
        task first.
        """
        pool = self.get_tasks() if tasks is None else tasks
        timed = sorted(
            (t for t in pool if t.start_time is not None and not t.completed),
            key=lambda t: (t.due_date, t.start_minutes),
        )
        pairs = []
        for i, a in enumerate(timed):
            for b in timed[i + 1:]:
                if not a.overlaps(b):
                    break  # sorted by start, so nothing later can overlap a
                pairs.append((a, b))
        return pairs

    @staticmethod
    def _describe_conflict(a: Task, b: Task) -> str:
        """Format one overlapping pair as a human-readable warning string.

        The message names both tasks with their pets and time ranges, and says
        whether the conflict is within one pet or between different pets, e.g.
        "Warning (same pet, 2026-10-18): Goldie's 'Vet call' (14:15-14:45)
        overlaps Goldie's 'Bath' (14:30-14:50)".
        """
        def label(t: Task) -> str:
            end = t.end_time.strftime("%H:%M")
            owner = t.pet.name if t.pet else "unassigned"
            return f"{owner}'s '{t.name}' ({t.start_time:%H:%M}-{end})"

        same = a.pet is not None and b.pet is not None and a.pet.id == b.pet.id
        kind = "same pet" if same else "different pets"
        return f"Warning ({kind}, {a.due_date}): {label(a)} overlaps {label(b)}"

    def add_task(self, pet: Pet, task: Task) -> List[str]:
        """Add a task to one of the owner's pets.

        Returns warnings for any existing tasks it overlaps (empty if none).
        The task is added regardless; a conflict is a warning, not an error.
        """
        self._require_owned(pet)
        pet.add_task(task)
        return [
            self._describe_conflict(*sorted((task, other), key=lambda t: t.start_minutes))
            for other in self.get_tasks()
            if other is not task and task.overlaps(other)
        ]

    def remove_task(self, pet: Pet, task: Task) -> None:
        """Remove a task from one of the owner's pets."""
        self._require_owned(pet)
        pet.remove_task(task)

    def _require_owned(self, pet: Pet) -> None:
        """Raise ValueError if the pet doesn't belong to this scheduler's owner."""
        if not any(p.id == pet.id for p in self.owner.pets):
            raise ValueError(f"Pet '{pet.name}' does not belong to this owner")
