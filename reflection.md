# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The app user should be able to add or remove a pet, schedule tasks such as walks and medical appointments, as well as view, add, or edit tasks. These are the three core functionalities that users should be able to perform. The main objects needed for this system are the following four classes: Owner, Pet, Task, and Scheduler. The UML design reflects these core functions, classes, and the relationships between the classes.

- What classes did you include, and what responsibilities did you assign to each?

I included the four classes: Owner, Pet, Task, and Scheduler. The responsibilities are described in the following sentences. The owner has (owns) zero or more pets. Pets need zero or more tasks. The scheduler organizes tasks and uses the owner's preferences. The classes, methods, and attributes are described below.

<u>Owner Class</u><br>
Attributes: Name, Pet Name(s), Schedule, Preferences <br>
Methods: Add Pet, Edit Pet, Remove Pet, Get Number of Pets

<u>Pet Class</u><br>
Attributes: Name, Age, Breed<br>
Methods: Walk, Eat, Sleep

<u>Task Class</u><br>
Attributes: Name, Duration, Priority, Task Type<br>
Methods: Schedule, Complete, Walk, Feed, Give Meds, Groom

<u>Scheduler Class</u><br>
Attributes: Owner Preferences, Time Available, Duration, Priority, List of Tasks<br>
Methods: Schedule, Add Task, Remove Task

**b. Design changes**

- Did your design change during implementation?

Yes.

- If yes, describe at least one change and why you made it.

Claude identified missing relationships, overlapping methods, and design issues after my first UML diagram and skeleton code implementation. The rationale for the fixes made sense because missing links between tasks and pets, the scheduler and owner as well as overlapping class methods could cause errors and conflicts later. Additionally, deduplicating and separating the methods and attributes makes the code cleaner and easier to maintain. For example, Claude created additional classes beyond the code four to help manage complexity and tracking such as schedule, preferences, task type, frequency, and priority.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

The scheduler considers time, priority as well as the owner's availability and the duration of each task. The task duration must add up to the owner's time available and never exceed it. Tasks that are complete are skipped. In terms of priority, if the available time is limited then higher priority tasks win. If there is a tie between tasks, then the earlier start time is chosen followed by the shorter duration task.

- How did you decide which constraints mattered most?

I evaluated Claude's implementation suggestions and went with what made the most logical sense. Priority is a big driver for resolving scheduling conflicts.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

I described the tradeoffs above. If there is time contention, higher priority tasks take precedence. This can result in one high-priority task that takes a long time crowding out multiple medium priority tasks.

- Why is that tradeoff reasonable for this scenario?

This is the first iteration of the app. There is no user feedback, so it is reasonable to deploy an easier implementation in the first version. Furthermore, the owner decides which tasks are high priority. The app simply incorporates those tags to resolve time conflicts. Adding complexity may not match the owner's decision-making process.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used Claude at all phases of the project. I manually brainstormed the design of classes, methods, and attributes. However, I had Claude generate the UML diagram and review it to see where my brainstorming fell short. I created the skeleton of the main.py script but Claude refactored and completed it. I also leveraged Claude for test cases and implementing the classes. Lastly, Claude helped me update and draft the documentation.

- What kinds of prompts or questions were most helpful?

I found that giving Claude direct commands with bulleted descriptions for context were most effective. That decreases the likelihood of hallucinations or Claude doing more than what is needed.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

Claude created a start_time attribute under the Task class as an integer that stores minutes after the start of the day. I had Claude change this to reflect a time object which stores time the way a human would select it; as hours and minutes.

- How did you evaluate or verify what the AI suggested?

I carefully reviewed the proposed changes and any justification that Claude provided. I also reviewed the code after the changes along with the explanations to see if they make sense.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

I wrote 53 pytest tests in tests/test_pawpal.py covering the scheduler's core behaviors such as:

    - Sorting by time, priority and duration, including ties and tasks with no start time.
    - Recurring tasks: completing a daily or weekly task creates the next one, and completing a task twice does not duplicate it.
    - Conflict detection: same-time and overlapping tasks across pets, back-to-back tasks, and ignoring complete or other-day tasks.
    - Scheduling: the time budget, priority winning when only one task fits, and preferences such as a daily cap and available hours.
    - Edge cases: a pet with no tasks, zero time available, and tasks that exactly fill the budget.

- Why were these tests important?

These behaviors decide what the owner is told to do each day, so a quiet bug here (a missed conflict, a duplicate recurring task, or an off-by-one at the time limit) would give a wrong plan with no error. The edge cases matter most because that is where the logic is easiest to get wrong. The tests also let me change the code later with confidence.

**b. Confidence**

- How confident are you that your scheduler works correctly?

Based on the current design and testing results, I am about 80 percent confident that the scheduler works correctly. It is always possible to miss or not even imagine certain issues until you have live user testing. Sometimes you don't even find out about a problem until you get to production but ideally, this only includes a few cases.

- What edge cases would you test next if you had more time?

If I had more time, I would start with tasks that run past midnight, because the conflict checks only look within a single day, so a late-night task could overlap with an early-morning one without a warning. I would also test editing a task in the app. Changing a start time or duration updates the task in place and skips the conflict check that adding a task runs, so an edit could quietly create an overlap. Next, I would look at recurring tasks that are completed late, since the next due date counts from today and not from the original due date, and I'm not sure that matches what a user would expect. I would also test preferences with an overnight window, such as 22:00 to 06:00, which the current "earliest before latest" rule does not allow.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am satisfied with the look and feel of the app. It has easy to use functionality and the test cases do not reveal any glaring weaknesses.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had more time, I would attempt to build the app mostly manually without AI assistance throughout. I am curious to see how AI acts as a reviewer and the one finishing the implementation instead of creating the skeleton in guiding along the way.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I found that using Claude's plan mode first is great for evaluating what Claude wants to do instead of prompting it and reviewing every step. It is hard to keep up with all the changes that Claude makes. Therefore, I would rather see the plan first and then feel more confident during implementation that the results reflect an agreed-upon plan. I also learned that Claude is so powerful that it can finish the whole implementation end-to-end with minimal guidance and effectively anticipates next steps. However, as the lead architect, you must guide Claude with an initial design and break up steps for a more polished, focused, and relevant product.
