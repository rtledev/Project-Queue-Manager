# Project-Queue-Manager
A Queue Manager for appointments.

Meeting Queue Manager - Ps & Qs
- Check-box for solo/group
- Keyword matching for grouping meetings.
- Priority Queues for DSL, First-come first-serve, etc
- Teacher and TA access for managing meetings.
- Calender with available dates/time slots
- Notes with meeting
- if grouping checkbox checked, similar notes/concepts can be grouped together - by TA/Prof
- Estimated wait-time on meeting, 
- “possible notification”  - email/text if you can implement
- so if person has made a meeting and certain keywords are used again in the title, prevent and tell them you already have an incoming meeting with the same or similar topic which you can discuss there
- will start as a ONE Class Project (one teacher, few TA if even there, then student)


### Elaboration on Professor, TA, and Students will show up and be added as their approriate account.
    - When creating a Prof access account (simple username, password etc)
        - Input for username and password
    - Need a specific code for code input (so not just a student creates a
    n admin account)
    - How TA's are set, list of students are given, and Prof will checkbox to add TA's.
    - Will have a list of students, those checkboxed (max 5) will have TA access permissions
    - TA's will also be separately displayed on the side including still being in the student list.
    - Professor can add up to 5 TA's (If statement with increment)
    - students will sign up for an account (possible email notifications as well for meetings)


### Elaboration on how Student list will work
    - Create an empty list for students to be put in and displayed
    - Formatting vetically (temp)
    - Once signed-up with ID, student will be added to the list of student (increment per sign up made)
    - Restrictions are set up by ID's, Let's say number has been assigned to student specifically, that's their ID. 
        - e.g. (CWID)
    - Student will be assigned an ID and will have a placeholder already. Once signed up, they will be added to the student list for view.
    - the reason why they have a placeholder, is because prof will know who is in their classes right now.

## What do we want to start with?
## We Will first work on the Priority Queue, Calendar appointment comes after Priority Queue works.
    - Create a List for Students (shown)
    - Create a window, add buttons and fuctionalities (will elaborate)
    - (Placeholders) Create a list of ID's allowed (could be CWID if connected, realistically 1-40 number).
        - The (GUI) Window will show an options asking whether they are a student or a professor. If a professor (create an Account) with general sign up functionality (look up on how other website do it and find INSPO). Students will be prompted to provide their name (first and last), email, and GIVEN ID (temp ID for now) after pressing the 'I am a Student' button.
#### Student Priority Queue Functionality what they see
            -> Check button if you want notifications of "possibly, position changed in Waitlist, ETC"
    - After chooosing Student or Professor (finished putting in credentials) -> window will show:
            -> Student (Calendar will have Date and Time) -> Today's date, reason why and if they are okay with being grouped (need a description for grouped). 
                -> Add implement pop-up of description of that the grouped button does.
                -> When hovered over, change color to blue or something like a hyperlink to show. (Hypertext)
            -> Once submitted, prompt (ARE YA SURE BUDDY, Verify information).
            -> Prompt window of the current position of the Queue.
            -> Give option to leave Queue (prompt are ya sure).
        -> Lets say Office hours is from 3-5pm. Queue stop and resets at 5:10pm and will prompt users who are still waiting (Professor couldn't see you today, if you NEED to see them, email, make an appointment, or try NEXT TIME but be earlier!!!!)
#### Professor/admin what they see (Priority Queue)
##### Side Note: Add cancelation feature for appointments and prio queue (in case of emergency). Add easy pop saying: (Meetings are canceled, quick- options like: emergency coming up or letting them custom-message.)
 - Specificed (whitelist ID) ID will give admin privildges (to Professor)
    -> Specific ID will given
    -> After putting credentials for Professor:
        -> upcoming meetings will show. 
        -> Button (On/Off) Show student list. (Clock if they are in actively in waitlist. Check-mark (person-icon) if they have an appointment, Memedog if not)
            -> List of Students (Prof end) will show first and last name and ID under. 
    


#### Try Catch if Student/Prof ID Doesn't match up.
    - input requirements of students are : Name (first and last), email (to email notifications), and temp ID.
    - input requirements of professor (edit) are : Name (first and last), email (to email notifications), and temp ID.
        - try catch with IF Else statement to check the ID to approve or disapprove account making and add an Exception Error Catch

    - If ID is approved/applicable, append the name and email and ID to the list of Students to show for Professor (admin).


    - Create a ID Requirement for students, wrong ID will not allow to create an appointment
    
    
### For the Waitlist -> PrioQueue
    - Warning that you might not make it within Office Hours as it is a walk-in and not appointment. So no guarantee but keep your eyes peeled on the Wait-List-Queue. Assuming each walk-in appointment is roughly 40min, if there's too many ppl prompt it.
    


### Goals to acoomplish:
    - Working Priority Queue: Walk in for open-time slots (add time slot based on when they joined - join stats)
        - First-come-First-serve 
        - DSL Prio Queue
            - 2 queues DSL is it's waitlist but you can show merged list 
                - 
        - Joined Queue (merged queue)
        - Waitlist showing on Prof and Students end
            - Prof sees the whole waitlist
            - student sees their position in waitlist
DSL - Damn, Sucks, Loser
    - Working Priority Queue: Walk in for open-time slots (add time slot based on when they joined - join stats)
        - Three Lists:
        1. All students (time stamped) Queued 1 -> n    (techincally-merged-list)
        2. Non-DSL Students (time stamped)    1 -> n - ALS
        3. DSL Student (time stamped)         1 -> n - NODSLS



# Potential implementations
## PWA - Progressive Web App/Application
-  Website built with web technologies (HTML, CSS, JavaScriot) that functions like a native app, offering installability, offline functionality via service worker, push notifications, and fast performance.

### Google provies a Workbox:
- A libary to simply service worker creation and caching
- Service Worker: JavaScript file that enables features like offline capabillities, push notifications, and caching.

### PWA's are built off (Javascript, CSS, HTML)
- Javascript: offline functionality support via service workers, dynamic content updates, and API interactions.
- CSS: providing styling, layout, and responsive design that gives PWA the app-like look.
- PWAs rely on progressive enhancement, starting with a basic HTML structure, enhancing the user experience with CSS, and adding advanced, app-like functionality with JavaScript and modern browser APIs. You cannot build a fully functional PWA with only one of them; they are complementary technologies.

# Tools used:
- Python used for the queue-management, priority queue, and I/O functionality of list
- SQL used for Student names, Student info such as CWID, and comments from professors, Meeting Date & Time
- React(JavaScript) - API Implementation, Manifest File, and functionality
- React(CSS) - Styling/Layout Look
- React(HMTL) - Structure of the Website, Functionality, Connected it to React/Python? IDK yet.