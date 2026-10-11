# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The app user should be able to add or remove a pet, schedule tasks such as walks and medical appointments, as well as view, add, or edit tasks. These are the three core functionalities that users should be able to perform. The main objects needed for this system are the following four classes: Owner, Pet, Task, and Scheduler. The UML design reflects these core functions, classes, and the relationships between the classes.

- What classes did you include, and what responsibilities did you assign to each?

I included the four classes: Owner, Pet, Task, and Scheduler. The responsibilities are described in the follow sentences. The owner has (owns) zero or more pets. Pets need zero or more tasks. The scheduler organizes tasks and uses the owner's preferences. The classes, methods, and attributes are described below.

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

Claude identified missing relationships, overlapping methods, and design issues after my first UML diagram and skeleton code implementation. The rationale for the fixes made sense because missing links between tasks and pets, the scheduler and owner as well as overlapping class methods could cause errors and conflicts later on. Additionally, deduplicating and separating the methods and attributes makes the code cleaner and easier to maintain. For example, Claude created additional classes beyond the code four to help manage complexity and tracking such as schedule, preferences, task type, frequency, and priority.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used Claude at all phases of the project. I manually brainstormed the design of classes, methods, and attributes. However, I had Claude generate the UML diagram and review it to see where my brainstorming fell short. I created the skeleton of the main.py script but I had Claude refactor and complete it. I also leveraged Claude for test cases and implementing the classes.

- What kinds of prompts or questions were most helpful?

I found that giving Claude direct commands with bulleted descriptions for context were most effective. That decreases the likelihood of hallucinations or Claude doing more than what is needed.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

Claude created a start_time attribute under the Task class as an integer that stores minutes after the start of the day. I had Claude change this to reflect a time object which stores time the way a human would select it; as hours and minutes.

- How did you evaluate or verify what the AI suggested?

I carefully reviewed the proposed changed and any justification that Claude provided. I also reviewed the code after the changes along with the explanations to see if they make sense.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
