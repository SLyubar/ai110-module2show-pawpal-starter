from dataclasses import dataclass, field
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
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def end_time(self) -> Optional[time]:
        """Time the task finishes (wraps past midnight), or None if unscheduled."""
        if self.start_time is None:
            return None
        start = datetime.combine(date.today(), self.start_time)
        return (start + timedelta(minutes=self.duration)).time()

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


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

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Order tasks by priority (high first), then start time (unset last)."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority.value,
                t.start_time is None,
                t.start_time if t.start_time is not None else time.min,
            ),
        )

    def filter_tasks(
        self, pet: Optional[Pet] = None, completed: Optional[bool] = None
    ) -> List[Task]:
        """Filter the owner's tasks by pet and/or completion status."""
        tasks = self.get_tasks()
        if pet is not None:
            tasks = [t for t in tasks if t.pet is not None and t.pet.id == pet.id]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def schedule(self) -> Schedule:
        """Build a Schedule from get_tasks() that fits time_available.

        Greedy: take incomplete tasks by priority, skipping any task that
        would exceed the remaining time. The chosen tasks are then returned
        in clock order (tasks without a start time last).
        """
        remaining = self.time_available
        chosen: List[Task] = []
        for task in self.sort_tasks([t for t in self.get_tasks() if not t.completed]):
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
            (t for t in pet.tasks if not t.completed),
            key=lambda t: (t.start_time is None, t.start_time or time.min),
        )
        lines = [f"Daily plan for {pet.name} ({pet.breed}):"]
        for t in tasks:
            when = t.start_time.strftime("%H:%M") if t.start_time else "--:--"
            lines.append(
                f"{when} — {t.name} ({t.duration} min) [priority: {t.priority.name.lower()}]"
            )
        return "\n".join(lines)

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to one of the owner's pets."""
        self._require_owned(pet)
        pet.add_task(task)

    def remove_task(self, pet: Pet, task: Task) -> None:
        """Remove a task from one of the owner's pets."""
        self._require_owned(pet)
        pet.remove_task(task)

    def _require_owned(self, pet: Pet) -> None:
        """Raise ValueError if the pet doesn't belong to this scheduler's owner."""
        if not any(p.id == pet.id for p in self.owner.pets):
            raise ValueError(f"Pet '{pet.name}' does not belong to this owner")
