# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Brief Implementation Summary

I built a pet scheduling application that allows pet owners to track their daily schedule of tasks for each pet. Owners can add or remove pets, plan their daily tasks such as grooming or walking, and account for any constraints or scheduling conflicts. There are four main classes for Owner, Pet, Task, and Scheduler. The owner owns pets and has preferences, pets need tasks, and the scheduler considers the owner's preferences and schedule. Beyond these four main classes, there are helper classes such as priority, tasktype, frequency, preferences and schedule.

## 🖥️ Sample Output

The CLI output is below with a daily schedule for each pet. It also includes the full daily schedule for all pets under one owner.

```
Daily plan for Goldie (Golden Retriever):
08:00 — Morning walk (30 min) [priority: high]
09:00 — Breakfast (10 min) [priority: high]
17:30 — Brushing (20 min) [priority: low]

Daily plan for Buddy (German Shepherd):
08:30 — Morning meds (5 min) [priority: high]
14:00 — Afternoon walk (45 min) [priority: medium]
18:00 — Dinner (10 min) [priority: high]

Today's schedule (all pets):
08:00 - Goldie: Morning walk (30 min) [priority: high]
08:30 - Buddy: Morning meds (5 min) [priority: high]
09:00 - Goldie: Breakfast (10 min) [priority: high]
14:00 - Buddy: Afternoon walk (45 min) [priority: medium]
17:30 - Goldie: Brushing (20 min) [priority: low]
18:00 - Buddy: Dinner (10 min) [priority: high]
```

## 🧪 Testing PawPal+

The command below runs the full test suite of 53 tests. They comprehensively cover happy path test cases and edge cases. The tests evaluate functionality related to tasks, pets, sorting, recurrence, conflicts, filtering, preferences, and scheduling.

```bash
# Run the full test suite:
python -m pytest
```

```
Sample test output:
======================== test session starts ====================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.15.1, platformdirs-4.13.0
collected 53 items                                                                              

tests\test_pawpal.py..............................         [100%]

==================== 53 passed in 0.74s =========================
```

Confidence Level: ⭐⭐⭐⭐⬛

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks(tasks, sort_by)` | `"priority"` (default), `"time"` or `"duration"`; tasks without a start time sort last. `next_up()` returns the next task by time. |
| Filtering | `Scheduler.filter_tasks(...)` | Any mix of pet (by id), completion status, task type and priority; unset criteria are ignored. `schedule()` greedily keeps the highest-priority tasks that fit `time_available` and skips the rest. |
| Conflict handling | `Scheduler.find_conflicts()`, `Task.overlaps()`, `Scheduler.add_task()` | Warns on overlapping time ranges for the same or different pets, using a sorted sweep. Back-to-back tasks don't conflict. Returns warning strings and never raises; `add_task` returns warnings for the new task. |
| Recurring tasks | `Task.next_occurrence()`, `Task.mark_complete()` | Completing a daily or weekly task adds a copy to the same pet, due today + 1 day or + 7 days (`timedelta`). Future copies stay out of today's plan. |

## 📸 Demo Walkthrough

### Main UI features

Run `streamlit run app.py`. The page is organized top to bottom:

| Section | What you can do |
|---------|-----------------|
| **Owner / Preferences** | Set your name, a daily minutes cap and your available hours. |
| **Add a Pet** | Add, edit or remove pets (name, age, breed). |
| **Schedule a Task** | Add tasks (pet, title, duration, priority, type, frequency, start time), then edit, complete or remove them. Filter the list by pet, status, type or priority, and sort by priority, time or duration. |
| **Build Schedule** | Enter the minutes you have and generate today's plan, with metrics, skipped tasks and a per-pet daily plan. |

### Example workflow

1. **Add a pet:** enter Mochi, 3, Shiba Inu, then click **Add pet**.
2. **Schedule tasks:** add "Morning walk" (20 min, 08:00), then "Bath" (30 min, 08:10).
3. **Read the warning:** the second task is still added, but a yellow warning says the two overlap, and the **Current tasks** banner counts the conflict.
4. **Sort and filter:** sort by time or priority, or filter to one pet. **Next up** shows the next pending task.
5. **Complete a daily task:** click **Mark complete**. A new copy appears due tomorrow.
6. **View today's schedule:** click **Generate schedule**. Tasks are picked by priority until the time runs out, shown in clock order, and anything left out is listed under **Not scheduled** with a reason.

### Scheduler behaviors shown

- **Sorting:** by priority, start time or duration. Tasks with no start time go last.
- **Filtering:** any mix of pet, status, type and priority.
- **Conflict warnings:** overlapping tasks are flagged for the same or different pets. Back-to-back tasks are not.
- **Recurring tasks:** completing a daily or weekly task creates the next one.
- **Time budget and preferences:** the plan fits your minutes and available hours.

### Sample CLI output

`python main.py` runs the same logic without the UI (output trimmed):

```text
Sorted by time:
  08:00 Goldie Morning walk     30 min high   walk  todo
  08:30 Buddy  Morning meds      5 min high   meds  done
  08:30 Buddy  Morning meds      5 min high   meds  todo
  09:00 Goldie Breakfast        10 min high   feed  todo
  14:00 Buddy  Afternoon walk   45 min medium walk  todo
  17:30 Goldie Brushing         20 min low    groom todo
  18:00 Buddy  Dinner           10 min high   feed  todo

Filter: high priority, not completed, sorted by time
  08:00 Goldie Morning walk     30 min high   walk  todo
  08:30 Buddy  Morning meds      5 min high   meds  todo
  09:00 Goldie Breakfast        10 min high   feed  todo
  18:00 Buddy  Dinner           10 min high   feed  todo

Next up after 10:00: 14:00 Buddy: Afternoon walk

Today's schedule (all pets):
08:00 - Goldie: Morning walk (30 min) [priority: high]
09:00 - Goldie: Breakfast (10 min) [priority: high]
14:00 - Buddy: Afternoon walk (45 min) [priority: medium]
17:30 - Goldie: Brushing (20 min) [priority: low]
18:00 - Buddy: Dinner (10 min) [priority: high]

Recurring tasks:
  completed Goldie: Morning walk (daily) -> next due 2026-10-19 (1 day(s) from today)
  completed Goldie: Brushing (weekly) -> next due 2026-10-25 (7 day(s) from today)

Conflict detection:
  existing tasks: no conflicts
  Warning (different pets, 2026-10-18): Buddy's 'Afternoon walk' (14:00-14:45) overlaps Goldie's 'Vet call' (14:15-14:45)
  Warning (same pet, 2026-10-18): Goldie's 'Vet call' (14:15-14:45) overlaps Goldie's 'Bath' (14:30-14:50)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
